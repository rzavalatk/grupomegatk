# -*- coding: utf-8 -*-
from odoo import models


class HrPayslip(models.Model):
    """Extiende hr.payslip para incluir adelantos de salario en la nómina.
    
    Sobrescribe el método get_inputs() para agregar automáticamente
    los adelantos de salario aprobados como deducciones en la nómina
    del mes correspondiente.
    """
    _inherit = 'hr.payslip'

    def get_inputs(self, contract_ids, date_from, date_to):
        """Añade adelantos de salario a las entradas de la nómina.
        
        Busca adelantos de salario aprobados para el empleado en el
        mes de la nómina y los agrega automáticamente como entrada
        con el código 'SAR' (Salary Advance Request).
        
        Args:
            contract_ids: Contratos del empleado
            date_from: Fecha de inicio del período de nómina
            date_to: Fecha de fin del período de nómina
            
        Returns:
            list: Lista de entradas incluyendo adelantos de salario
        """
        # Obtener entradas base del método padre
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from,
                                                date_to)
        # Obtener empleado del contrato o del payslip
        employee_id = self.env['hr.contract'].browse(
            contract_ids[0].id).employee_id if contract_ids \
            else self.employee_id
        
        # Buscar adelantos de salario del empleado
        advance_salary = self.env['salary.advance'].search(
            [('employee_id', '=', employee_id.id)])
        
        # Procesar adelantos del mes actual
        for record in advance_salary:
            current_date = date_from.month
            date = record.date
            existing_date = date.month
            # Si el adelanto es del mes actual
            if current_date == existing_date:
                state = record.state
                amount = record.advance
                # Agregar monto a la entrada SAR si está aprobado
                for result in res:
                    if state == 'approve' and amount != 0 and result.get(
                            'code') == 'SAR':
                        result['amount'] = amount
        return res
