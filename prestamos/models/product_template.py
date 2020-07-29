# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Product(models.Model):
    _inherit = "product.template"

    gasto = fields.Boolean(string='Gasto',)
    interes = fields.Boolean(string='Interes',)