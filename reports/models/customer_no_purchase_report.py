from odoo import models, fields, api

import logging
from datetime import datetime
from datetime import date


_logger = logging.getLogger(__name__)

class CustomerNoPurchaseReport(models.Model):
    _name = 'customer.no.purchase.report'
    _description = 'Customer No Purchase Report'

    @api.onchange('date_from','date_to','company_id')
    def _onchange_date_from(self):
        self.name = "Reporte de Clientes inactivos de " + str(self.company_id.name) + " del " +str(self.date_from) + " al " + str(self.date_to)
    
    
    report_lines_from_customer_purchase = fields.One2many(
        'customer.purchase.report.line', 'report_purchase_customer', string="Clientes que compraron en el intervalo de tiempo", readonly=True)
    
    report_lines_from_no_customer_purchase = fields.One2many(
        'customer.purchase.report.line', 'report_no_purchase_customer', string="Clientes que no compraron en el intervalo de tiempo", readonly=True)

    name = fields.Char(string="Nombre de reporte", required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')

    def generate_reports(self):
        self._get_customers_purchase('report_lines_from_customer_purchase')
        self._get_customers_no_purchase('report_lines_from_no_customer_purchase')
        #self._calculate_differences()
    
    def _get_customers_purchase(self, field_name):
        #Busqueda para todas las facturas en el periodo de tiempo 1 (Periodo de clientres que si han comprado)
        domain = ['&', '&', '&', '&',
            ('company_id', '=', self.company_id.id),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
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
                            if invoice_item.invoice_date <= self.date_to: 
                                if invoice_item.invoice_date >= self.date_from:
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
    
    def _get_customers_no_purchase(self, field_name):
        
        #Busqueda para todas las facturas en el periodo de tiempo 1 (Periodo de clientres que si han comprado)
        domain = ['&', '&', '&', '&',
            ('company_id', '=', self.company_id.id),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
        ]
        account_orders = self.env['account.move'].search(domain)
        
        #lista con todos los ids de los clientes
        customer_ids = account_orders.mapped('partner_id.id')      
        
        #Busqueda de los clientes que no han comprado
        domain_customers = ['&',
            ('company_id', '=', self.company_id.id),
            ('id', 'not in', customer_ids)
        ]
        customers = self.env['res.partner'].search(domain_customers)
        
        
               
        
        
        
        #Proceso para agregar los clientes que no compraron
        
        lines = []
        for customer_item in customers:
            n = True
            for invoice_item in customer_item.invoice_ids: #TODAS LAS FACTURAS DEL CLIENTE YA SEAN COMPRAS, VENTAS O COTIZACONES
                if n:
                    if invoice_item.move_type == 'out_invoice':
                        if invoice_item.invoice_date and isinstance(invoice_item.invoice_date, date):
                            if invoice_item.invoice_date >= self.date_to: 
                                if invoice_item.invoice_date <= self.date_from:
                                    n = False 
                                    _logger.warning(customer_item.id)
                                    _logger.warning(invoice_item.id)
                                    _logger.warning(invoice_item.invoice_date.year)
                                    _logger.warning(invoice_item.invoice_user_id.id)
                                    _logger.warning(invoice_item.amount_total)
                                    _logger.warning(invoice_item.invoice_payment_term_id.display_name)         
                    else:
                        n = True
        if lines:
            self.write({field_name: lines})
            
        

class CustomerReportLine(models.Model):
    _name = 'customer.purchase.report.line'
    _description = 'Customer purchase Report Line'
    
    
    report_purchase_customer = fields.Many2one(
        'customer.no.purchase.report', string="Clientes que compraron en el intervalo de tiempo", ondelete='cascade')
    
    report_no_purchase_customer = fields.Many2one(
        'customer.no.purchase.report', string="Clientes que no compraron en el intervalo de tiempo", ondelete='cascade')
    
    partner_id = fields.Many2one('res.partner', string='Customer')
    last_purchase = fields.Many2one('account.move', string='Ultima compra')
    purchase_date = fields.Date('Fecha')
    purchase_comercial = fields.Many2one('res.users', string='Comercial')
    purchase_amount = fields.Float('Valor')
    purchase_term_id = fields.Char('Termino de pago')
    #location_id = fields.Many2one('stock.location', string="Location", required=True)
    #date_create = fields.Datetime(string="Create Date", required=True)