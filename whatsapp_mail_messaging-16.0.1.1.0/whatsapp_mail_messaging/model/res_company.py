# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    """
    Extends the 'res.company' model to include WhatsApp message template.
    """
    _inherit = 'res.company'

    whatsapp_message = fields.Text(string="Message Template",
                                   help="whatsapp message template")
