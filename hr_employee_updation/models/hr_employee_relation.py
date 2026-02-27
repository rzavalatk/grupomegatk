# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployeeRelation(models.Model):
    """Modelo para almacenar tipos de relaciones familiares.
    
    Define los diferentes tipos de relaciones familiares que pueden
    tener los empleados (cónyuge, hijo, padre, madre, hermano, etc.).
    Usado como catálogo para el módulo de información familiar.
    """

    _name = 'hr.employee.relation'
    _description = 'Relación de Empleado'

    # ===== CAMPO PRINCIPAL =====
    
    name = fields.Char(string="Relación",
                       help="Tipo de relación familiar con el empleado")
