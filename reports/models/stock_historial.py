from itertools import groupby

from odoo import models, fields, api
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class StockReportHistory(models.Model):
    _name = 'stock.report.history'
    _description = 'Stock Report History'

    name = fields.Char(string="Report Name", required=True)
    date_from = fields.Datetime(string="Start Date", required=True)
    date_to = fields.Datetime(string="End Date", required=True)
    company_id = fields.Many2one('res.company', string='Compañia')
    
    products_idsg = []
    
    report_lines_from = fields.One2many('stock.report.line', 'report_id_from', string="Report Lines From", readonly=True)
    report_lines_to = fields.One2many('stock.report.line', 'report_id_to', string="Report Lines To", readonly=True)
    report_differences = fields.One2many('stock.report.difference', 'report_id', string="Report Differences", readonly=True)

    def generate_reports(self):
        self._generate_report_lines(self.date_from, 'report_lines_from')
        #self._generate_report_lines(self.date_to, 'report_lines_to')
        #self._calculate_differences()

    def groupby_product(self, products_ids):
        group_products = groupby(products_ids, lambda x: x[0])
        _logger.warning(group_products)
        return next(group_products, True) and not next(group_products, False)
    
    def _generate_report_lines(self, date, field_name):
        
        StockQuant = self.env['stock.valuation.layer']
        
        quants = StockQuant.search(['&',
            ('create_date', '<=', date),
            ('company_id', '=', self.company_id.id)])
        
        #_logger.warning('Prueba reports : fecha='+ str(fecha_objeto))
        lines = []
        list_product = []
        
        
        for quant in quants:
            list_product.append([quant.product_id.id, quant.quantity, quant.create_date])
        
        _logger.warning( "tamaño de list_product" + str(len(list_product)))
        
        for key, group in groupby(list_product, lambda x: x[0]):
            quant_product = 0
            for quantity in group:
                quant_product = quant_product + quantity[1]
            
            self.products_idsg.append([key, quant_product])
        
        _logger.warning( "tamaño de products idsg" + str(len(self.products_idsg)))        
        
        
        _logger.warning("No entre")
        if self.products_idsg:
            _logger.warning("Entra")
            _logger.warning(self.products_idsg)            
        
        
            for line_product in self.products_idsg: 
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
    #location_id = fields.Many2one('stock.location', string="Location", required=True)
    #date_create = fields.Datetime(string="Create Date", required=True)

class StockReportDifference(models.Model):
    _name = 'stock.report.difference'
    _description = 'Stock Report Difference'

    report_id = fields.Many2one('stock.report.history', string="Report", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity_from = fields.Float(string="Quantity From", required=True)
    quantity_to = fields.Float(string="Quantity To", required=True)
    quantity_difference = fields.Float(string="Quantity Difference", required=True)


"""if self.products_groups:
                for line_product in self.products_groups:
          
                    
                    if line_product["product_id"]==quant.product_id.id:
                        _logger.warning( "Entre al IF" )
                        line_product['quantity'] = line_product['quantity'], + quant.quantity
                    else:
                        _logger.warning( "eNTRE AL ELSE" )
                        self.products_groups.append({
                            'product_id': quant.product_id.id,
                            'quantity': quant.quantity,
                            'date_create': quant.create_date, 
                        })
                    
            else:
                _logger.warning( "Primero" )
                self.products_groups.append({
                    'product_id': quant.product_id.id,
                    'quantity': quant.quantity,
                    'date_create': quant.create_date, 
                })"""