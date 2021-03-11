# -*- encoding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime
from odoo.exceptions import Warning


class WizardGiftCardCobrar(models.TransientModel):
	_name = 'gifrcard.wizard.cobrar'

	monto = fields.Float("Monto", required=True,)
	descripcion = fields.Char('Descripción', required=True,)

	def aceptar(self):
		ctx = self._context
		obj_giftcard = self.env[ctx["active_model"]].browse(ctx['active_id'])
		if self.monto > 0 and obj_giftcard.saldo >= self.monto:
			valores = {
				'gifcard_id': obj_giftcard.id,
				'date': datetime.now(),
				'descripcion': self.descripcion, 
				'monto': self.monto * (-1),
			}

			obj_giftcard.giftcard_detalle.create(valores)
			obj_giftcard.saldo = obj_giftcard.saldo - self.monto
		elif self.monto < 0:
			raise Warning(_('Monto debe ser mayor que cero.'))
		elif obj_giftcard.saldo < self.monto:
			raise Warning(_('Monto debe ser menor o igual al saldo de la tarjeta.'))

