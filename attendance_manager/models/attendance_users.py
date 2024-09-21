from odoo import models, fields, api

class AttendanceUsers(models.Model):
    _name = 'attendance.users'
    _description = 'Modelo de asistencias para usuarios'

    id_marcaciones = fields.Integer(string='ID marcaciones', required=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)