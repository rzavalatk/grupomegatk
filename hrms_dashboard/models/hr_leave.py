# -*- coding: utf-8 -*-
from odoo import fields, models


class HrLeave(models.Model):
    """Extiende hr.leave para mostrar duración de ausencia.
    
    Añade un campo computado que muestra la duración de la solicitud
    de ausencia en formato legible (días u horas según configuración).
    """
    _inherit = 'hr.leave'

    duration_display = fields.Char(
        string='Solicitado (Días/Horas)', compute='_compute_duration_display',
        store=True, help="Campo que muestra la duración de la solicitud "
                         "de ausencia en días u horas dependiendo de la "
                         "configuración del tipo de ausencia")
