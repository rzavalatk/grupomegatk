# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.addons import decimal_precision as dp
import math

class Afiliados(models.Model):
	_name = 'prestamos.afiliados'
	_description = "Prestamos Afiliados"
	_order = "name desc"
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

	name = fields.Char('Numero', copy=False)
	payment_type = fields.Selection([('debit', 'Debito'), ('credit', 'Credito')], string='Transacción', required=True)
	res_partner_prov_id = fields.Many2one('res.partner', string='Afiliado', domain=[('supplier','=',True), ],)
	active = fields.Boolean(string='Activo', default=True)

	
