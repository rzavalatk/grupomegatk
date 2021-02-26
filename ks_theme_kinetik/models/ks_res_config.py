# Copyright 2016 Tecnativa - Antonio Espinosa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class KsWebsiteConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ks_logo = fields.Binary(related='website_id.logo', readonly=False)

# class Sale_order(models.Model):
#     _inherit = 'sale.order.line'
#
#     def get_sale_order_line_multiline_description_sale(self, product):
#         description = product.get_product_multiline_description_sale() + "\nks_description_end"
#         return description + self._get_sale_order_line_multiline_description_variants()
