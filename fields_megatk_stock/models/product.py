# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Product(models.Model):
    _inherit = "product.template"

    @api.onchange('x_comisiones.obj_padre')
    def _onchange_xcomision(self):
        print("/////////////////////////////////////////////////////")

