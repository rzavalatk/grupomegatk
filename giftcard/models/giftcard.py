# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import random

class GiftCard(models.Model):
	_name = 'giftcard'
	_description = 'Creación y validacion de Gift Card'
	_order = "fechaval desc"

	def _get_invoiced(self):
		w = len(set(self.giftcard_detalle.ids))
		self.detalle = w

	@api.onchange("account_id")
	def onchangemoneda(self):
		if self.account_id:
			if self.account_id.currency_id:
				self.currency_id = self.account_id.currency_id.id
			else:
				if self.company_id:
					self.currency_id = self.company_id.currency_id.id
	
	def _codigo(self):
		cod = datetime.now()
		codigo = str(cod.day) + str(cod.month) + str(cod.year) + str(cod.hour) + str(cod.minute) + str(cod.second) + str(random.randrange(0, 9))
		return  codigo

	@api.model_create_multi
	def create(self, values_list):
		for vals in values_list:
			if vals.get('giftcard_number', ('50000')) == ('50000'):
				vals['giftcard_number'] = self.env['ir.sequence'].next_by_code('giftcard.number')
		return super().create(values_list)

	
	def get_fecha(self):
		self.fecha_actual = datetime.now()
		
	name = fields.Char('Número', copy=False,)
	fechaval = fields.Datetime('Fecha validación', copy=False, readonly=True, states={'draft': [('readonly', False)]},)
	saldo = fields.Float('Saldo:', copy=False,)
	giftcard_number = fields.Char(string="Numero de giftcard", default="50000", copy=False, required=True, readonly=True)
	pago = fields.Float('pago', copy=False,)
	partner_id = fields.Many2one('res.partner', string='Cliente', domain=[('x_customer','=', True)], copy=False,)
	currency_id = fields.Many2one("res.currency", "Moneda", track_visibility='onchange', copy=False,)
	state = fields.Selection( [('draft', 'Borrador'), ('cancelado', 'Cancelado'),('validado', 'Validado'),('finalizado', 'Finalizado')], string="Estado", default='draft',copy=False, track_visibility='onchange',)
	company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, default=lambda self: self.env.user.company_id,readonly=True, states={'draft': [('readonly', False)]},)
	giftcard_detalle = fields.One2many("giftcard.detalle", "gifcard_id", "Movimientos", copy=False,)
	detalle = fields.Integer(string='Detalle', compute='_get_invoiced', readonly=True)
	fecha_actual = fields.Datetime('Fecha actual',compute = 'get_fecha',)

	
	def validar(self):
		self.write({'state': 'validado'})

	def cancelar(self):
		self.write({'state': 'cancelado'})

	def back_draft(self):
		self.write({'state': 'draft'})


class GiftCardDetalle(models.Model):
	_name = 'giftcard.detalle'
	_description = 'detalle de transacción'
	_order = "date desc"
	
	gifcard_id = fields.Many2one('giftcard', 'Giftcard')
	partner_id = fields.Many2one(related='gifcard_id.partner_id', string="Cliente")
	date = fields.Datetime("Fecha")
	descripcion = fields.Char('Descripción', )
	monto = fields.Float('Monto')


