# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
	_inherit = "hr.employee"

	permisos_dias = fields.Integer(string='Días',copy=False, track_visibility='onchange', default=0)
	permisos_horas = fields.Integer(string='Horas',copy=False, track_visibility='onchange', default=0)
	permisos_minutos = fields.Integer(string='minutos',copy=False, track_visibility='onchange', default=0)
	fecha_ingreso = fields.Date(string='Fecha de ingreso')

class HrEmployeePublic(models.Model):
	_inherit = "hr.employee.public"

	permisos_dias = fields.Integer(string='Días',copy=False, track_visibility='onchange', default=0)
	permisos_horas = fields.Integer(string='Horas',copy=False, track_visibility='onchange', default=0)
	permisos_minutos = fields.Integer(string='minutos',copy=False, track_visibility='onchange', default=0)
	fecha_ingreso = fields.Date(string='Fecha de ingreso')
