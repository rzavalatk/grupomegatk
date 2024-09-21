from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    replace_standard_wizard = fields.Boolean(config_parameter='barcode_product_label.replace_standard_wizard')
