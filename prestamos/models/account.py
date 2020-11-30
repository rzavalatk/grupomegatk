# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError

class Account(models.Model):
	_inherit = 'account.account'

	desembolso = fields.Boolean(string='Desembolso',)
	redescuento = fields.Boolean(string='Redescuento',)