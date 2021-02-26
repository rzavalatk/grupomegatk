# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ks_product_slider(models.Model):
    _name = 'ks_product.multitab_slider'
    _description = 'This is used for product slider snippet'

    name = fields.Char(required=True, translate=True)
    ks_product_template_slider = fields.Many2many("product.template", string="Items")
    ks_loop = fields.Boolean("Repeat Products", default=False)
    ks_auto_slide = fields.Boolean("Automatic Slide", default=True)
    ks_Speed = fields.Integer("Slide Speed", default=300)
    ks_item_selection_method = fields.Selection(
        [('products', 'Products')],
        string='Slider Type', required=True, default='products')
    ks_nav_links = fields.Boolean("Navigation Buttons", default=True)
    ks_product_brand_ids = fields.Many2many('ks_product_manager.ks_brand', string='Brand')
    ks_product_cat_ids = fields.Many2many('product.public.category', string='Category')
    ks_product_blogs_ids = fields.Many2many('blog.post', string='Blogs')
    ks_items_per_slide = fields.Selection([('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
                                          string='Items Per Slide', required=True, default='4')
    tabs_line_ids_line = fields.One2many('ks_product.slider_line', 'tabs_line_ids_tabs', 'Product Attributes')


class ks_product_slider_multitab(models.Model):
    _name = 'ks_product.slider_tabs'
    _description = 'This is used for manage tabs for a product slider snippet'
    name = fields.Char(required=True, translate=True)


class ks_product_slider_line(models.Model):
    _name = 'ks_product.slider_line'
    _description = 'This is used for manage tabs for a product slider snippet'
    name = fields.Char()
    ks_product_template_sliders = fields.Many2many("product.template", string="Products")
    tabs_line_ids = fields.Many2one('ks_product.slider_tabs', 'Tab Name')
    tabs_line_ids_tabs = fields.Many2one('ks_product.multitab_slider', string='Product Attributes')

