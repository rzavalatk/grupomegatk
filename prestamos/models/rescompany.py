# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class ResCompany(models.Model):
	_inherit = "res.company"

	account_id = fields.Many2one('account.account', 'Cuenta de desembolso',  )
	account_redes_id = fields.Many2one('account.account', 'Cuenta de redescuento',  )
	recibir_pagos = fields.Many2one("account.journal", "Recibir pagos", )
	producto_gasto_id = fields.Many2one('product.product', string='Cuenta de gasto', )
	producto_interes_id = fields.Many2one('product.product', string='Cuenta de interes', )
	interes_id = fields.Many2one("account.account", "Recibir depósito", )
