# # -*- coding: utf-8 -*-
from odoo import models, fields, api


class Ks_WebsiteMegaMenu(models.Model):
    _inherit = "website.menu"
    _description = "This model will add mega menu option to the website menu"

    ks_is_mega_menu = fields.Boolean("Is Mega Menu")
    ks_display_img = fields.Boolean("Display Category Images")
    ks_content_id = fields.Char("Content")
    ks_current_categories = fields.Many2many("product.public.category", 'rel_menu_category', 'menu_ks_id', 'ecom_cat_id', string="Categories to displayed", compute='change_website_data')
    ks_categories = fields.Many2many("product.public.category", string="Categories to display")
    ks_banner_img = fields.Binary("Banner Image")
    ks_is_background_image = fields.Boolean("Set Background Image")
    ks_background_image = fields.Binary("Background Image")

    ks_item_selection_method = fields.Selection(
        [('products', 'All Products'), ('brands', 'Brands'), ('Cats', 'Categories')],
        string='Item Selection Type', default='products')

    ks_products_ids = fields.Many2many("product.template", string="Products",domain=[('website_published','=',True)])
    ks_product_brand_ids = fields.Many2many('ks_product_manager.ks_brand', string='Brands')
    ks_is_category_tab_layout = fields.Boolean(string='Set Tab Layout For Categories')
    ks_show_sub_categories = fields.Boolean(string='Display Sub Categories', default=True)

    # Slider Configuration
    ks_is_slider = fields.Selection(
        [('image', 'Image'), ('slider', 'Slider')],
        string='Show Image/Slider')

    ks_item_slider_selection_method = fields.Selection(
        [('products', 'All Products'), ('brands', 'Brands'), ('cats', 'Categories')],
        string='Selection Type', default='products')

    ks_slider_title = fields.Char("Title")
    ks_slider_position = fields.Selection(
        [('left', 'Left'), ('right', 'Right')],
        string='Position', default='left')
    ks_slider_Speed = fields.Integer("Slide Speed", default=300)
    ks_slider_products_ids = fields.Many2many("product.template", string="Products Slider",domain=[('website_published','=',True)])
    ks_slider_product_brand_ids = fields.Many2many('ks_product_manager.ks_brand', string='Brands Slider')
    ks_slider_categories = fields.Many2many("product.public.category", string="Categories")
    ks_side_image = fields.Binary("Image")
    ks_side_image_description = fields.Char("Short Description")
    ks_side_image_link = fields.Char("Link")
    # Advance Configuration
    ks_is_font_color_set = fields.Boolean("Set Font Color")
    ks_font_color_main_cat = fields.Char(default="#000000", string="Main Heading Color")
    ks_font_color_sub_cat = fields.Char(default="#000000", string="Sub Heading Color")
    ks_set_number_of_columns = fields.Selection([('two', '2'), ('three', '3'), ('four', '4'), ('five', '5'), ('six  ', '6')],
        string='Set Number of Column', default='four', required=True)

    # ToDo Remove this field when create a new database
    ks_font_color = fields.Char()
    ks_is_categories_slider = fields.Char()

    @api.depends('website_id')
    def change_website_data(self):
        for rec in self:
            if rec.id:
                current_web_category = self.env['product.public.category'].search(
                    ['|', ('website_id', '=', rec.website_id.id), ('website_id', '=', False)])
                rec.ks_current_categories = [(6, 0, current_web_category.ids)]
            if not rec.id:
                current_web_category = self.env['product.public.category'].search(
                    ['|', ('website_id', '=', rec.website_id.id), ('website_id', '=', False)])
                rec.ks_current_categories = [(6, 0, current_web_category.ids)]
                test = rec.ks_categories.filtered(lambda c: c.id in current_web_category.ids)
                rec.ks_categories = [(6, 0, test.ids)]
            if not rec.website_id:
                all_category = self.env['product.public.category'].search([])
                rec.ks_current_categories = [(6, 0, all_category.ids)]

    @api.multi
    def ks_get_image_url(self):
        for rec in self:
            if rec.ks_is_background_image and rec.ks_background_image:
                return '/web/image/website.menu/' + str(rec.id) + '/ks_background_image/330x330'

            else:
                return ""
    @api.multi
    def ks_get_side_image_url(self):
        for rec in self:
            if rec.ks_side_image and rec.ks_side_image:
                return '/web/image/website.menu/' + str(rec.id) + '/ks_side_image/330x330'

            else:
                return ""

    @api.multi
    def get_current_website(self):
        for rec in self:
            return rec.website.id
        else:
            return ""


class ks_website_logo(models.Model):
    _inherit = 'website'

    logo = fields.Binary(string="Website logo")

#     @api.model
#     def copy_menu_hierarchy(self, top_menu):
#         print("dfshhs")
#         print("Fdfdsf")
#         pass
#         c = super(ks_website_top_menu, self).copy_menu_hierarchy(top_menu)
#         print("dfshhs")
#         # def copy_menu(menu, t_menu):
#         #     new_menu = menu.copy({
#         #         'parent_id': t_menu.id,
#         #         'website_id': self.id,
#         #     })
#         #     for submenu in menu.child_id:
#         #         copy_menu(submenu, new_menu)
#         #
#         # for website in self:
#         #     new_top_menu = top_menu.copy({
#         #         'name': _('Top Menu for Website %s') % website.id,
#         #         'website_id': website.id,
#         #     })
#         #     li = self.env.ref()
#         #     for submenu in top_menu.child_id:
#         #         copy_menu(submenu, new_top_menu)
#
#     @api.multi
#     def write(self, values):
#         a = super(ks_website_top_menu, self).write(values)
#         return a
