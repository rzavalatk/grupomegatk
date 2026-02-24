# -*- encoding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime
from odoo.exceptions import UserError

class WizardGenerarCuota(models.TransientModel):
	_name = 'prestamos.cuota.wizard.cheque'
	_description = "Generar cuotas de prestamos"

	monto = fields.Float("Total del pago",  required=True)
	fecha_pagado = fields.Date(string='Fecha de pago',copy=False,required=True)
	moratorio = fields.Boolean(string='Cobrar mora',default=True)

	@api.model
	def ingresar_pago(self, monto):
		ctx = self._context
		obj_prestamo = self.env[ctx["active_model"]].browse(ctx['active_id'])

		if self.monto > (obj_prestamo.saldo +  obj_prestamo.cuota_prestamo):
			raise UserError(_('El pago no se puede procesar porque la deuda  del prestamo es inferior.'))

		if obj_prestamo.cuotas_prestamo_id.state != 'proceso':
			raise UserError(_('El pago no se puede procesar porque el prestamo no es valido.'))
		
		obj_prestamo.pago = self.monto if self.monto > 0 else 0
		obj_prestamo.state = 'validado'
		obj_prestamo.interes_generado = (obj_prestamo.cuota_capital * (2/100)) if (self.moratorio and self.fecha_pagado > obj_prestamo.fecha_pago) or self.monto == 0 else 0
		obj_prestamo.fecha_pagado = self.fecha_pagado
