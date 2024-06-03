# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
    Amplía el modelo 'res.config.settings' para incluir opciones de configuración adicionales.
    """
    _inherit = 'res.config.settings'

    whatsapp_message = fields.Text(string="Plantilla de mensajes",
                                   related='company_id.whatsapp_message',
                                   readonly=False)
