# -*- coding: utf-8 -*-

from odoo import models, fields, api

class GastoImportacion(models.Model):
	_name="import.gasto.mega"

	name = fields.Char(string="Name")
	active = fields.Boolean("Is active")
	descripcion = fields.Text("Descripción")
	tipo = fields.Selection([("costo","Costo"),("gasto","Gasto")], string="Tipo")
	