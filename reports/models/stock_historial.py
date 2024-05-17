from odoo import models, fields, api
from datetime import datetime

class StockReportHistory(models.Model):
    _name = 'stock.report.history'
    _description = 'Stock Report History'

    name = fields.Char(string="Report Name", required=True)
    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    report_lines_from = fields.One2many('stock.report.line', 'report_id_from', string="Report Lines From", readonly=True)
    report_lines_to = fields.One2many('stock.report.line', 'report_id_to', string="Report Lines To", readonly=True)
    report_differences = fields.One2many('stock.report.difference', 'report_id', string="Report Differences", readonly=True)

    def generate_reports(self):
        self._generate_report_lines(self.date_from, 'report_lines_from')
        self._generate_report_lines(self.date_to, 'report_lines_to')
        self._calculate_differences()

    def _generate_report_lines(self, date, field_name):
        self.ensure_one()
        StockQuant = self.env['stock.quant']
        quants = StockQuant.search([('inventory_date', '<=', date)])
        lines = []
        for quant in quants:
            lines.append((0, 0, {
                'product_id': quant.product_id.id,
                'quantity': quant.quantity,
                'location_id': quant.location_id.id,
            }))
        self.write({field_name: lines})

    def _calculate_differences(self):
        self.ensure_one()
        lines_from = {line.product_id.id: line for line in self.report_lines_from}
        lines_to = {line.product_id.id: line for line in self.report_lines_to}
        differences = []
        for product_id in set(lines_from.keys()).union(lines_to.keys()):
            qty_from = lines_from.get(product_id, {}).get('quantity', 0)
            qty_to = lines_to.get(product_id, {}).get('quantity', 0)
            differences.append((0, 0, {
                'product_id': product_id,
                'quantity_from': qty_from,
                'quantity_to': qty_to,
                'quantity_difference': qty_to - qty_from,
            }))
        self.report_differences = differences

class StockReportLine(models.Model):
    _name = 'stock.report.line'
    _description = 'Stock Report Line'

    report_id_from = fields.Many2one('stock.report.history', string="Report From", ondelete='cascade')
    report_id_to = fields.Many2one('stock.report.history', string="Report To", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity = fields.Float(string="Quantity", required=True)
    location_id = fields.Many2one('stock.location', string="Location", required=True)

class StockReportDifference(models.Model):
    _name = 'stock.report.difference'
    _description = 'Stock Report Difference'

    report_id = fields.Many2one('stock.report.history', string="Report", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity_from = fields.Float(string="Quantity From", required=True)
    quantity_to = fields.Float(string="Quantity To", required=True)
    quantity_difference = fields.Float(string="Quantity Difference", required=True)
