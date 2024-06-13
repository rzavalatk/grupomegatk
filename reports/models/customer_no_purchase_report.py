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
    partner_id = fields.Many2one('res.partner', string='Customer')
    company_id = fields.Many2one('res.company', string='Company')
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')

    
    def get_customers_no_purchase(self):
        domain = ['&', '&', '&', '&',
            ('company_id', '=', self.company_id.id),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_refund'),
        ]
        account_orders = self.env['account.move'].search(domain)
        customer_ids = account_orders.mapped('partner_id.id')
        
        _logger.warning(len(account_orders))
        _logger.warning(len(customer_ids))
        
        for partner in customer_ids:
            _logger.warning(partner.name)
        

        domain_customers = [
            ('company_id', '=', self.company_id.id),
            ('id', 'not in', customer_ids)
        ]
        customers = self.env['res.partner'].search(domain_customers)
        
        report_lines = []
        for customer in customers:
            customer_domain = [
            ('company_id', '=', self.company_id.id),
            ('partner_id', '=', customer.id),
            ('payment_state', 'in', ['paid']),
            ('state', 'in', ['posted']),
            ('move_type', 'in', ['out_refund']),
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
    _name = 'customer.no.purchase.report.line'
    _description = 'Customer Report Line'

    #location_id = fields.Many2one('stock.location', string="Location", required=True)
    #date_create = fields.Datetime(string="Create Date", required=True)