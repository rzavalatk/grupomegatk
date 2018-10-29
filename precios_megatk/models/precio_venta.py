# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class Precioproducto(models.Model):
    _name = "lista.precios.producto"
    _order = 'name asc'

    name = fields.Many2one("lista.precios.tipo.descuento", "Margen", required=True, ondelete='cascade')
    product_id = fields.Many2one("product.product", "Producto", required=True)
    lista_id = fields.Many2one("lista.precios.megatk", "Lista de precios", ondelete='cascade')
    descuento = fields.Float("Margen")
    precio = fields.Float("Precio")
