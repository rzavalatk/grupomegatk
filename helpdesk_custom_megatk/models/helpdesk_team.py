# -*- coding: utf-8 -*-
from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    x_is_technical_area = fields.Boolean(
        string="Area de Soporte Tecnico",
        help="Si esta activo, los tickets de este equipo mostraran campos tecnicos.",
    )
