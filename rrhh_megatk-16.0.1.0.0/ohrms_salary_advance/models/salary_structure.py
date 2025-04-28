# -*- coding: utf-8 -*-

from odoo import fields, models


class SalaryStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    max_percent = fields.Integer(string='Porcentaje máximo de anticipo de salario', help="Porcentaje máximo de anticipo de salario")
    advance_date = fields.Integer(string='Adelanto de sueldo-Después de días', help="Adelanto de sueldo-Después de días")

