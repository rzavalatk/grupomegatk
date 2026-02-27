# -*- coding: utf-8 -*-

from odoo import models, fields, api

class GastoImportacion(models.Model):
	_name="import.gasto.mega"
	_order = 'name asc'
	_description = "description"

	name = fields.Char(string="Nombre",required=True,)
	tipo_gasto = fields.Selection([('int', 'Internacional'), ('nac', 'Nacional')],string='Tipo de gasto')
	active = fields.Boolean("Activo", default=True)
	descripcion = fields.Text("Descripción")
	