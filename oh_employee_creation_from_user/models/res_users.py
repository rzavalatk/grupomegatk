# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResUsers(models.Model):
    """Extensión del modelo de Usuario para creación automática de empleados.
    
    Cuando se crea un nuevo usuario en el sistema, automáticamente se crea
    un registro de empleado vinculado. Esto simplifica la administración
    al evitar la necesidad de crear ambos registros por separado.
    """
    _inherit = 'res.users'

    # ===== CAMPO DE RELACIÓN =====
    
    employee_id = fields.Many2one('hr.employee',
                                  string='Empleado Relacionado',
                                  ondelete='restrict', auto_join=True,
                                  help='Empleado relacionado basado en los'
                                       ' datos del usuario')

    # ===== MÉTODOS SOBRESCRITOS =====
    
    @api.model_create_multi
    def create(self, vals):
        """Sobrescribe el método 'create' para crear automáticamente un empleado.
        
        Al crear un nuevo usuario, este método automáticamente:
        1. Crea el registro de usuario normalmente
        2. Crea un empleado vinculado con el nombre y datos del usuario
        3. Asocia el empleado con el usuario creado
        
        Args:
            vals (list): Lista de diccionarios con valores para crear usuarios
            
        Returns:
            recordset: Registros de usuarios creados con empleados vinculados
        """
        # Crea el usuario utilizando el método original
        result = super(ResUsers, self).create(vals)
        
        # Crea automáticamente el empleado asociado
        result['employee_id'] = self.env['hr.employee'].sudo().create({
            'name': result['name'],              # Nombre del empleado = nombre del usuario
            'user_id': result['id'],             # Vincula el usuario con el empleado
            'private_street': result['partner_id'].id  # Dirección del partner
        })
        return result
