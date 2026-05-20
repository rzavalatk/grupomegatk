# -*- coding: utf-8 -*-
from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    x_is_technical_area = fields.Boolean(
        related="team_id.x_is_technical_area",
        store=True,
        readonly=True,
    )
    x_tecnico_diagnostico = fields.Text(string="Diagnostico tecnico")
    x_tecnico_solucion = fields.Text(string="Solucion aplicada")
