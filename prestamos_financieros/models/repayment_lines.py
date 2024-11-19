# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

import logging
import math


_logger = logging.getLogger(__name__)

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
    amount_capital_loan = fields.Float(string='Capital',copy=False)
    
    interest_rate = fields.Float(string='Interes',copy=False, digits=dp.get_precision('Product Unit of Measure'))
    interest_generated = fields.Float(string='Interes generado',copy=False, default=0, digits=(16, 2))
    interest_on_arrears = fields.Float(string='Interes moratorio',copy=False, default=0,)
    
    balance = fields.Float(string='Saldo',readonly=True,copy=False)
    bills = fields.Float(string='Gastos',copy=False)
    
    amount_pay = fields.Float(string='Se pago ', track_visibility='onchange', copy=False,readonly=True, digits=(16, 2))
    recibir_pagos = fields.Many2one("account.journal", "Recibir pagos",)
    invoice_id = fields.Many2many("account.move", string="Factura", track_visibility='onchange',copy=False,)
    payment_ids = fields.Many2many("account.payment", string="Pagos", track_visibility='onchange',copy=False,)
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

    
    
    
    invoice = fields.Boolean(string="Factura Intereses", default=False,)

    def action_view_invoice(self):
        invoices = self.mapped('invoice_id')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view_id = self.env.ref('account.view_move_form').id
            action['views'] = [(form_view_id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        
        return action
    
    def action_view_payment(self):
        patment = self.mapped('payment_ids')
        action = self.env.ref('account.action_account_payments').read()[0]
        if len(patment) > 1:
            action['domain'] = [('id', 'in', patment.ids)]
        elif len(patment) == 1:
            action['views'] = [
                (self.env.ref('account.view_account_payment_form').id, 'form')]
            action['res_id'] = patment.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    
    def action_pay_emi(self):
        """Crear factura para los intereses"""
        time_now = self.date_due

        for rec in self:
            loan_lines_ids = self.env['repayment.line'].search(
                [('loan_id', '=', rec.loan_id.id)], order='date_due asc')
            for line in loan_lines_ids:
                if line.date_due < rec.date_due and line.state in \
                        ('unpaid', 'invoiced'):
                    message_id = self.env['message.popup'].create(
                        {'message': (
                            "Tiene cuotas pendientes que pagar")})
                    return {
                        'name': 'Repayment',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'message.popup',
                        'res_id': message_id.id,
                        'target': 'new'
                    }

        invoice = self.env['account.move']
        
        lineas = []
        if self.interest_generated > 0:
            val_lineas = { 
            'name': 'Cobro de interes mensual de ' + str(self.loan_id.interest_rate) + '%',
            'account_id': self.loan_id.account_id.id,
            'price_unit': self.interest_generated,
            'quantity': 1,
            'product_id':False,
            'x_user_id': self.env.user.id
            }
            lineas.append((0, 0, val_lineas))

        if self.interest_on_arrears > 0:
            val_lineas1 = {
                'name': 'Interes moratorios por incumplimiento de pago',
                'account_id': self.loan_id.account_int_moratorio.id,
                'price_unit': self.interest_on_arrears,
                'quantity': 1,
                'product_id':False,
                'x_user_id': self.env.user.id
            }
            lineas.append((0, 0, val_lineas1))
            
        val_encabezado = {
            'move_type': 'out_invoice',
            'invoice_date': time_now,
            'partner_id': self.partner_id.id,
            'currency_id': self.company_id.currency_id.id,
            'payment_reference': self.name,
            'invoice_line_ids': lineas
        }
        
        account_invoice_id = invoice.create(val_encabezado)
        
        # Aplicar el pago a la factura existente

        capital_invoice = self.env['account.move'].browse(self.loan_id.invoice_cxc_ids[0].id)
        #_logger.warning('Factura : ' + str(capital_invoice.name))
        if not capital_invoice:
            raise UserError("No se encontró la factura del capital.")

        # Suponiendo que ya esta la factura cargada en 'capital_invoice
        # Creamos un nuevo pago
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',  # o 'outbound' dependiendo del tipo de pago, este es para recibir dineros
            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            'partner_type': 'customer',
            'payment_reference': capital_invoice.name,
            'partner_id': capital_invoice.partner_id.id,
            'amount': self.amount_capital_quota,  # reemplaza con el monto del pago
            'currency_id': capital_invoice.currency_id.id,
            'reconciled_invoice_ids': [(4, capital_invoice.id)],
            #'account_id': capital_invoice.partner_id.property_account_payable_id.id,  # configuramos la cuenta por pagar
        })

        # Registramos el pago
        payment.action_post()
        
        self.loan_id.write({
            'remaining_capital': self.loan_id.remaining_capital - self.amount_capital_quota,
            'pay_capital': self.loan_id.pay_capital + self.amount_capital_quota
        })


        
        if account_invoice_id and payment:
            self.invoice = True
            
            self.write({
                'invoice_id': [(6, 0, [account_invoice_id.id])],
                'payment_ids': [(6, 0, [payment.id])],
                'state': 'invoiced'
            })

        return {
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': account_invoice_id.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
        }
