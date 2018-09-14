# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class StockPicking(models.Model):
	_inherit = "stock.picking"
	
	ponderacion = fields.Boolean("Ponderación calculada")

	

	
	