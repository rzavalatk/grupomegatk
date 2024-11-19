# -*- coding: utf-8 -*-

from odoo import fields, models


class MessageWizard(models.TransientModel):
    """Para crear mensajes de alerta"""
    _name = 'message.popup'
    _description = 'Generate Popup Message'

    message = fields.Text(string='Message', required=True, help="Alert Content")
