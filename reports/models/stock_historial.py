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
    
    name = fields.Char(string="Nombre de reporte", required=True, readonly=True, states={'borrador': [('readonly', False)]})
    date_from = fields.Datetime(string="Fecha inicio", required=True, readonly=True, states={'borrador': [('readonly', False)]})
    date_to = fields.Datetime(string="Fecha final", required=True, readonly=True, states={'borrador': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company.id, required=True, readonly=True, states={'borrador': [('readonly', False)]})
    state = fields.Selection([('borrador', 'Borrador'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado')], default='borrador')
    
    report_lines_from = fields.One2many('stock.report.line', 'report_id_from', string="Report Lines From", readonly=True)
    report_lines_to = fields.One2many('stock.report.line', 'report_id_to', string="Report Lines To", readonly=True)
    report_differences = fields.One2many('stock.report.difference', 'report_id', string="Report Differences", readonly=True)

    product_list = fields.One2many('product.product', compute='_compute_product_list', string="Product List", store=False)
    
    @api.depends('report_lines_from', 'report_lines_to')
    def _compute_product_list(self):
        product_ids = set(self.report_lines_from.mapped('product_id.id') + self.report_lines_to.mapped('product_id.id'))
        self.product_list = self.env['product.product'].browse(list(product_ids))

    @api.onchange('date_from', 'date_to', 'company_id')
    def _onchange_dates(self):
        self.name = f"No vendido del {self.date_from} al {self.date_to}"
    
    def generate_reports(self):
        self._generate_report_lines(self.date_from, 'report_lines_from')
        self._generate_report_lines(self.date_to, 'report_lines_to')
        self._calculate_differences()
        self.write({'state': 'aprobado'})

    def _generate_report_lines(self, date, field_name):
        StockQuant = self.env['stock.valuation.layer']
        quants = StockQuant.search([('create_date', '<=', date), ('company_id', '=', self.company_id.id)])
        
        product_quantities = {}
        for quant in quants:
            if quant.product_id.active and quant.product_id.detailed_type not in ['consu', 'service'] and quant.product_id.list_price > 0:
                product_id = quant.product_id.id
                quantity = quant.quantity
                product_quantities[product_id] = product_quantities.get(product_id, 0) + quantity

        lines = [(0, 0, {'product_id': product_id, 'quantity': quantity}) for product_id, quantity in product_quantities.items()]
        self.write({field_name: lines})

    def _calculate_differences(self):
        lines_from = {line.product_id.id: line for line in self.report_lines_from}
        lines_to = {line.product_id.id: line for line in self.report_lines_to}
        differences = []
        
        for product_id in set(lines_from.keys()).union(lines_to.keys()):
            qty_from = lines_from.get(product_id, 0).quantity if product_id in lines_from else 0
            qty_to = lines_to.get(product_id, 0).quantity if product_id in lines_to else 0
            
            if qty_from != qty_to:
                product = self.env['product.product'].browse(product_id)
                differences.append((0, 0, {
                    'product_id': product_id,
                    'quantity_from': qty_from,
                    'quantity_to': qty_to,
                    'quantity_difference': qty_to - qty_from,
                    'lst_price': product.lst_price * qty_to,
                    'standard_price': product.standard_price * qty_to,
                    'linea': product.x_ingresotk,
                    'marca': product.marca_id.name,
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
        
        def escribir_hoja(worksheet, encabezados, datos, col_widths, formatos):
            for col, width in enumerate(col_widths):
                worksheet.set_column(col, col, width)
            
            for col, encabezado in enumerate(encabezados):
                worksheet.write(0, col, encabezado, header_format)
            
            for row, record in enumerate(datos, start=1):
                for col, value in enumerate(record):
                    worksheet.write(row, col, value, formatos[col])
        
        encabezados_reports_differences = ['Producto', 'Cantidad inicial', 'Cantidad final', 'Movimiento', 'Precio de coste', 'Precio de venta']
        col_widths_reports_differences = [45, 25, 25, 25, 25, 25]
        formatos_reports_differences = [None, number_format, number_format, number_format, currency_format, currency_format]
        
        datos_differences = [
            (record.product_id.name, record.quantity_from, record.quantity_to, record.quantity_difference, record.standard_price, record.lst_price)
            for record in self.report_differences
        ]
        
        escribir_hoja(worksheet_sin_movimiento, encabezados_reports_differences, datos_differences, col_widths_reports_differences, formatos_reports_differences)
        
        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': f'reporte_movimiento_inventario_{self.date_from}_{self.date_to}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'store_fname': f'reporte_movimiento_inventario_{self.date_from}_{self.date_to}.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


class StockReportLine(models.Model):
    _name = 'stock.report.line'
    _description = 'Stock Report Line'

    report_id_from = fields.Many2one('stock.report.history', string="Reporte Inicial", ondelete='cascade')
    report_id_to = fields.Many2one('stock.report.history', string="Reporte Final", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Producto", required=True)
    quantity = fields.Float(string="Cantidad al día", required=True)


class StockReportDifference(models.Model):
    _name = 'stock.report.difference'
    _description = 'Stock Report Difference'

    report_id = fields.Many2one('stock.report.history', string="Reporte", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Producto", required=True)
    quantity_from = fields.Float(string="Cantidad Inicial", required=True)
    quantity_to = fields.Float(string="Cantidad Final", required=True)
    quantity_difference = fields.Float(string="Movimiento", required=True)
    lst_price = fields.Float(string="Precio de venta", required=True)
    standard_price = fields.Float(string="Precio de coste", required=True)
    linea = fields.Char(string="Línea")
    marca = fields.Char(string="Marca")
