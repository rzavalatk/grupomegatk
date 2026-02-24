# -*- coding: utf-8 -*-
from odoo import fields, models


class HrAttendance(models.Model):
    """Extensión del modelo de Asistencia para multi-compañía.
    
    Agrega el campo de compañía para registrar a qué empresa pertenece
    cada registro de asistencia, permitiendo separación de datos en
    entornos multi-empresa.
    """
    _inherit = 'hr.attendance'

    # ===== CAMPO DE COMPAÑÍA =====
    
    company_id = fields.Many2one(comodel_name='res.company',
                                 string='Compañía',
                                 copy=False, readonly=True,
                                 help="Compañía de la asistencia.",
                                 default=lambda self: self.env.user.company_id)
