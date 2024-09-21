# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Add new fields to display service products"""
    _inherit = 'res.config.settings'

    interest_product_id = fields.Many2one('product.product',
                                          string="Interest Product",
                                          config_parameter="prestamos_financieros"
                                                           ".interest_"
                                                           "product_id",
                                          help="Product For Interest "
                                               "To Create Invoice Lines")
    repayment_product_id = fields.Many2one('product.product',
                                           string="Repayment Product",
                                           config_parameter="prestamos_financieros"
                                                            ".repayment_"
                                                            "product_id",
                                           help="Product For Repayment "
                                                "To Create Invoice Lines")
