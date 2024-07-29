# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

class Cuota(models.Model):
    _name = 'cuota'
    _description = 'Modelo de Cuota'
    
    def __type_prestamo(self):
        if self.prestamo_id:
            return self.prestamo_id.loan_type
    
    #Datos de la cuota
    name = fields.Char('Numero',copy=False,required=True)
    description = fields.Text(copy=False)
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, default=lambda self: self.env.user.company_id)
    res_partner_id = fields.Many2one('res.partner', string='Cliente',domain=[('customer','=',True), ],copy=False)
    
    #Datos de los pagos
    date_due = fields.Date(string='Fecha limite',copy=False,)
    payment_date = fields.Date(string='Fecha pagado',copy=False,)
    amount = fields.Float(string='Cuota',copy=False)
    amount_capital_quota = fields.Float(string='Capital de cuota',copy=False)
    amount_capital = fields.Float(string='Capital',copy=False)
    interest_rate = fields.Float(string='Interes',copy=False, digits=dp.get_precision('Product Unit of Measure'))
    interest_generated = fields.Float(string='Interes generado',copy=False, default=0,)
    interest_on_arrears = fields.Float(string='Interes moratorio',copy=False, default=0,)
    balance = fields.Float(string='Saldo',readonly=True,copy=False)
    bills = fields.Float(string='Gastos',copy=False)
    amount_pay = fields.Float(string='Pago', track_visibility='onchange',copy=False,readonly=True,)
    recibir_pagos = fields.Many2one("account.journal", "Recibir pagos",  domain=[('type','=','bank')],)
    invoice_id = fields.Many2one("account.move", "Factura", track_visibility='onchange',copy=False,)
    is_pagado = fields.Boolean(string='Pagado', default=False)
    invoice = fields.Boolean(string="invoice", default=False,)
    
    #Datos del prestamo
    prestamo_id = fields.Many2one('prestamo', string='Préstamo', required=True, ondelete='cascade')
    type_prestamo = fields.Char(string='Tipo', default=__type_prestamo)
    
    state = fields.Selection( [('borrador', 'Borrador'), ('cancelado', 'Cancelado'),('invoiced','Factura'), ('unpaid', 'Sin pagar'),('pagado', 'Pagado')], string="Estado", default='draft')
    
    @api.depends('amount', 'amount_pay')
    def _compute_balance(self):
        for cuota in self:
            cuota.balance = cuota.amount - cuota.amount_pay

    def action_validate(self):
        for cuota in self:
            cuota.state = 'validado'

    def action_cancel(self):
        for cuota in self:
            cuota.state = 'cancelado'

    def action_pay(self):
        for cuota in self:
            cuota.is_pagado = True
            cuota.state = 'hecho'

    def action_pay_emi(self):
        
        time_now = self.date_due

        for rec in self:
            loan_lines_ids = self.env['cuota'].search(
                [('prestamo_id', '=', rec.prestamo_id.id)], order='date asc')
            for line in loan_lines_ids:
                if line.date_due < rec.date_due and line.state in \
                        ('unpaid', 'invoiced'):
                    message_id = self.env['message.popup'].create(
                        {'message': (
                            "Hay cuotas pendientes para pagar")})
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
            'name': 'Cobro de interes mensual de ' + str(self.prestamo_id.interest_rate) + '%',
            'account_id': self.prestamo_id.account_id.id,
            'price_unit': self.interest_generated,
            'quantity': 1,
            'product_id':False,
            'x_user_id': self.env.user.id
            }
            lineas.append((0, 0, val_lineas))

        if self.interest_on_arrears > 0:
            val_lineas1 = {
                'name': 'Interes moratorios por incumplimiento de pago',
                'account_id': self.prestamo_id.account_int_moratorio.id,
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
        
        # Crear el pago
        payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'amount': self.amount,  # Monto del capital
            'currency_id': self.company_id.currency_id.id,
            'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
            'journal_id': self.journal_id.id,  # Diario desde donde se hará el pago
            'payment_date': time_now,
        })

        # Confirmar el pago
        payment.action_post()

        # Reconciliar el pago con la factura
        #(invoice + payment).line_ids.filtered(lambda line: line.account_id == self.repayment_account_id).reconcile()

        
        if invoice:
            self.invoice = True
            self.write({'state': 'invoiced'})

        return {
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': account_invoice_id.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
        }

    def action_view_invoice(self):
        invoices = self.mapped('invoice_id')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.move_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def cancelar(self):
        if self.state == 'hecho':
            raise Warning(_('No se puede eliminar o cancelar una cuota en estado '+ self.state))
        else:
            self.pago = ''
            self.write({'state': 'cancelado'})

    def back_draft(self):
        self.write({'state': 'draft'})

    def unlink(self):
        for cuota in self:
            if cuota.state != 'draft':
                raise Warning(_('No se puede eliminar o cancelar una cuota en estado '+ cuota.state))
        return super(Cuota, self).unlink()
