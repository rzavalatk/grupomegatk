# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PriceWebsite(models.Model):
    _inherit = 'product.template'


    select_website_price = fields.Integer("Seleccionar Precio mostrado en Sitio web",default=2)