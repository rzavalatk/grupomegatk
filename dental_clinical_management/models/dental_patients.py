# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import email_normalize


class ResPartner(models.Model):
    """Para crear pacientes en la clínica, se utiliza el modelo res.partner y se personaliza"""
    _inherit = 'res.partner'

    company_type = fields.Selection(selection_add=[('person', 'Paciente'),
                                                   ('company', 'Distribuidor de Medicamentos')],
                                    help="Tipo de paciente")
    dob = fields.Date(string="Fecha de nacimiento",
                      help="Fecha de nacimiento del paciente")
    patient_age = fields.Integer(compute='_compute_patient_age',
                                 store=True,
                                 string="Edad",
                                 help="Edad del paciente")
    sex = fields.Selection([('male', 'Masculino'), ('female', 'Femenino')],
                           string="Sexo",
                           help="Sexo del paciente")
    insurance_company_id = fields.Many2one('insurance.company',
                                           string="Compañía de seguros",
                                           help="Mencione la compañía de seguros")
    start_date = fields.Date(string="Miembro desde",
                             help="Fecha de inicio del seguro del paciente")
    expiration_date = fields.Date(string="Fecha de expiración",
                                  help="Fecha de expiración del seguro del paciente")
    insureds_name = fields.Char(string="Nombre del asegurado",
                                help="Nombre del asegurado")
    identification_number = fields.Char(string="Número de identificación",
                                        help="Número de identificación del asegurado")
    is_patient = fields.Boolean(string="Es paciente",
                                help="Para indicar que es un paciente")
    medical_questionnaire_ids = fields.One2many('medical.questionnaire',
                                                'patient_id',
                                                readonly=False,
                                                help="Conectar el modelo cuestionario médico en pacientes")
    report_ids = fields.One2many('xray.report', 'patient_id',
                                 string='Rayos X',
                                 help="Agregar los reportes de rayos X del paciente")

    @api.model
    def create(self, vals):
        """Sobrescribe el método create para manejar lógica adicional para DentalPatients.
        Cuando se crea un nuevo paciente, se procede a crear un asistente de portal
        para otorgarle acceso al portal.

        Si el `company_type` no es `person`, se asume que el registro es para un
        distribuidor de medicamentos u otra entidad. En este caso, se crea un usuario
        desde una plantilla con grupos y permisos predefinidos, y se normaliza el correo
        electrónico para consistencia."""

        if 'company_type' in vals and vals['company_type'] == 'person':
            vals['is_patient'] = True
        res = super(ResPartner, self).create(vals)
        if 'company_type' in vals and vals['company_type'] == 'person':
            wizard = self.env['portal.wizard'].create({
                'partner_ids': [fields.Command.link(res.id)]
            })
            portal_wizard = self.env['portal.wizard.user'].sudo().create({
                'partner_id': res.id,
                'email': res.email,
                'wizard_id': wizard.id,
            })
            portal_wizard.action_grant_access()
        else:
            try:
                user = self.env['res.users'].with_context(
                    no_reset_password=True)._create_user_from_template({
                    'email': email_normalize(res.email),
                    'login': email_normalize(res.email),
                    'partner_id': res.id,
                    'groups_id': [
                        self.env.ref("base.group_user").id,
                        self.env.ref(
                            'dental_clinical_management.group_dental_doctor').id,
                        self.env.ref('sales_team.group_sale_salesman').id,
                        self.env.ref('hr.group_hr_user').id,
                        self.env.ref('account.group_account_invoice').id,
                        self.env.ref('stock.group_stock_user').id,
                        self.env.ref('purchase.group_purchase_user').id
                    ],
                    'company_id': self.env.company.id,
                    'company_ids': [(6, 0, self.env.company.ids)],
                })
                self.env['hr.employee'].search(
                    [('work_email', '=', res.email)]).user_id = user.id
            except:
                raise UserError(_("El correo electrónico ya está en uso por otro dentista"))
        return res

    @api.depends('dob')
    def _compute_patient_age(self):
        """Calcula la edad del paciente según su fecha de nacimiento (dob)
        y actualiza el campo `patient_age`. La edad se calcula restando el año
        de nacimiento del paciente al año actual. Si la fecha actual es antes
        del cumpleaños del paciente en el año actual, se resta un año a la edad."""
        for record in self:
            record.patient_age = (fields.date.today().year - record.dob.year -
                                  ((fields.date.today().month,
                                    fields.date.today().day) <
                                   (record.dob.month,
                                    record.dob.day))) if record.dob else False
