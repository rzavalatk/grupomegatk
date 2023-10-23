# -*- encoding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime
from odoo.exceptions import Warning


class WizardGenerarDeposito(models.TransientModel):
	_name = 'prestamos.afiliados.wizard.deposito'

	def _get_moneda(self):
		ctx = self._context
		obj_prestamo = self.env[ctx["active_model"]].browse(ctx['active_id'])
		return obj_prestamo.currency_id.id

	monto = fields.Float(string='Monto', required=True,)
	pagos = fields.Many2one("account.account", "Recibir depósito", required=True, domain="[ ('user_type_id.type', '=', 'liquidity')]")
	description = fields.Char('Descripción', required=True,)
	fecha = fields.Date(string='Fecha', required=True,)
	fechavence = fields.Date(string='Vence', required=True,)
	currency_id = fields.Many2one('res.currency', 'Moneda', default=_get_moneda,)

	@api.multi
	def deposito(self):
		if self.monto > 0:
			self.crear_factura_cxp()
		else:
			raise Warning(_('El monto debe ser mayor que cero.'))

	def crear_factura_cxp(self):
		obj_factura = self.env["account.invoice"]
		ctx = self._context
		obj_prestamo = self.env[ctx["active_model"]].browse(ctx['active_id'])

		lineas = []
		val_lineas = {
			'name': self.description,
			'account_id': self.pagos.id,
			'price_unit': self.monto,
			'quantity': 1,
			'product_id': False,
		}
		lineas.append((0, 0, val_lineas))
		company_id = obj_prestamo.company_id.id
		val_encabezado = {
			'name': '',
			'type': 'in_invoice',
			'date_invoice': self.fecha,
			'date_due': self.fechavence,
			'account_id': obj_prestamo.res_partner_prov_id.property_account_payable_id.id,
			'partner_id': obj_prestamo.res_partner_prov_id.id,
			'currency_id': self.currency_id.id or obj_prestamo.currency_id.id,
			'company_id': company_id,
			'user_id': obj_prestamo.user_id.id,
			'invoice_line_ids': lineas,
		}

		account_invoice_id = obj_factura.create(val_encabezado)
		account_invoice_id.action_invoice_open()
		obj_prestamo.actualizar()
		obj_prestamo.invoice_cxc_ids = [(4,account_invoice_id.id,0)]
		obj_prestamo.saldo_inicial = self.monto
		obj_prestamo.state = 'validado'
