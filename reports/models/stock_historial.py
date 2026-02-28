from itertools import groupby

from odoo import models, fields, api
from datetime import datetime, date
import time
from collections import defaultdict
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
    product_list_1 = []

    def generate_reports(self):
        # Genera los reportes de inventario para ambas fechas y calcula diferencias
        products_from = self._generate_report_lines(self.date_from, 'report_lines_from')
        products_to = self._generate_report_lines(self.date_to, 'report_lines_to')
        self._calculate_differences(products_from, products_to)
        self.write({'state': 'aprobado'})

    def _generate_report_lines(self, date_report, field_name):
        productos = self.env['product.product'].search([('company_id', '=', self.company_id.id), ('active', '=', True)])
        inventario = []
        product_location_set = set()
        company_locations = {
            8: [155, 161],
            9: [181, 169, 175],
        }
        valid_locations = company_locations.get(self.company_id.id, [])

        # Determina si es inventario actual o histórico
        if date.today() == date_report.date():
            for producto in productos:
                if producto.detailed_type not in ['consu', 'service'] and producto.list_price > 0:
                    for quant in producto.stock_quant_ids:
                        if quant.location_id.id in valid_locations:
                            inventario.append({
                                "producto": producto.id,
                                "Ubicacion": quant.location_id.id,
                                "cantidad": quant.quantity
                            })
                            product_location_set.add((producto.id, quant.location_id.id))
        else:
            product_location_quantities = defaultdict(lambda: defaultdict(float))
            move_lines = self.env['stock.move.line'].search([
                ('date', '<=', date_report),
                ('company_id', '=', self.company_id.id),
            ])
            for ml in move_lines:
                product = ml.product_id
                if not product.active or product.detailed_type in ['consu', 'service'] or product.list_price <= 0:
                    continue
                # Origen
                if ml.location_id.id in valid_locations and ml.location_id.usage == 'internal':
                    product_location_quantities[product.id][ml.location_id.id] -= ml.qty_done
                    product_location_set.add((product.id, ml.location_id.id))
                # Destino
                if ml.location_dest_id.id in valid_locations and ml.location_dest_id.usage == 'internal':
                    product_location_quantities[product.id][ml.location_dest_id.id] += ml.qty_done
                    product_location_set.add((product.id, ml.location_dest_id.id))
            for product_id, locations in product_location_quantities.items():
                for location_id, qty in locations.items():
                    if qty >= 0 and location_id in valid_locations:
                        inventario.append({
                            "producto": product_id,
                            "Ubicacion": location_id,
                            "cantidad": qty
                        })

        # Escribir líneas del reporte
        lines = []
        for item in inventario:
            lines.append((0, 0, {
                'product_id': item["producto"],
                'location_id': item["Ubicacion"],
                'quantity': item["cantidad"],
            }))
        self.write({field_name: lines})

        # Devuelve el set de (producto, ubicación) para usar en diferencias
        return product_location_set

    def _calculate_differences(self, products_from, products_to):
        self.ensure_one()
        # Combina todos los productos/ubicaciones de ambas fechas
        all_product_locations = products_from.union(products_to)
        # Indexa líneas por producto y ubicación
        lines_from = {(line.product_id.id, line.location_id.id): line for line in self.report_lines_from}
        lines_to = {(line.product_id.id, line.location_id.id): line for line in self.report_lines_to}
        differences = []

        for product_id, location_id in all_product_locations:
            qty_from = lines_from.get((product_id, location_id), False)
            qty_to = lines_to.get((product_id, location_id), False)
            cantidad_inicial = qty_from.quantity if qty_from else 0
            cantidad_final = qty_to.quantity if qty_to else 0
            diferencia = cantidad_final - cantidad_inicial

            # Solo muestra productos donde no hubo movimiento o no tienen movieminto entre las fechas
            if cantidad_inicial == cantidad_final and cantidad_inicial > 0 and cantidad_final > 0:
                product = self.env['product.product'].browse(product_id)
                movimiento = self.env['stock.move.line'].search_count([
                    ('product_id', '=', product_id),
                    ('date', '>=', self.date_from),
                    ('date', '<=', self.date_to),
                    ('company_id', '=', self.company_id.id),
                    ('location_id', 'in', [loc.id for loc in product.stock_quant_ids.mapped('location_id')]),
                    ('location_dest_id', 'in', [loc.id for loc in product.stock_quant_ids.mapped('location_id')]),
                ])
                
                if movimiento == 0:
                    differences.append((0, 0, {
                        'product_id': product_id,
                        'location_id': location_id,
                        'quantity_from': cantidad_inicial,
                        'quantity_to': cantidad_final,
                        'quantity_difference': diferencia,
                        'barcode': product.barcode or '',
                        'lst_price': product.lst_price * cantidad_final,
                        'standard_price': product.standard_price * cantidad_final,
                        'linea': product.x_ingresotk,
                        'marca': product.marca_id.name if product.marca_id else '',
                    }))
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
        encabezados_lines_reports = ['Producto', 'Almacen', 'Cantidad al dia']
        col_widths_lines_reports = [45,30, 20]  # Ajusta estos valores según sea necesario
        formatos_lines_reports = [None, None, number_format]  # Formatos para cada columna
        
        encabezados_reports_differences = ['Codigo de barras', 'Producto', 'Cantidad inicial', 'Cantidad final', 'Movimiento', 'Precio de coste', 'Precio de venta', 'Linea', 'Marca']
        col_widths_reports_differences = [30,45, 25, 25, 25, 25, 25, 25, 25]  # Ajusta estos valores según sea necesario
        formatos_reports_differences = [None,None, number_format, number_format, number_format, currency_format, currency_format, None, None]  # Formatos para cada columna
        
        # Preparar los datos 
        datos_lines_from_report = [
            (
                record.product_id.name,
                record.location_id.name,
                record.quantity,
            )
            for record in self.report_lines_from
        ]
        
        datos_lines_to_report = [
            (
                record.product_id.name,
                record.location_id.name,
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
                record.marca
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
    location_id = fields.Many2one('stock.location', string="Ubicación")
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
    location_id = fields.Many2one('stock.location', string="Ubicación")
    
    barcode = fields.Char(string="Barcode")
    linea = fields.Char(string="Linea")
    marca = fields.Char(string="Marca")

