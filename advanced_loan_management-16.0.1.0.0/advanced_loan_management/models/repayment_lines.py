# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class RepaymentLine(models.Model):
    """ Cuotas"""
    _name = "repayment.line"
    _description = "Repayment Line"

    def __type_prestamo(self):
        if self.loan_id:
            return self.loan_id.loan_type_id
        
    #Datos de la cuota
    name = fields.Char(string="Cuota ", default="/", readonly=True,)
    description = fields.Text(copy=False)
    partner_id = fields.Many2one('res.partner', string="Partner",required=True,)
    company_id = fields.Many2one('res.company', string='Company',readonly=True,
                                 default=lambda self: self.env.company)
    
    #Datos de los pagos
    date_due = fields.Date(string="Fecha de pago", required=True, default=fields.Date.today(),readonly=True,)
    payment_date = fields.Date(string='Fecha pagado',copy=False,)
    amount = fields.Float(string="Cuota", required=True, digits=(16, 2))
    amount_capital_quota = fields.Float(string='Capital de cuota',copy=False)
    amount_capital = fields.Float(string='Capital',copy=False)
    interest_rate = fields.Float(string='Interes',copy=False, digits=dp.get_precision('Product Unit of Measure'))
    interest_generated = fields.Float(string='Interes generado',copy=False, default=0, digits=(16, 2))
    interest_on_arrears = fields.Float(string='Interes moratorio',copy=False, default=0,)
    balance = fields.Float(string='Saldo',readonly=True,copy=False)
    bills = fields.Float(string='Gastos',copy=False)
    
    amount_pay = fields.Float(string='Se pago ', track_visibility='onchange', copy=False,readonly=True, digits=(16, 2))
    recibir_pagos = fields.Many2one("account.journal", "Recibir pagos", store=True, default=lambda self: self.
                                      env['account.journal'].search([('code', 'like', 'CSH1')]),  domain=[('type','=','bank')],)
    invoice_id = fields.Many2one("account.move", "Factura", track_visibility='onchange',copy=False,)
    is_pagado = fields.Boolean(string='Pagado', default=False)
    invoice = fields.Boolean(string="invoice", default=False,)
    interest_account_id = fields.Many2one('account.account',
                                          string="Cuenta de Interes",
                                          store=True,)
    
    #Datos del prestamo
    loan_id = fields.Many2one('loan.request', string="Loan Ref.",
                              help="Loan",
                              readonly=True)
    type_prestamo = fields.Char(string='Tipo', default=__type_prestamo)
       
    
    state = fields.Selection(string="State",
                             selection=[('unpaid', 'Sin pagar'),
                                        ('invoiced', 'Facturado sin pagar'),
                                        ('paid', 'Pagado')],
                             required=True, readonly=True, copy=False,
                             tracking=True, default='unpaid',)

    
    
    repayment_account_id = fields.Many2one('account.account',
                                           string="Repayment",
                                           store=True,
                                           help="Account For Repayment")
    invoice = fields.Boolean(string="Factura Intereses", default=False,)

    def action_pay_emi(self):
        """Creates invoice for each EMI"""
        time_now = self.date
        interest_product_id = self.env['ir.config_parameter'].sudo().get_param(
            'advanced_loan_management.interest_product_id')
        repayment_product_id = self.env['ir.config_parameter'].sudo().get_param(
            'advanced_loan_management.repayment_product_id')

        for rec in self:
            loan_lines_ids = self.env['repayment.line'].search(
                [('loan_id', '=', rec.loan_id.id)], order='date asc')
            for line in loan_lines_ids:
                if line.date < rec.date and line.state in \
                        ('unpaid', 'invoiced'):
                    message_id = self.env['message.popup'].create(
                        {'message': (
                            "You have pending amounts")})
                    return {
                        'name': 'Repayment',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'message.popup',
                        'res_id': message_id.id,
                        'target': 'new'
                    }

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': time_now,
            'partner_id': self.partner_id.id,
            'currency_id': self.company_id.currency_id.id,
            'payment_reference': self.name,
            'invoice_line_ids': [
                (0, 0, {
                    'price_unit': self.amount,
                    'product_id': repayment_product_id,
                    'name': 'Repayment',
                    'account_id': self.repayment_account_id.id,
                    'quantity': 1,
                }),
                (0, 0, {
                    'price_unit': self.interest_amount,
                    'product_id': interest_product_id,
                    'name': 'Interest amount',
                    'account_id': self.interest_account_id.id,
                    'quantity': 1,
                }),
            ],
        })
        if invoice:
            self.invoice = True
            self.write({'state': 'invoiced'})

        return {
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
        }
