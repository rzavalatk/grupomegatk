# -*- encoding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime
from odoo.exceptions import Warning

class WizardGenerarCuota(models.TransientModel):
	_name = 'prestamos.cuota.wizard.cheque'

	monto = fields.Float("Total del pago",  required=True)

	@api.multi
	def ingresar_pago(self):
		ctx = self._context
		obj_prestamo = self.env[ctx["active_model"]].browse(ctx['active_id'])

		if self.monto < (obj_prestamo.cuota_interes + obj_prestamo.gastos):
			raise Warning(_('El monto del pago debe de ser mayor a la cuota del interes.'))

		if self.monto > (obj_prestamo.saldo +  obj_prestamo.cuota_prestamo):
			raise Warning(_('El pago no se puede procesar porque la deuda  del prestamo es inferior.'))

		if obj_prestamo.cuotas_prestamo_id.state != 'proceso':
			raise Warning(_('El pago no se puede procesar porque el prestamo no es valido.'))
		
		obj_prestamo.pago = self.monto
		obj_prestamo.state = 'validado'
