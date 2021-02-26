# # -*- coding: utf-8 -*-
from odoo import models, fields, api



class Ks_IrUiView(models.Model):
    _inherit = "ks_product.slider"

    ks_is_full_width = fields.Boolean(string="Full Width", default=False)
    ks_template_type = fields.Selection([('t1', 'Circular'), ('t2', 'Square')],
                                        string='Template type', required='true', default='t1')
    ks_loop = fields.Boolean("Repeat Items", default=False)
    ks_is_animation = fields.Boolean(string="Animation", default=False)
    ks_items_per_slide_for_brands = fields.Selection([('4', '4'), ('5', '5'), ('6', '6')],
                                                     string='Items Per Slide for brands', required=True, default='4')
    ks_blog_template=fields.Selection([('t1', 'Design-1'), ('t2', 'Design-2')],
                                        string='Blog Template type', required='true', default='t1')
    ks_items_per_slide_for_blogs = fields.Selection([('3', '3'), ('4', '4'), ('5', '5')],
                                                     string='Items Per Slide for Blog', required=True, default='3')


class Ks_IrUiView(models.Model):
    _inherit = "ks_product.grid"

    ks_template_selection = fields.Selection([('t1', 'Template1'), ('t2', 'Template2'), ],
                                             string='Template type', required='true', default='t1')

class Ks_Alternate_Slider(models.Model):
    _inherit = 'product.template'

    ks_is_accessories_slider = fields.Boolean("Show Accessories Slider", default=False)
    ks_accessories_repeat_product = fields.Boolean("Accessories Repeat Product", default=False)
    ks_accessories_slider_speed = fields.Integer("Accessories Slider Speed")
    ka_accessories_automitic_slider = fields.Boolean("Accessories Auto Slider", default=False)
    ks_accessories_navigation = fields.Boolean("Accessories Navigation buttons", default=False)

    ks_is_alternate_slider = fields.Boolean("Show Alternate Slider", default=False)
    ks_alternate_repeat_product = fields.Boolean("Repeat Product", default=False)
    ks_alternate_slider_speed = fields.Integer("Slider Speed")
    ka_alternate_automitic_slider = fields.Boolean("Auto Slider", default=False)
    ks_alternate_navigation = fields.Boolean("Navigation buttons", default=False)
    ks_sale_count = fields.Float('Sale Count',default=0)
    ks_view_count = fields.Integer('view_count', default=0)
    ks_rating_avg = fields.Float('rating_average', default=0)
    ks_description = fields.Html('Product Description')

    @api.multi
    def _cron_saleupdate(self,auto_commit=True):
        products=self.env['product.template'].search([])
        for product in products:
            product.sudo().ks_sale_count = product.sudo().sales_count
            product.sudo().ks_rating_avg = product.sudo().rating_avg
        ks_cron_status = self.env['ks_theme_kinetik.ks_settings'].search([])
        try:
            if ks_cron_status:
                ks_cron_status.sudo().write({'cron_update':True})
        except:
            pass


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self.order_line:
            if len(order.product_id):
                order.product_id.product_tmpl_id.ks_sale_count = order.product_id.product_tmpl_id.sales_count

class Ks_Breadcumb_Image(models.Model):
    _name='ks_theme_kinetik.ks_breadcumb'
    _description = 'Breadcrumb Images'

    name=fields.Char('Name',default='Shop Breadcumb')
    breadcumb_image = fields.Binary("Breadcumb Image")
    ks_breadcumb_image_url=fields.Char('url',compute='calculate_image_url',store=True)

    @api.depends('breadcumb_image')
    def calculate_image_url(self):
        self.ks_breadcumb_image_url = "/web/image/ks_theme_kinetik.ks_breadcumb/" + str(self.id) + "/breadcumb_image"

class Ks_Kinetik_Settings(models.Model):
    _name = 'ks_theme_kinetik.ks_settings'
    _description = 'Kinetik Setting'

    name = fields.Char('Name', default='Kinetik Settings')
    cron_update=fields.Boolean('Status of Cron',default=False)
    default_order_by = fields.Selection([('ks_sale_count desc', 'Highest Sale'), ('ks_view_count desc', 'Most Popular'),
                                         ('ks_rating_avg desc', 'Highest Rating'), ('create_date desc', 'Newest Arrivals'),
                                         ('name asc', 'Name A-Z'), ('name desc', 'Name Z-A')], string='Default Sort By')


