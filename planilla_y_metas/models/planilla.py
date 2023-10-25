# -*- coding: utf-8 -*-

from odoo import models, api, fields
import datetime
import pytz


class DeductionsEmployee(models.Model):
    _name = "hr.employee.deductions"
    _description = "description"

    name = fields.Char("Deducción")
    period = fields.Integer("Periodo")
    deduction = fields.Float("Valor a deducir")
    percentage = fields.Float("Porcentaje %")
    formula = fields.Text("Formula")
    employee_file_id = fields.Many2one("hr.employee.file")
    tipo_deduction = fields.Selection([
        ('static', 'Valor estatico'),
        ('percentage', 'Porcentaje %'),
        ('formula', 'Formula (Programado)'),
    ], string="Tipo de deducción")


class FileEmployee(models.Model):
    _name = "hr.employee.file"
    _description = "description"

    name = fields.Many2one("hr.employee", "Empleado")
    base_salary = fields.Float("Salario Base")
    deductions_id = fields.Many2many(
        "hr.employee.deductions", "employee_file_id")

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         'El registro de empleado que intenta crear ya existe. \nPor favor corrijalo e intentelo de nuevo.')
    ]


class Spreadsheet(models.Model):
    _name = "hr.employee.spreadsheet"
    _description = "description"

    meses = ["","Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    def _name_(self):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
        fecha_ = pytz.utc.localize(
            self.date).astimezone(user_tz)
        fecha = fecha_.date()
        print("///////////////",self.meses[fecha.month],"/////////////////")
        

    name = fields.Char("Planilla", compute=_name_)
    date = fields.Datetime("Fecha")
