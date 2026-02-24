# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    """Extensión del modelo de Empleado para incluir información de renuncias.
    
    Agrega campos adicionales al modelo 'hr.employee' para rastrear la fecha
    de renuncia y el tipo de salida del empleado (renuncia voluntaria o despido).
    """
    _inherit = 'hr.employee'

    # ===== CAMPOS ADICIONALES =====
    
    resign_date = fields.Date(
        string='Fecha de Renuncia', readonly=True,
        help="Fecha en que el empleado renunció o fue despedido")
    resigned = fields.Boolean(
        string="Renunció", default=False,
        help="Marcar si el empleado renunció voluntariamente")
    fired = fields.Boolean(
        string="Despedido", default=False,
        help="Marcar si el empleado fue despedido por la empresa")
