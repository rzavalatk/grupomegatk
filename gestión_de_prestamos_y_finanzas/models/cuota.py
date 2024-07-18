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
    
    #Datos del prestamo
    prestamo_id = fields.Many2one('prestamo', string='Préstamo', required=True, ondelete='cascade')
    type_prestamo = fields.Char(string='Tipo', default=__type_prestamo)
    
    state = fields.Selection( [('draft', 'Borrador'), ('cancelado', 'Cancelado'), ('validado', 'Validado'),('pay', 'Pagado')], string="Estado", default='draft')
    
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

    """def pagar(self):
        obj_factura = self.env["account.move"]
        lineas = []
        if self.interest_generated > 0:
            val_lineas = {
            'name': 'Cobro de interes mensual de ' + str(self.interest_rate) + '%',
            'account_id': self.prestamo_id.account_id,
            'price_unit': self.interest_generated,
            'quantity': 1,
            'product_id': False,
            'x_user_id': self.env.user.id
            }
            lineas.append((0, 0, val_lineas))

        if self.interest_on_arrears > 0:
            val_lineas1 = {
                'name': 'Interes moratorios por incumplimiento de pago',
                'account_id': self.interest_generated,
                'price_unit': self.interest_on_arrears,
                'quantity': 1,
                'product_id': False,
                'x_user_id': self.env.user.id
            }
            lineas.append((0, 0, val_lineas1))
        
        company_id = self.company_id.id
        
        val_encabezado = {
            'move_type': 'out_invoice',
            #'invoice_line_ids': self.prestamo_id.partner_id.property_account_receivable_id.id,
            'partner_id': self.prestamo_id.partner_id.id,
            #'journal_id': journal_id,
            'currency_id': self.prestamo_id.currency_id.id,
            'company_id': company_id,
            'user_id': self.env.user.id,
            'invoice_line_ids': lineas,
        }
        
        account_invoice_id = obj_factura.create(val_encabezado)
        
        
        capital = self.amount_pay - (self.interest_generated)
        
        if self.amount > 0:
            obj_paymet_id = self.env["account.payment"]
            val_payment = {
                'payment_type': 'inbound',
                'company_id': company_id,
                'partner_type': 'customer',
                'partner_id': self.prestamo_id.partner_id.id,
                'amount': self.amount,
                'currency_id': self.prestamo_id.currency_id.id,
                'journal_id': self.prestamo_id.recibir_pagos.id,
                'payment_date': self.payment_date,
                'communication': self.prestamo_id.name + ' ' + self.name,
                'payment_method_id': 1
            }
            paymet_id = obj_paymet_id.create(val_payment)
            paymet_id.post()
            vals= {
                'invoice_cxc_ids': [(4, account_invoice_id.id, 0)],
                'payment_ids': [(4, paymet_id.id, 0)]
            }
        else:
            vals= {
                    'invoice_cxc_ids': [(4, account_invoice_id.id, 0)],
                }   
        self.prestamo_id.write(vals) 
        # capital_real = self.cuota_capital + self.cuota_interes
        if capital != 0:
            # if self.pago < self.cuota_prestamo:
            #     saldo = self.cuota_capital + self.cuota_interes + self.interes_moratorio  - self.pago
            # elif self.pago == capital_real:
            #     saldo = self.cuota_capital + self.cuota_interes - self.pago
            # elif self.pago > self.cuota_prestamo:
            #     saldo = self.cuota_capital - self.pago
            # else:
            #     saldo = self.saldo
            saldo = self.amount_capital_quota + self.interest_generated + self.interest_on_arrears - self.amount_pay
            if 0 >= saldo: 
                vals_c= {
                    'monto_restante': saldo,
                    'state': 'finalizado'
                }
            else:
                vals_c= {
                    'monto_restante': saldo
                }

            self.prestamo_id.write(vals_c)

            if self.saldo > 0 and abs(self.pago - self.cuota_prestamo) > 0.01:
                tasa = self.cuotas_prestamo_id.tasa / 100
                cuota = self.pago - self.gastos
                self.cuotas_prestamo_id._cuotas(saldo,tasa,cuota,0,self.interes_generado)
        self.write({
            'invoice_id' : account_invoice_id.id,
            'state': 'hecho',
            })

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
        return super(PrestamosCuotas, self).unlink()
"""