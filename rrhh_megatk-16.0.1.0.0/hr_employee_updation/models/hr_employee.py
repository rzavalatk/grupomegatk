# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, _, api

GENDER_SELECTION = [('male', 'Masculino'),
                    ('female', 'Femenino'),
                    ('other', 'Otro')]


class HrEmployeeFamilyInfo(models.Model):
    """Tabla para información familiar del empleado"""

    _name = 'hr.employee.family'
    _description = 'RRHH información familiar del empleado'

    employee_id = fields.Many2one('hr.employee', string="Empleado", help='Seleccionar empleado', invisible=1)
    relation_id = fields.Many2one('hr.employee.relation', string="Relación", help="Relación con el empleado")
    member_name = fields.Char(string='Nombre')
    member_contact = fields.Char(string='Numero de contacto')
    birth_date = fields.Date(string="Cumpleaños", tracking=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def mail_reminder(self):
        """Manda una notificación cuando se vaya a expirar la identidad o el pasaporte"""

        current_date = fields.Date.context_today(self) + timedelta(days=1)
        employee_ids = self.search(['|', ('id_expiry_date', '!=', False),
                                    ('passport_expiry_date', '!=', False)])
        for emp in employee_ids:
            if emp.id_expiry_date:
                exp_date = fields.Date.from_string(
                    emp.id_expiry_date) - timedelta(days=14)
                if current_date >= exp_date:
                    mail_content = "  Hola " + emp.name + ",<br>su identidad " + emp.identification_id + "ya va a expirar " + \
                                   str(emp.id_expiry_date) + ". Por favor, renuevela antes de la fecha de expiración"
                    main_content = {
                        'subject': _('ID-%s Expira en %s') % (
                            emp.identification_id, emp.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': emp.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
            if emp.passport_expiry_date:
                exp_date = fields.Date.from_string(
                    emp.passport_expiry_date) - timedelta(days=180)
                if current_date >= exp_date:
                    mail_content = "  Hola  " + emp.name + ",<br>su Pasaporte " + emp.passport_id + "ya va a expirar " + \
                                   str(emp.passport_expiry_date) + ".  Por favor, renuevela antes de la fecha de expiración"
                    main_content = {
                        'subject': _('Pasaporte-%s Expira en %s') % (
                            emp.passport_id, emp.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': emp.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()

    personal_mobile = fields.Char(
        string='Celular personal', related='address_home_id.mobile', store=True,)
    joining_date = fields.Date(string='Fecha de ingreso', compute='_compute_joining_date', store=True)
    id_expiry_date = fields.Date(string='Fecha de expiración de identidad',)
    passport_expiry_date = fields.Date(string='Fecha de expiración de pasaporte'),
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_rel','id_ref', 'attach_ref',string="Adjunto",help='Puede subir un adjunto de la identidad')
    passport_attachment_id = fields.Many2many('ir.attachment','passport_attachment_rel','passport_ref', 'attach_ref1',
        string="Adjunto", help='Puede subir un adjunto del pasaporte')
    fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Familia', help='Información familiar')

    @api.depends('contract_id')
    def _compute_joining_date(self):
        for rec in self:
            rec.joining_date = min(rec.contract_id.mapped('date_start'))\
                if rec.contract_id else False

    @api.onchange('spouse_complete_name', 'spouse_birthdate')
    def onchange_spouse(self):
        relation = self.env.ref('hr_employee_updation.employee_relationship')
        if self.spouse_complete_name and self.spouse_birthdate:
            self.fam_ids = [(0, 0, {
                'member_name': self.spouse_complete_name,
                'relation_id': relation.id,
                'birth_date': self.spouse_birthdate,
            })]


class EmployeeRelationInfo(models.Model):
    """Tabla para guardar información familiar de empleados"""

    _name = 'hr.employee.relation'

    name = fields.Char(string="Relación",
                       help="Relación con el empleado")
