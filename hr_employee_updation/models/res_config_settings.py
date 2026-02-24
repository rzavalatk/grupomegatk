# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Extensión de configuración para período de preaviso.
    
    Agrega configuraciones relacionadas con el período de preaviso que
    los empleados deben cumplir antes de terminar su relación laboral.
    """
    _inherit = 'res.config.settings'

    # ===== CONFIGURACIONES DE PERÍODO DE PREAVISO =====
    
    notice_period = fields.Boolean(string='Período de Preaviso',
                                   help='Habilite para configurar un período de preaviso'
                                        ' para los empleados.',
                                   config_parameter='hr_employee_updation.notice_period')
    no_of_days = fields.Integer(string='Días de Preaviso',
                                help='Establezca el número de días para el período'
                                     ' de preaviso.',
                                config_parameter='hr_employee_updation.no_of_days')
