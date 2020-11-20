# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import Warning

class ProductPonderacion(models.Model):
	_name = 'product.ponderacion'
	_order = "fecha_recepcion desc"

	product_id = fields.Many2one("product.template", "Producto", required=True)
	fecha_recepcion = fields.Datetime(string='Ingreso')
	ponderacion = fields.Float(string='Ponderacion %',)
	costo_real = fields.Float(string='Consto Honduras')
	ponderacion_id = fields.Many2one('import.product.mega', 'Nombre')


class ClassName(models.Model):
	_inherit = 'product.template'

	x_ponderaciones = fields.One2many('product.ponderacion', 'product_id')
