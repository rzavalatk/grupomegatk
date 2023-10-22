# -*- encoding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, exceptions, _
from datetime import datetime
from odoo.exceptions import Warning


class WizardGiftCardRecar(models.TransientModel):
	_name = 'gifrcard.wizard.recar'
	_description = "description"

	monto = fields.Float("Monto", required=True,)
	descripcion = fields.Char('Descripción', required=True, default='Recarga')

	def aceptar(self):
		if self.monto > 0:
			ctx = self._context
			obj_giftcard = self.env[ctx["active_model"]].browse(ctx['active_id'])
			obj_giftcard.state = 'validado'

			valores = {
				'gifcard_id': obj_giftcard.id,
				'date': datetime.now(),
				'descripcion': self.descripcion, 
				'monto': self.monto,
			}

			obj_giftcard.giftcard_detalle.create(valores)
			if not obj_giftcard.fechaval:
				obj_giftcard.fechaval = datetime.now() 
			obj_giftcard.saldo = obj_giftcard.saldo + self.monto
			obj_giftcard.pago = self.monto
		elif self.monto < 0:
			raise Warning(_('Monto debe ser mayor que cero.'))
