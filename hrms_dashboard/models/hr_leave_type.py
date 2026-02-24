# -*- coding: utf-8 -*-
from odoo import fields, models


class HrLeaveType(models.Model):
    """Extiende tipos de ausencia con configuración de factor amplio.
    
    Añade un campo booleano para indicar si el tipo de ausencia debe
    incluirse en el cálculo del factor amplio (broad factor) del empleado.
    El factor amplio es una métrica que mide el impacto de las ausencias.
    """
    _inherit = 'hr.leave.type'

    emp_broad_factor = fields.Boolean(
        string="Factor Amplio", help="Se mostrará en el reporte de factor amplio")
