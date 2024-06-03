# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    whatsapp_message = fields.Text(string="Plantilla de mensajes",
                                   help="plantilla de mensaje whatsapp")
