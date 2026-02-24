# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ActivoFijo(models.Model):
    _inherit = 'account.asset'

    employee_id = fields.Many2one('hr.employee', string='Responsable',)
    departamento = fields.Char(related='employee_id.department_id.name', string="Departamento")

    marca = fields.Char(string='Marca',)
    modelo = fields.Char(string='Modelo',)
    serie = fields.Char(string='Serie',)
    descripcion = fields.Text(string='Descripción',)


    