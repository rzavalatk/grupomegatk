# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ks_product_slider(models.Model):
    _name = 'ks_product.slider'
    _description = 'This is used for product slider snippet'

    name = fields.Char(required=True, translate=True)
    ks_product_template_slider = fields.Many2many("product.template", string="Products")
    ks_loop = fields.Boolean("Repeat Products", default=False)
    ks_auto_slide = fields.Boolean("Automatic Slide", default=True)
    ks_Speed = fields.Integer("Slide Speed", default=300)
    ks_item_selection_method = fields.Selection(
        [('products', 'Products'), ('brands', 'Brands'), ('Cats', 'Categories'),('blogs', 'Blogs')],
        string='Slider Type', required=True, default='products')
    ks_nav_links = fields.Boolean("Navigation Buttons", default=True)
    ks_product_brand_ids = fields.Many2many('ks_product_manager.ks_brand', string='Brand')
    ks_product_cat_ids = fields.Many2many('product.public.category', string='Category')
    ks_product_blogs_ids = fields.Many2many('blog.post', string='Blogs')
    ks_items_per_slide = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')],
                                          string='Items Per Slide', required=True, default='4')


