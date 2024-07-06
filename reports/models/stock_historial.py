from itertools import groupby

from odoo import models, fields, api
from datetime import datetime
import time

import base64
import io
from odoo.tools.misc import xlsxwriter

import logging

_logger = logging.getLogger(__name__)


class StockReportHistory(models.Model):
    _name = 'stock.report.history'
    _description = 'Stock Report History'
    
    @api.onchange('date_from','date_to','company_id')
    def _onchange_date_from(self):
        self.name = "No vendido del " +str(self.date_from) + " al " + str(self.date_to)
    
   

    name = fields.Char(string="Nombre de reporte", required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    date_from = fields.Datetime(string="Fecha inicio", required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    date_to = fields.Datetime(string="Fecha final", required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True, readonly=True, states={'borrador': [('readonly', False)]},)

    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ], default='borrador')
    

    report_lines_from = fields.One2many(
        'stock.report.line', 'report_id_from', string="Report Lines From", readonly=True)
    report_lines_to = fields.One2many(
        'stock.report.line', 'report_id_to', string="Report Lines To", readonly=True)
    report_differences = fields.One2many(
        'stock.report.difference', 'report_id', string="Report Differences", readonly=True)
    
    product_list = []

    def generate_reports(self):
        self._generate_report_lines(self.date_from, 'report_lines_from')
        time.sleep(4)
        self._generate_report_lines(self.date_to, 'report_lines_to')
        time.sleep(4)
        self._calculate_differences()
        
        self.write({'state': 'aprobado'})


    def _generate_report_lines(self, date, field_name):

        StockQuant = self.env['stock.valuation.layer']

        quants = StockQuant.search(['&',
                                    ('create_date', '<=', date),
                                    ('company_id', '=', self.company_id.id)])

        # Diccionario para acumular las cantidades por producto
        product_quantities = {}
        products_idsg = []
        # Recorre todos los movimientos y acumula las cantidades en el diccionario
        for quant in quants:
            if quant.product_id.active:
                if quant.product_id.detailed_type not in ['consu','service']:
                    if quant.product_id.list_price > 0:
                        product_id = quant.product_id.id
                        quantity = quant.quantity

                        if product_id in product_quantities:
                            product_quantities[product_id] += quantity
                        else:
                            product_quantities[product_id] = quantity
                            self.product_list.append(quant.product_id)

        # Transforma el diccionario en la lista self.products_idsg
        products_idsg = [[product_id, quantity] for product_id, quantity in product_quantities.items()]

        #_logger.warning("tamaño de products idsg: " + str(len(products_idsg)))

        if len(products_idsg) >= 1:
            

            lines = []
            for line_product in products_idsg:
                lines.append((0, 0, {
                    'product_id': line_product[0],
                    'quantity': line_product[1],
                }))

            self.write({field_name: lines})

    def _calculate_differences(self):
        self.ensure_one()
        lines_from = {line.product_id.id: line for line in self.report_lines_from}
        #time.sleep(4)
        lines_to = {line.product_id.id: line for line in self.report_lines_to}
        differences = []
        ids = []
        for product_id in set(lines_from.keys()).union(lines_to.keys()):
            if product_id in lines_from:
                qty_from = lines_from[product_id].quantity  # Access quantity directly
            else:
                qty_from = 0
            if product_id in lines_to:
                qty_to = lines_to[product_id].quantity  # Access quantity directly
            else:
                qty_to = 0
            
            if qty_from > 0:
                if qty_to > 0:
                    if (qty_from - qty_to) == 0:
                        for product in self.product_list:
                            if product_id == product.id:
                                if product_id not in ids:
                                    differences.append((0, 0, {
                                        'product_id': product_id,
                                        'quantity_from': qty_from,
                                        'quantity_to': qty_to,
                                        'quantity_difference': qty_to - qty_from,
                                        'barcode': product.barcode,
                                        'lst_price': product.lst_price * qty_to,
                                        'standard_price': product.standard_price * qty_to,
                                        'linea': product.x_ingresotk,
                                        'marca': product.marca_id.name,
                                    }))
                                    ids.append(product_id)
        self.report_differences = differences
    
    

    def exportar_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Crear hojas de Excel
        worksheet_sin_movimiento = workbook.add_worksheet('Productos sin movimientos')
        worksheet_product_from = workbook.add_worksheet(f'Reporte a la fecha {self.date_from}')
        worksheet_product_to = workbook.add_worksheet(f'Reporte a la fecha {self.date_to}')
        
        
        # Definir formatos
        currency_format = workbook.add_format({'num_format': 'L#,##0.00', 'align': 'center'})
        number_format = workbook.add_format({'num_format': '#,##0', 'align': 'center'})
        header_format = workbook.add_format({'bold': True, 'align': 'center'})
        
        # Función para escribir encabezados y datos en una hoja y ajustar el tamaño de las columnas
        def escribir_hoja(worksheet, encabezados, datos, col_widths, formatos):
            # Ajustar el tamaño de las columnas
            for col, width in enumerate(col_widths):
                worksheet.set_column(col, col, width)
            
            # Escribir los encabezados
            for col, encabezado in enumerate(encabezados):
                worksheet.write(0, col, encabezado, header_format)
            
            # Escribir los datos
            row = 1
            for record in datos:
                for col, value in enumerate(record):
                    worksheet.write(row, col, value, formatos[col])
                row += 1

        # Encabezados y anchos de columnas
        encabezados_lines_reports = ['Producto', 'Cantidad al dia']
        col_widths_lines_reports = [45, 20]  # Ajusta estos valores según sea necesario
        formatos_lines_reports = [None, number_format]  # Formatos para cada columna
        
        encabezados_reports_differences = ['Codigo de barras','Producto', 'Cantidad inicial', 'Cantidad final', 'Movimiento', 'Precio de coste', 'Precio de venta', 'Linea', 'Marca']
        col_widths_reports_differences = [30, 45, 25, 25, 25, 25, 25, 35, 35]  # Ajusta estos valores según sea necesario
        formatos_reports_differences = [None, None, number_format, number_format, number_format, None, None, None, None]  # Formatos para cada columna
        
        # Preparar los datos
        datos_lines_from_report = [
            (
                record.product_id.name,
                record.quantity,
            )
            for record in self.report_lines_from
        ]
        
        datos_lines_to_report = [
            (
                record.product_id.name,
                record.quantity,
            )
            for record in self.report_lines_to
        ]

        datos_differences = [
            (
                record.barcode,
                record.product_id.name,
                record.quantity_from,
                record.quantity_to,
                record.quantity_difference,
                record.standard_price,
                record.lst_price,
                record.linea,
                record.marca,
                
            )
            for record in self.report_differences
        ]
        
        # Escribir datos en las hojas correspondientes y ajustar el tamaño de las columnas
        escribir_hoja(worksheet_sin_movimiento, encabezados_reports_differences, datos_differences, col_widths_reports_differences, formatos_reports_differences)
        escribir_hoja(worksheet_product_from, encabezados_lines_reports, datos_lines_from_report, col_widths_lines_reports, formatos_lines_reports)
        escribir_hoja(worksheet_product_to, encabezados_lines_reports, datos_lines_to_report, col_widths_lines_reports, formatos_lines_reports)
        
        workbook.close()
        output.seek(0)

        # Crear el adjunto
        attachment = self.env['ir.attachment'].create({
            'name': f'reporte_movimiento_inventario_{self.date_from}_{self.date_to}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'store_fname': f'reporte_movimiento_inventario_{self.date_from}_{self.date_to}.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Devolver la acción para descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def generate_excel(self):
        vals = []
        for line in self.report_differences:
            
            vals.append({
                'Producto': line.product_id,
                'Cantidad Inicial': line.quantity_from,
                'Cantidad Actual': line.quantity_to,
                'Cantidad movida': line.quantity_difference,
                'Compañia': self.company_id,
                'Fecha hace 6 meses': self.date_from,
                'Fecha actual': self.date_to,
            })
        return {
            'data': vals,
            'name': self.name
            }




class StockReportLine(models.Model):
    _name = 'stock.report.line'
    _description = 'Stock Report Line'

    report_id_from = fields.Many2one(
        'stock.report.history', string="Reporte Inicial", ondelete='cascade')
    report_id_to = fields.Many2one(
        'stock.report.history', string="Reporte Final", ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', string="Producto", required=True)
    quantity = fields.Float(string="Cantidad al dia", required=True)
    
    
    #location_id = fields.Many2one('stock.location', string="Location", required=True)
    #date_create = fields.Datetime(string="Create Date", required=True)


class StockReportDifference(models.Model):
    _name = 'stock.report.difference'
    _description = 'Stock Report Difference'

    report_id = fields.Many2one(
        'stock.report.history', string="Reporte", ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', string="Producto", required=True)
    quantity_from = fields.Float(string="Cantidad Inicial", required=True)
    quantity_to = fields.Float(string="Cantidad Final", required=True)
    quantity_difference = fields.Float(
        string="Movimiento", required=True)
    lst_price = fields.Float(string="Precio de venta", required=True)
    standard_price = fields.Float(string="Precio de coste", required=True)

    barcode = fields.Char(string="Barcode")
    linea = fields.Char(string="Linea")
    marca = fields.Char(string="Marca")