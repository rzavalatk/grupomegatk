# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields


class HrEmployeeBase(models.AbstractModel):
    """Extiende el modelo base de empleado para recalcular nuevas contrataciones.
    
    Sobrescribe el método _compute_newly_hired para determinar si un
    empleado es considerado "recién contratado" basado en su fecha de
    primer contrato o creación (dentro de los últimos 90 días).
    """
    _inherit = 'hr.employee.base'

    def _compute_newly_hired(self):
        """Verifica empleados recién contratados por fecha.
        
        Un empleado se considera recién contratado si su fecha de primer
        contrato (o fecha de creación si no tiene contrato) es dentro de
        los últimos 90 días desde hoy.
        """
        # Calcular fecha límite (90 días atrás)
        new_hire_date = fields.Datetime.now() - timedelta(days=90)
        for employee in self:
            if employee['first_contract_date']:
                # Si tiene fecha de primer contrato, usarla
                employee.newly_hired = (employee[
                                           'first_contract_date'] >
                                        new_hire_date.date())
            else:
                # Si no, usar fecha de creación del registro
                employee.newly_hired = employee[
                                           'create_date'] > new_hire_date
