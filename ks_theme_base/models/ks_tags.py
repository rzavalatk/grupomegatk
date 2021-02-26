# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ks_Tags(models.Model):
    """
        - Tags for the products and categories
        - Each product can be assigend a tag on the bussiness logic or manually by the user
    """
    _name = "ks_theme.tags"
    _description = "Tags for the products and categories"
    name = fields.Char(required=True, translate=True)
    ks_state = fields.Boolean(default=True)
    ks_product_ids = fields.Many2many('product.template', 'products_track_tags_rel',
                                      'ks_theme_tags_id', 'product_template_id',
                                      string='Products Tags')


class ks_products_track_tags_rel(models.Model):
    """
           - Maintaing this table to access the assignments of the tags
       """
    _name = "ks_products_track_tags_rel"
    _description = "Relation of products and tags"
    name = fields.Char()
    ks_source = fields.Char()
