# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Empleado(models.Model):
    _inherit = "hr.employee"

    marcacion_id = fields.Char(string = "Reloj marcación")
    equipo_metas_id = fields.Many2one('hr.employee.equipo.metas', string='Equipo metas',)
    equipo_madrug_id = fields.Many2one('hr.employee.equipo.madrugador', string='Equipo madrugador',)

class EmpleadoMetas(models.Model):
    _name = 'hr.employee.equipo.metas'
    _description = 'Metas'
    _order = 'name asc'

    name = fields.Char("Equipo")
    active = fields.Boolean(string='Activo', default=True)
    employe_ids = fields.One2many('hr.employee', 'equipo_metas_id', string='Empleados',)
    employe_jefe_id = fields.Many2one('hr.employee', string='Jefe',)

class EmpleadoMetas(models.Model):
    _name = 'hr.employee.equipo.madrugador'
    _description = 'Madrugador'
    _order = 'name asc'

    name = fields.Char("Equipo")
    active = fields.Boolean(string='Activo', default=True)
    employe_ids = fields.One2many('hr.employee', 'equipo_madrug_id', string='Empleados',)

    

