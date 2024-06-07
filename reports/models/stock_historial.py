from itertools import groupby

from odoo import models, fields, api
from datetime import datetime

import base64
import io
from odoo.tools.misc import xlsxwriter

import logging

_logger = logging.getLogger(__name__)


class StockReportHistory(models.Model):
    _name = 'stock.report.history'
    _description = 'Stock Report History'
    
    """def _name_(self):
        self.name = "Reporte de movimiento de inventario :: " + str(self.company_id.name)"""

    @api.onchange('date_from','date_to','company_id')
    def _onchange_date_from(self):
        self.name = "Reporte de " + str(self.company_id.name) + " // " +str(self.date_from) + "::" + str(self.date_to)
    
   

    name = fields.Char(string="Nombre de reporte", required=True)
    date_from = fields.Datetime(string="Fecha inicio", required=True)
    date_to = fields.Datetime(string="Fecha final", required=True)
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id)

    

    report_lines_from = fields.One2many(
        'stock.report.line', 'report_id_from', string="Report Lines From", readonly=True)
    report_lines_to = fields.One2many(
        'stock.report.line', 'report_id_to', string="Report Lines To", readonly=True)
    report_differences = fields.One2many(
        'stock.report.difference', 'report_id', string="Report Differences", readonly=True)

    def generate_reports(self):
        self._generate_report_lines(self.date_from, 'report_lines_from')
        self._generate_report_lines(self.date_to, 'report_lines_to')
        self._calculate_differences()


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
            product_id = quant.product_id.id
            quantity = quant.quantity

            if product_id in product_quantities:
                product_quantities[product_id] += quantity
            else:
                product_quantities[product_id] = quantity

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
        lines_to = {line.product_id.id: line for line in self.report_lines_to}
        differences = []
        for product_id in set(lines_from.keys()).union(lines_to.keys()):
            if product_id in lines_from:
                qty_from = lines_from[product_id].quantity  # Access quantity directly
            else:
                qty_from = 0
            if product_id in lines_to:
                qty_to = lines_to[product_id].quantity  # Access quantity directly
            else:
                qty_to = 0
            
            if qty_from != 0:
                if qty_to != 0:
                    if (qty_from - qty_to) == 0:
                        _logger.warning("Entra")
                        differences.append((0, 0, {
                            'product_id': product_id,
                            'quantity_from': qty_from,
                            'quantity_to': qty_to,
                            'quantity_difference': qty_to - qty_from,
                        }))
        self.report_differences = differences
    
    def exportar_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Escribir los encabezados
        worksheet.write(0, 0, 'Producto')
        worksheet.write(0, 1, 'Inventario Inicial')
        worksheet.write(0, 2, 'Inventario Final')
        worksheet.write(0, 3, 'Movimiento de producto')

        # Escribir los datos
        row = 1
        for record in self.report_differences:
            worksheet.write(row, 0, record.product_id.product_tmpl_id.name)
            worksheet.write(row, 1, record.quantity_from)
            worksheet.write(row, 2, record.quantity_to)
            worksheet.write(row, 3, record.quantity_difference)
            row += 1

        workbook.close()
        output.seek(0)

        # Crear el adjunto
        attachment = self.env['ir.attachment'].create({
            'name': 'stock_report_history_export.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'store_fname': 'stock_report_history_export.xlsx',
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

