# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountMove(models.Model):
    """Esta clase amplía la funcionalidad del modelo 'account.move' para
    incluir una referencia a un ticket de ayuda a través del campo 'ticket_id'."""
    _inherit = 'account.move'

    ticket_id = fields.Many2one('help.ticket', string='Ticket',
                                help='Elija el ticket de ayuda',)
