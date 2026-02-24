# -*- coding: utf-8 -*-
from odoo import fields, models


class HrContract(models.Model):
    """Extensión del modelo de contrato para agregar período de preaviso.
    
    Agrega el campo 'notice_days' para almacenar el período de preaviso
    requerido antes de la terminación del contrato. El valor predeterminado
    se obtiene de la configuración general del sistema.
    """
    _inherit = 'hr.contract'

    # ===== MÉTODOS AUXILIARES =====
    
    def _default_notice_days(self):
        """Obtiene el período de preaviso predeterminado desde la configuración.
        
        Returns:
            int: El período de preaviso en días, o 0 si no está configurado.
        """
        return self.env['ir.config_parameter'].get_param(
            'hr_employee_updation.no_of_days') if self.env[
            'ir.config_parameter'].get_param(
            'hr_employee_updation.notice_period') else 0

    # ===== CAMPOS =====
    
    notice_days = fields.Integer(string="Período de Preaviso",
                                 default=_default_notice_days,
                                 help="Número de días requeridos de preaviso"
                                      " antes de la terminación del contrato.")
