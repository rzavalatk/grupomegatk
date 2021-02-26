# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ks_main_slider(models.Model):
    _name = 'ks_product_main.slider'
    _order = 'sequence'
    _description = 'Website Main Slider'

    name = fields.Char(required='true')
    ks_main_slider_img = fields.Binary("Banner Image")
    ks_main_slider_link = fields.Char("Banner Link")
    ks_main_slider_animate_in = fields.Selection([('fadeInUp', 'fadeInUp')], default="fadeInUp")
    ks_main_slider_animate_out = fields.Selection([('fadeOutUp', 'fadeOutUp')], default="fadeOutUp")
    sequence = fields.Integer('Sequence')
