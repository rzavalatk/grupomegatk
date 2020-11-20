# -*- encoding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime
from odoo.exceptions import Warning

class WizardGenerarCuota(models.TransientModel):
	_name = 'prestamos.cuota.wizard.cheque'

	monto = fields.Float("Total del pago",  required=True)
	pago_interes = fields.Boolean(string='Crear pago',default=True)
	fecha_pagado = fields.Date(string='Fecha de pago',copy=False,required=True)
	moratorio = fields.Boolean(string='Cobrar mora',default=True)

	@api.multi
	def ingresar_pago(self):
		ctx = self._context
		obj_prestamo = self.env[ctx["active_model"]].browse(ctx['active_id'])

		if self.monto < (obj_prestamo.cuota_interes + obj_prestamo.gastos) and self.pago_interes:
			raise Warning(_('El monto del pago debe de ser mayor a la cuota del interes.'))

		if self.monto > (obj_prestamo.saldo +  obj_prestamo.cuota_prestamo):
			raise Warning(_('El pago no se puede procesar porque la deuda  del prestamo es inferior.'))

		if obj_prestamo.cuotas_prestamo_id.state != 'proceso':
			raise Warning(_('El pago no se puede procesar porque el prestamo no es valido.'))
		
		obj_prestamo.pago = self.monto if self.pago_interes else 0
		obj_prestamo.state = 'validado'
		obj_prestamo.pago_interes = self.pago_interes
		obj_prestamo.interes_moratorio = (obj_prestamo.cuota_capital * (2/100)) if self.moratorio and self.fecha_pagado > obj_prestamo.fecha_pago else 0
		obj_prestamo.fecha_pagado = self.fecha_pagado
		if not self.pago_interes:
			obj_prestamo.monto_atrasado_actual = obj_prestamo.cuota_prestamo - obj_prestamo.cuota_interes
		elif self.monto < obj_prestamo.cuota_prestamo:
			obj_prestamo.monto_atrasado_actual = obj_prestamo.cuota_prestamo - self.monto
