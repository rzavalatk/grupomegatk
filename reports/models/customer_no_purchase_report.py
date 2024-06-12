from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)

class CustomerNoPurchaseReport(models.TransientModel):
    _name = 'customer.no.purchase.report'
    _description = 'Customer No Purchase Report'

    partner_id = fields.Many2one('res.partner', string='Customer')
    company_id = fields.Many2one('res.company', string='Company')
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')

    @api.model
    def get_customers_no_purchase(self, company_id, date_from, date_to):
        domain = [
            ('company_id', '=', company_id),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('state', 'in', ['posted']),
            ('move_type', 'in', ['out_refund']),
        ]
        account_orders = self.env['account.move'].search(domain)
        customer_ids = account_orders.mapped('partner_id.id')
        
        _logger.warning(customer_ids)

        domain_customers = [
            ('company_id', '=', company_id),
            ('id', 'not in', customer_ids)
        ]
        customers = self.env['res.partner'].search(domain_customers)
        
        report_lines = []
        for customer in customers:
            customer_domain = [
            ('company_id', '=', company_id),
            ('partner_id', '=', customer.id),
            ('payment_state', 'in', ['paid']),
            ('state', 'in', ['posted']),
            ('move_type', 'in', ['out_refund']),
            ]
            
            customer_orders = self.env['account.move'].search(customer_domain)
            
            _logger.warning(customer_ids)
        
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