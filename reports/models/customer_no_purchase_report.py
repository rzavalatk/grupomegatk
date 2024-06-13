from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)

class CustomerNoPurchaseReport(models.TransientModel):
    _name = 'customer.no.purchase.report'
    _description = 'Customer No Purchase Report'

    @api.onchange('date_from','date_to','company_id')
    def _onchange_date_from(self):
        self.name = "Reporte de Clientes inactivos de " + str(self.company_id.name) + " del " +str(self.date_from) + " al " + str(self.date_to)
    

    name = fields.Char(string="Nombre de reporte", required=True)
    company_id = fields.Many2one('res.company', string='Company')
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')

    
    def get_customers_no_purchase(self):
        domain = ['&', '&', '&', '&',
            ('company_id', '=', self.company_id.id),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
        ]
        account_orders = self.env['account.move'].search(domain)
        customer_list = account_orders.mapped('partner_id')
        customer_ids = account_orders.mapped('partner_id.id')
        
        n = 4 
        
        for customer_item in customer_list:
            if n < 5:
                _logger.warning(customer_item.name)
                _logger.warning(len(customer_item.invoice_ids))
                for invoice_item in customer_item.invoice_ids:
                    _logger.warning(invoice_item.internal_number)
        
        """_logger.warning(len(account_orders))
        _logger.warning(len(customer_ids))"""
        
        domain_customers = ['&',
            ('company_id', '=', self.company_id.id),
            ('id', 'not in', customer_ids)
        ]
        customers = self.env['res.partner'].search(domain_customers)
        
        #_logger.warning(len(customers))
        
        report_lines = []
        for customer in customers:
            customer_domain = [
            ('company_id', '=', self.company_id.id),
            ('partner_id', '=', customer.id),
            ('payment_state', 'in', ['paid']),
            ('state', 'in', ['posted']),
            ('move_type', 'in', ['out_invoice']),
            ]
            
            customer_orders = self.env['account.move'].search(customer_domain)
            
            #_logger.warning(customer_orders)
        
            report_lines.append((0, 0, {
                'partner_id': customer.id,
                'company_id': self.company_id.id,
                'date_from': self.date_from,
                'date_to': self.date_to
            }))
            
        

class CustomerReportLine(models.Model):
    _name = 'customer.purchase.report.line'
    _description = 'Customer purchase Report Line'
    
    partner_id = fields.Many2one('res.partner', string='Customer')
    #location_id = fields.Many2one('stock.location', string="Location", required=True)
    #date_create = fields.Datetime(string="Create Date", required=True)