# -*- coding: utf-8 -*-

from odoo import models, api, fields


class ModelCompras(models.Model):
    _inherit = 'purchase.order'


    cubing = fields.Float("Cubicaje total")
    weight = fields.Float("Peso total")
    code_reference = fields.Char("Código de Referencia")
    origin_city = fields.Char("Ciudad de origen")