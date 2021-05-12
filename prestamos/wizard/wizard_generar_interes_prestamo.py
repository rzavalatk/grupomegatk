# -*- encoding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime
from odoo.exceptions import Warning


class WizardGenerarfacturainteres(models.TransientModel):
	_name = 'prestamos.personal.wizard.interes'

	pago = fields.Float(string='Pago',)
	interes = fields.Float(string='Interes',)
	fecha_pago = fields.Date(string='Fecha',copy=False, required=True)

	def factu_interes(self):
		if self.pago > 0 or self.interes > 0:
			obj_factura = self.env["account.invoice"]
			ctx = self._context
			obj_prestamo = self.env[ctx["active_model"]].browse(ctx['active_id'])
			lineas = []
			producto_interes_id = ''
			company_id = obj_prestamo.company_id.id

			if self.interes > 0:
				val_lineas = {
				'name': 'Cobro de interes',
				'account_id': obj_prestamo.producto_interes_id.property_account_income_id.id or obj_prestamo.producto_interes_id.categ_id.property_account_income_categ_id.id,
				'price_unit': self.interes,
				'quantity': 1,
				'product_id': obj_prestamo.producto_interes_id.id or False,
				'x_user_id': obj_prestamo.env.user.id
				}
				lineas.append((0, 0, val_lineas))

				journal_id = (self.env['account.invoice'].with_context(company_id=company_id)
					.default_get(['journal_id'])['journal_id'])
				if not journal_id:
					raise UserError(_('Please define an accounting sales journal for this company.'))

				val_encabezado = {
					'name': '',
					'type': 'out_invoice',
					'account_id': obj_prestamo.res_partner_id.property_account_receivable_id.id,
					'partner_id': obj_prestamo.res_partner_id.id,
					'journal_id': journal_id,
					'currency_id': obj_prestamo.currency_id.id,
					'company_id': company_id,
					'user_id': obj_prestamo.env.user.id,
					'invoice_line_ids': lineas,
				}
				account_invoice_id = obj_factura.create(val_encabezado)
				obj_prestamo.invoice_cxc_ids = [(4, account_invoice_id.id, 0)]
				
			if self.pago > 0:
				obj_paymet_id = self.env["account.payment"]
				val_payment = {
					'payment_type': 'inbound',
					'company_id': company_id,
					'partner_type': 'customer',
					'partner_id': obj_prestamo.res_partner_id.id,
					'amount': self.pago,
					'currency_id': obj_prestamo.currency_id.id,
					'journal_id': obj_prestamo.recibir_pagos.id,
					'payment_date': self.fecha_pago,
					'communication': obj_prestamo.name,
					'payment_method_id': 1
				}
				paymet_id = obj_paymet_id.create(val_payment)
				paymet_id.post()
				obj_prestamo.payment_ids = [(4, paymet_id.id, 0)]

			if obj_prestamo.monto_restante > 0 :
				if self.pago - self.interes < 0:
					obj_prestamo.monto_restante = obj_prestamo.monto_restante - (self.pago - self.interes)
			obj_prestamo.interes_generado = (obj_prestamo.monto_restante * obj_prestamo.tasa)/100
		else:
			raise UserError(_('El pago y El interes no pueden ser cero.'))

