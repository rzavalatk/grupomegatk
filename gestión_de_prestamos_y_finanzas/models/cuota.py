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
    payment_date = fields.Date(string='Fecha de pago',copy=False,)
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
    
    state = fields.Selection( [('draft', 'Borrador'), ('cancelado', 'Cancelado'), ('proceso', 'Proceso de pago'),('pagado', 'Pagado')], string="Estado", default='draft')
    
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

    def generar_factura(self):
        for cuota in self:
            factura = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': cuota.prestamo_id.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'name': 'Cuota de Préstamo',
                    'quantity': 1,
                    'price_unit': cuota.amount,
                })]
            })
            cuota.write({'pagado': True})
