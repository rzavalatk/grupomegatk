# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class StockPicking(models.Model):
	_inherit = "stock.picking"
	
	ponderacion = fields.Boolean("Ponderación calculada")



class StockMove(models.Model):
	_inherit = "stock.move"
	
	tax_id = fields.Many2many('account.tax', related='purchase_line_id.taxes_id')
	