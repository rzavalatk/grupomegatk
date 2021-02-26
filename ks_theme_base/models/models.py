# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ks_product_manager(models.Model):
    _inherit = 'product.template'

    """
    This model is used to place a option to select brand for product 
        at the time of creation of product
    """

    ks_discounted_price = fields.Float(string='Offer Price', compute='_calculate_offer_price')
    ks_product_brand_id = fields.Many2one(
        'ks_product_manager.ks_brand',
        string='Brand', group_expand='_read_group_stage_ids'
    )
    ks_product_tags = fields.Many2many("ks_theme.tags", 'products_track_tags_rel',
                                       'product_template_id', 'ks_theme_tags_id',
                                       string='Featured Tags')

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = stages.sudo()._search([], order=order)
        return self.env['ks_product_manager.ks_brand'].browse(stage_ids)

    @api.multi
    def _calculate_offer_price(self):
        for rec in self:
            if rec.ks_product_brand_id:
                ks_disc = rec.ks_product_brand_id.ks_brand_discount
                discount = rec.list_price * ks_disc / 100
                disc_price = rec.list_price - discount
                rec.ks_discounted_price = disc_price


class ks_brand(models.Model):
    _name = 'ks_product_manager.ks_brand'
    _description = 'Ks Model'

    """This model is create brand and their info"""

    name = fields.Char(string='Brand Name',required='true')
    ks_image = fields.Binary(string='Image')
    ks_product_ids = fields.One2many('product.template', 'ks_product_brand_id', widget='binary')
    ks_products_count = fields.Integer(string='Number of products', compute='ks_get_products_count')
    ks_brand_discount = fields.Integer(string='Discount Percentage')
    ks_brand_logo = fields.Binary(string='Brand Logo', widget='binary')
    ks_brand_url = fields.Char(invisible=True)
    ks_is_checked_on_shop = fields.Boolean(default=False)
    ks_is_published = fields.Boolean(default=False, string="Published")
    ks_brand_description=fields.Char(string='Description')
    @api.multi
    @api.depends('ks_product_ids')
    def ks_get_products_count(self):
        """This method is used to count no. of product under a brand"""

        for brand in self:
            brand.ks_products_count = len(brand.ks_product_ids)

    @api.multi
    def ks_get_brand_url(self, name):
        for rec in self:
            base_url = rec.env['ir.config_parameter'].sudo().get_param('web.base.url')
            if rec.name:
                return 'shop?filter=' + str(name)
            else:
                return ""


class ks_Tags(models.Model):
    _name = "ks_theme.tags"
    _description = 'Ks Model'

    name = fields.Char()
    ks_state = fields.Boolean(default=True)
    brand_name = fields.Many2many('product.template', relation='ks_products_track_tags_rel',
                                  string='Available Products Tags')


class ks_products_track_tags_rel(models.Model):
    _name = "ks_products_track_tags_rel"
    _description = 'Ks Model'

    name = fields.Char()
    ks_source = fields.Char()


class ks_trending_style(models.Model):
    _inherit = 'product.public.category'

    ks_product_category_slogan = fields.Char(string='Slogan')
    ks_categ_tag = fields.Boolean(string='Trendy')
    child_id = fields.One2many('product.public.category', 'parent_id', string='Child Category')
    category_url = fields.Char(help="So each category can have their urls")
    ks_categ_background = fields.Binary(string='Breadcrumb Image', widget='binary')
