# -*- coding: utf-8 -*-
from odoo import api, fields, models

class HrContract(models.Model):
    """Extensión del modelo de Contratos de RRHH.
    
    Este modelo extiende 'hr.contract' agregando un campo adicional 'emp_transfer'
    para vincular contratos con empleados transferidos. El método 'create' se
    personaliza para actualizar automáticamente el estado de la transferencia
    cuando se crea un nuevo contrato para un empleado transferido.
    """
    _inherit = 'hr.contract'

    # ===== CAMPOS ADICIONALES =====
    
    emp_transfer = fields.Many2one(
        'employee.transfer', string='Empleado Transferido',
        help="Empleado que ha sido transferido y necesita un nuevo contrato")

    @api.model
    def create(self, vals):
        """Crea un nuevo registro de contrato con los valores proporcionados.
        
        Sobrescribe el método create para actualizar automáticamente el estado
        de la transferencia de empleado a 'done' cuando se crea un nuevo contrato
        para un empleado que fue transferido.
        
        Args:
            vals (dict): Diccionario con los valores del nuevo contrato
            
        Returns:
            hr.contract: Registro del contrato creado
        """
        # Llama al método create original del padre
        res = super(HrContract, self).create(vals)
        
        # Si el contrato está vinculado a una transferencia
        if res.emp_transfer:
            # Actualiza el estado de la transferencia a 'finalizado'
            res.emp_transfer.write(
                {'state': 'done'})
        return res
