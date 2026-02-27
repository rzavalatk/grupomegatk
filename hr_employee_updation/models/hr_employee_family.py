# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _


class HrEmployeeFamily(models.Model):
    """Modelo para almacenar información de familiares de empleados.
    
    Permite registrar datos de los familiares y dependientes de cada empleado,
    incluyendo nombre, relación familiar, contacto y fecha de nacimiento.
    Útil para gestión de beneficios, seguros y contactos de emergencia.
    """
    _name = 'hr.employee.family'
    _description = 'Información Familiar de Empleado'
    _rec_name = 'member_name'

    # ===== CAMPOS =====
    
    employee_id = fields.Many2one('hr.employee', string="Empleado",
                                  help='Seleccione el empleado correspondiente',
                                  invisible=1)
    relation_id = fields.Many2one('hr.employee.relation', string="Relación",
                                  help="Relación familiar con el empleado")
    member_name = fields.Char(string='Nombre', help='Nombre del familiar')
    member_contact = fields.Char(string='Número de Contacto',
                                 help='Número de contacto del familiar')
    birth_date = fields.Date(string="Fecha de Nacimiento", tracking=True,
                             help='Fecha de nacimiento del familiar')
