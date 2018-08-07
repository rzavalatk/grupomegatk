# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class TipoDescuento(models.Model):
    _name = "lista.precios.tipo.descuento"

    name = fields.Char('Margen',  required=True)
    company_id = fields.Many2one('res.company', "Empresa", default=lambda self: self.env.user.company_id, required=True)
    active = fields.Boolean("Activo", default=True)
    descuento = fields.Float("Margen %")
    precio = fields.Float("Precio")