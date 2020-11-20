# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class TipoDescuento(models.Model):
    _name = "lista.precios.tipo.descuento"
    _order = 'name asc'

    name = fields.Char('Margen',  required=True)
    active = fields.Boolean("Activo", default=True)
    descuento = fields.Float("Margen %")
    precio = fields.Float("Precio")
    tipo_precio = fields.Selection([('a','A'),('m','M')], string='Precio')