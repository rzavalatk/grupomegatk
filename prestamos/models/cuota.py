# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)


class PrestamosCuotas(models.Model):
    _name = 'prestamos.cuotas'
    _description = "Cuotas de los prestamos"
    # _order = "fecha_pago asc"

    @api.model
    def tipo(self):
        if self.cuotas_prestamo_id:
            return self.cuotas_prestamo_id.tipo_prestamo

    name = fields.Char('Numero',copy=False,required=True)
    description = fields.Text(copy=False)
    # currency_id = fields.Many2one('res.currency', 'Moneda',)
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, default=lambda self: self.env.user.company_id)
    res_partner_id = fields.Many2one('res.partner', string='Cliente',domain=[('customer','=',True), ],copy=False)
    state = fields.Selection( [('draft', 'Borrador'), ('cancelado', 'Cancelado'), ('validado', 'Validado'),('hecho', 'Hecho')], string="Estado", default='draft')
    cuotas_prestamo_id = fields.Many2one('prestamos', 'Prestamo',copy=False)
    tipo = fields.Char(string='Tipo', default=tipo)
    fecha_pago = fields.Date(string='Fecha limite',copy=False,)
    fecha_pagado = fields.Date(string='Fecha de pago',copy=False,)
    cuota_prestamo = fields.Float(string='Cuota',copy=False)
    cuota_capital = fields.Float(string='Capital',copy=False)
    cuota_interes = fields.Float(string='Interes',copy=False, digits=dp.get_precision('Product Unit of Measure'))
    interes_generado = fields.Float(string='Interes generado',copy=False, default=0,)
    interes_moratorio = fields.Float(string='Interes moratorio',copy=False, default=0,)
    saldo = fields.Float(string='Saldo',readonly=True,copy=False)
    gastos = fields.Float(string='Gastos',copy=False)
    pago = fields.Float(string='Pago', track_visibility='onchange',copy=False,readonly=True,)
    recibir_pagos = fields.Many2one("account.journal", "Recibir pagos",  domain=[('type','=','bank')],)
    invoice_id = fields.Many2one("account.move", "Factura", track_visibility='onchange',copy=False,)

    # @api.onchange('cuotas_prestamo_id')
    # def _onchange_cuotas_prestamo_id(self):
    #   self.currency_id = self.cuotas_prestamo_id.currency_id.id

    def validar(self):
        obj_factura = self.env["account.move"]
        lineas = []
        if self.cuota_interes > 0:
            val_lineas = {
            'name': 'Cobro de interes mensual de ' + str(self.cuotas_prestamo_id.tasa) + '%',
            'account_id': self.cuotas_prestamo_id.producto_interes_id.property_account_income_id.id or self.cuotas_prestamo_id.producto_interes_id.categ_id.property_account_income_categ_id.id,
            'price_unit': self.cuota_interes,
            'quantity': 1,
            'product_id': self.cuotas_prestamo_id.producto_interes_id.id or False,
            'x_user_id': self.env.user.id
            }
            lineas.append((0, 0, val_lineas))

        if self.interes_moratorio > 0:
            val_lineas1 = {
                'name': 'Interes moratorios por incumplimiento de pago',
                'account_id': self.cuotas_prestamo_id.producto_interes_id.property_account_income_id.id or self.cuotas_prestamo_id.producto_interes_id.categ_id.property_account_income_categ_id.id,
                'price_unit': self.interes_moratorio,
                'quantity': 1,
                'product_id': self.cuotas_prestamo_id.producto_interes_id.id or False,
                'x_user_id': self.env.user.id
            }
            lineas.append((0, 0, val_lineas1))
        
        company_id = self.company_id.id
        journal_id = (self.env['account.move'].with_context(company_id=company_id or self.env.user.company_id.id)
            .default_get(['journal_id'])['journal_id'])
        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        val_encabezado = {
            'name': '',
            'move_type': 'out_invoice',
            'invoice_line_ids': self.cuotas_prestamo_id.res_partner_id.property_account_receivable_id.id,
            'partner_id': self.cuotas_prestamo_id.res_partner_id.id,
            #'journal_id': journal_id,
            'currency_id': self.cuotas_prestamo_id.currency_id.id,
            'company_id': company_id,
            'user_id': self.env.user.id,
            'invoice_line_ids': lineas,
        }
        
        account_invoice_id = obj_factura.create(val_encabezado)
        
        
        capital = self.pago - (self.cuota_interes + self.gastos)
        if self.pago > 0:
            obj_paymet_id = self.env["account.payment"]
            val_payment = {
                'payment_type': 'inbound',
                'company_id': company_id,
                'partner_type': 'customer',
                'partner_id': self.cuotas_prestamo_id.res_partner_id.id,
                'amount': self.cuota_interes + capital,
                'currency_id': self.cuotas_prestamo_id.currency_id.id,
                'journal_id': self.cuotas_prestamo_id.recibir_pagos.id,
                'payment_date': self.fecha_pago,
                'communication': self.cuotas_prestamo_id.name + ' ' + self.name,
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
        self.cuotas_prestamo_id.write(vals) 
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
            saldo = self.cuota_capital + self.cuota_interes + self.interes_moratorio - self.pago
            if 0 >= saldo: 
                vals_c= {
                    'monto_restante': saldo,
                    'state': 'finalizado'
                }
            else:
                vals_c= {
                    'monto_restante': saldo
                }

            self.cuotas_prestamo_id.write(vals_c)

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


