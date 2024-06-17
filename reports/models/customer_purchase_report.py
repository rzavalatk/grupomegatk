from odoo import models, fields, api

import logging
from datetime import datetime
from datetime import date


_logger = logging.getLogger(__name__)

class CustomerPurchaseReport(models.Model):
    _name = 'customer.purchase.report'
    _description = 'Customer No Purchase Report'

    @api.onchange('date_from','date_to','company_id')
    def _onchange_date_from(self):
        self.name = "Reporte de Clientes inactivos de " + str(self.company_id.name) + " del " +str(self.date_from) + " al " + str(self.date_to)
    
    
    report_lines_from_customer_purchase = fields.One2many(
        'customer.purchase.report.line', 'report_purchase_customers', string="Clientes que compraron en el intervalo de tiempo 1", readonly=True)
    
    report_lines_to_customer_purchase = fields.One2many(
        'customer.purchase.report.line', 'report_to_purchase_customer', string="Clientes que compraron en el intervalo de tiempo 2", readonly=True)

    report_differences = fields.One2many(
        'customer.purchase.report.line.difference', 'report_id', string="Report Differences", readonly=True)
    
    report_differences_OI = fields.One2many(
        'customer.purchase.report.line.difference', 'report_id_OI', string="Report Differences", readonly=True)
    
    name = fields.Char(string="Nombre de reporte", required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    
    date_from_i2 = fields.Date(string='Fencha inicio')
    date_to_i2 = fields.Date(string='Fecha final')

    def generate_reports(self):
        line_from = self._get_customers_purchase( self.date_from, self.date_to, 'report_lines_from_customer_purchase')
        line_to = self._get_customers_purchase( self.date_from_i2, self.date_to_i2, 'report_lines_to_customer_purchase')
        #self._get_customers_no_purchase('report_lines_from_no_customer_purchase')
        self._get_customers_difference(line_from, line_to)
        
    def _get_customers_purchase(self,date1, date2, field_name):
        #Busqueda para todas las facturas en el periodo de tiempo 1 (Periodo de clientres que si han comprado)
        domain = ['&', '&', '&', '&',
            ('company_id', '=', self.company_id.id),
            ('invoice_date', '>=', date1),
            ('invoice_date', '<=', date2),
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
        ]
        account_orders = self.env['account.move'].search(domain)
        
        #Lista de todos los clientes y luego lista con todos los ids de los clientes
        customer_list = account_orders.mapped('partner_id')
        customer_ids = account_orders.mapped('partner_id.id')
        
        #Proceso para escribir los clientes que si han comprado en ese periodo de tiempo 1
        lines = []
        for customer_item in customer_list:
            n = True
            for invoice_item in customer_item.invoice_ids: #TODAS LAS FACTURAS DEL CLIENTE YA SEAN COMPRAS, VENTAS O COTIZACONES
                if n:
                    if invoice_item.move_type == 'out_invoice':
                        if invoice_item.invoice_date and isinstance(invoice_item.invoice_date, date):
                            if invoice_item.invoice_date <= date2: 
                                if invoice_item.invoice_date >= date1:
                                    n = False 
                                    lines.append((0, 0, {
                                        'partner_id': customer_item.id,
                                        'last_purchase': invoice_item.id,
                                        'purchase_date': invoice_item.invoice_date,
                                        'purchase_comercial': invoice_item.invoice_user_id.id,
                                        'purchase_amount': invoice_item.amount_total,
                                        'purchase_term_id': invoice_item.invoice_payment_term_id.display_name,
                                    }))         
                    else:
                        n = True
        if lines:
            self.write({field_name: lines})
        
        return customer_ids    
        
    
    def _get_customers_difference(self, list_from, list_to):
        self.ensure_one()
        differences = []
        differences_OI = []
        
        for item_from in list_from:
            #partner = self.env['res.partner'].search(['id', '=', str(item_from)])
            #_logger.warning(item_from)
            if item_from in list_to:
               
                differences.append((0, 0, {
                    'partner_id': item_from,
                    'company_id': self.company_id.id,
                    
                }))
            else:
                differences_OI.append((0, 0, {
                    'partner_id': item_from,
                    'company_id': self.company_id.id,
                    
                }))
        self.report_differences = differences
        self.report_differences_OI = differences
        
        

class CustomerReportLine(models.Model):
    _name = 'customer.purchase.report.line'
    _description = 'Customer purchase Report Line'
    
    
    report_purchase_customers = fields.Many2one(
        'customer.purchase.report', string="Clientes que compraron en el intervalo de tiempo 1", ondelete='cascade')
    
    report_to_purchase_customer = fields.Many2one(
        'customer.purchase.report', string="Clientes que compraron en el intervalo de tiempo 2", ondelete='cascade')
    
    partner_id = fields.Many2one('res.partner', string='Customer')
    last_purchase = fields.Many2one('account.move', string='Ultima compra')
    purchase_date = fields.Date('Fecha')
    purchase_comercial = fields.Many2one('res.users', string='Comercial')
    purchase_amount = fields.Float('Valor')
    purchase_term_id = fields.Char('Termino de pago')
    #location_id = fields.Many2one('stock.location', string="Location", required=True)
    #date_create = fields.Datetime(string="Create Date", required=True)
    
class CustomerReportLineDifference(models.Model):
    _name = 'customer.purchase.report.line.difference'
    _description = 'Customer purchase Report Line difference'

    report_id = fields.Many2one(
        'customer.purchase.report', string="Reporte", ondelete='cascade')
    
    report_id_OI = fields.Many2one(
        'customer.purchase.report', string="Reporte", ondelete='cascade')
    
    partner_id = fields.Many2one('res.partner', string='Customer')
    company_id = fields.Many2one('res.company', string='Compañia')
    email = fields.Text('email')
    phone = fields.Text('telefono')