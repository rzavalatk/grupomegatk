# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ks_deal_of_the_day(models.Model):
    _name = 'ks_theme_kinetik.ks_deal_of_the_day'
    _description = 'Offer Timer'

    name = fields.Char(string='Name')
    ks_selected_product = fields.Many2one('product.pricelist', string='Product')
    ks_end_time = fields.Datetime(string='Offer End DateTime')



 # <field name="date_start"/>