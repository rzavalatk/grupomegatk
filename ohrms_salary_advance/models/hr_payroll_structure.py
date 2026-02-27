# -*- coding: utf-8 -*-
from odoo import fields, models


class HrPayrollStructure(models.Model):
    """Extiende la estructura salarial con configuración de adelantos.
    
    Añade campos para configurar:
    - Porcentaje máximo de adelanto permitido sobre el salario
    - Número mínimo de días que deben transcurrir desde la última nómina
      antes de poder solicitar un adelanto
    """
    _inherit = 'hr.payroll.structure'

    max_percent = fields.Integer(string='Porcentaje Máximo de Adelanto',
                                 help="Porcentaje máximo del adelanto de "
                                      "salario sobre el salario base.")
    advance_date = fields.Integer(string='Adelanto - Después de Días',
                                  help="Número mínimo de días después de la "
                                       "última nómina para solicitar adelanto.")
