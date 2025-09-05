# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HrEmployee(models.Model):
    """Para agregar los doctores de la clínica"""
    _inherit = 'hr.employee'

    job_position = fields.Char(string="Puesto de trabajo",
                               help="Agregar el puesto de trabajo del doctor")
    specialised_in_id = fields.Many2one('dental.specialist',
                                        string='Especializado en',
                                        help="Agregar el departamento en el que el doctor está especializado")
    dob = fields.Date(string="Fecha de nacimiento",
                      required=True,
                      help="Fecha de nacimiento del paciente")
    doctor_age = fields.Integer(compute='_compute_doctor_age',
                                store=True,
                                string="Edad",
                                help="Edad del paciente")
    sex = fields.Selection([('male', 'Masculino'),
                            ('female', 'Femenino')],
                           string="Sexo",
                           help="Sexo del paciente")
    time_shift_ids = fields.Many2many('dental.time.shift',
                                      string="Turno",
                                      help="Turno del doctor")

    def unlink(self):
        """Eliminar el usuario correspondiente de 'res.users' al
        eliminar el doctor"""
        for record in self:
            self.env['res.users'].search([
                ('id', '=', record.user_id.id)]).unlink()
        res = super(HrEmployee, self).unlink()
        return res

    @api.depends('dob')
    def _compute_doctor_age(self):
        """Calcular la edad del doctor a partir de la fecha de nacimiento"""
        for record in self:
            record.doctor_age = (fields.date.today().year - record.dob.year -
                                 ((fields.date.today().month,
                                   fields.date.today().day) <
                                  (record.dob.month,
                                   record.dob.day))) if record.dob else False
