# -*- encoding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime
from odoo.exceptions import Warning


class WizardGenerarCheque(models.TransientModel):
	_name = 'prestamos.afiliados.wizard.cheque'
	_description = "description"

	
	@api.onchange("currency_id")
	def onchangecurrency(self):
		if self.currency_id:
			if self.currency_id != self.company_id.currency_id:
				tasa = self.currency_id.with_context(date=self.fecha)
				self.currency_rate = 1 / tasa.rate 
				self.es_moneda_base = False
			else:
				self.currency_rate = 1
				self.es_moneda_base = True

	fecha = fields.Date("Fecha de cheque/transferencia", required=True)
	name = fields.Char("Descripción del cheque", required=True)
	company_id = fields.Many2one("res.company", "Empresa", required=True, default=lambda self: self.env.user.company_id)
	banco_id = fields.Many2one("account.journal", "Banco", required=True)
	monto = fields.Float("Total",)
	doc_type = fields.Selection([('check', 'Cheque'), ('transference', 'Transferencia'),('debit','Débito')], string='Tipo de Transacción', required=True)

	currency_id = fields.Many2one("res.currency", "Moneda", default=lambda self: self.env.user.company_id.currency_id, domain=[('active', '=', True)])
	es_moneda_base = fields.Boolean("Es moneda base")
	currency_rate = fields.Float("Tasa de Cambio", digits=(12, 6))

	@api.model_create_multi
	def generate_cheque(self):
		if self.monto <= 0:
			raise Warning(_('El monto del cheque/transferencia debe de ser mayor que cero.'))

		ctx = self._context
		obj_prestamo = self.env[ctx["active_model"]].browse(ctx['active_id'])
		if self.doc_type != 'debit':
			obj_check = self.env["banks.check"]
			lineas = []
			val_lineas = {
				'account_id': obj_prestamo.res_partner_prov_id.property_account_payable_id.id,
				'move_type': 'debit',
				'name': self.name,
				'amount': self.monto,
				'partner_id': obj_prestamo.res_partner_prov_id.id,
			}
			lineas.append((0, 0, val_lineas))
			val_encabezado = {
				'company_id': self.company_id.id,
				'journal_id': self.banco_id.id,
				'date' : self.fecha,
				'total': self.monto,
				'memo': self.name,
				'es_moneda_base': self.es_moneda_base,
				'currency_rate': self.currency_rate,
				'currency_id': self.currency_id.id,
				'doc_type': self.doc_type,
				'name': obj_prestamo.res_partner_prov_id.name,
				'check_lines': lineas,
			}
		
			id_move = obj_check.create(val_encabezado)
			id_move.action_validate()
		else:
			ctx = self._context
			obj_prestamo = self.env[ctx["active_model"]].browse(ctx['active_id'])
			obj_debit = self.env["banks.debit"]
			lineas = []
			val_lineas = {
				'account_id': obj_prestamo.res_partner_prov_id.property_account_payable_id.id,
				'move_type': 'debit',
				'name': self.name,
				'amount': self.monto,
				'partner_id': obj_prestamo.res_partner_prov_id.id,
			}
			lineas.append((0, 0, val_lineas))
			val_encabezado = {
				'company_id': self.company_id.id,
				'journal_id': self.banco_id.id,
				'date' : self.fecha,
				'total': self.monto,
				'memo': self.name,
				'es_moneda_base': self.es_moneda_base,
				'currency_rate': self.currency_rate,
				'currency_id': self.currency_id.id,
				'doc_type': self.doc_type,
				'name': obj_prestamo.res_partner_prov_id.name,
				'debit_line': lineas,
			}
			
			id_move = obj_debit.create(val_encabezado)
			id_move.action_validate()
		obj_prestamo.actualizar()

