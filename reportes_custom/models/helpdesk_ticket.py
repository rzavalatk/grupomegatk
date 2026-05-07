# -*- coding: utf-8 -*-

from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Backward-compatible field for custom views that still read record.color.
    color = fields.Integer(string='Color', default=0)
