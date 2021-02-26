# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ks_product_grid(models.Model):
    _name = "ks_product.grid"
    _description = 'This is used for product slider'

    name = fields.Char(required='true', translate=True)
    ks_product_template_grid = fields.Many2many("product.template", string="Products")
