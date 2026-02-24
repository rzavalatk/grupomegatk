# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _

GENDER_SELECTION = [('male', 'Masculino'),
                    ('female', 'Femenino'),
                    ('other', 'Otro')]


class HrEmployee(models.Model):
    """Modelo extendido de empleado con información adicional.
    
    Agrega campos relacionados con información personal, familiar y documentos
    de identificación del empleado. Incluye funcionalidades para el cálculo
    automático de la fecha de ingreso y notificaciones de vencimiento de documentos.
    """
    _inherit = 'hr.employee'

    # ===== CAMPOS ADICIONALES =====
    
    personal_mobile = fields.Char(string='Móvil', related='private_phone',
                                  help="Número de móvil personal del "
                                       "empleado", store=True, )
    joining_date = fields.Date(compute='_compute_joining_date',
                               string='Fecha de Ingreso', store=True,
                               help="Fecha de ingreso del empleado calculada a partir de la"
                                    " fecha de inicio del contrato")
    id_expiry_date = fields.Date(help='Fecha de vencimiento del documento de Identificación',
                                 string='Fecha de Vencimiento',)
    passport_expiry_date = fields.Date(help='Fecha de vencimiento del Pasaporte',
                                       string='Fecha de Vencimiento')
    identification_attachment_ids = fields.Many2many(
        'ir.attachment', 'id_attachment_rel',
        'id_ref', 'attach_ref', string="Adjunto",
        help='Adjunte la copia del documento de Identificación')
    # Alias legacy para compatibilidad con vistas antiguas que usan "id_attachment_id"
    id_attachment_id = fields.Many2many(
        'ir.attachment',
        string="Adjunto",
        related='identification_attachment_ids',
        readonly=False,
        help='Campo legado, use identification_attachment_ids.')
    passport_attachment_ids = fields.Many2many(
        'ir.attachment',
        'passport_attachment_rel',
        'passport_ref', 'attach_ref1', string="Adjunto",
        help='Adjunte la copia del Pasaporte')
    # Alias legacy para compatibilidad con vistas antiguas que usan "passport_attachment_id"
    passport_attachment_id = fields.Many2many(
        'ir.attachment',
        string="Adjunto",
        related='passport_attachment_ids',
        readonly=False,
        help='Campo legado, use passport_attachment_ids.')
    family_info_ids = fields.One2many(
        'hr.employee.family', 'employee_id',
        string='Familia',
        help='Información Familiar')
    # Alias legacy para compatibilidad con vistas antiguas que usan "fam_ids"
    fam_ids = fields.One2many(
        'hr.employee.family', 'employee_id',
        string='Familia',
        help='Campo legado, use family_info_ids.')

    # ===== MÉTODOS COMPUTADOS =====
    
    @api.depends('contract_id')
    def _compute_joining_date(self):
        """Calcula la fecha de ingreso del empleado basado en su contrato.
        
        Toma la fecha más antigua de inicio de contrato como fecha de ingreso.
        Si no existe contrato, el campo permanece vacío.
        """
        for employee in self:
            employee.joining_date = min(
                employee.contract_id.mapped('date_start')) \
                if employee.contract_id else False

    # ===== MÉTODOS ONCHANGE =====
    
    @api.onchange('spouse_complete_name', 'spouse_birthdate')
    def _onchange_spouse_complete_name(self):
        """Llena automáticamente el campo family_info_ids con información del cónyuge.
        
        Crea automáticamente un registro de familiar asociado al empleado cuando
        se completa el nombre o fecha de nacimiento del cónyuge.
        """
        relation = self.env.ref('hr_employee_updation.employee_relationship')
        if self.spouse_complete_name and self.spouse_birthdate:
            self.family_info_ids = [(0, 0, {
                'member_name': self.spouse_complete_name,
                'relation_id': relation.id,
                'birth_date': self.spouse_birthdate,
            })]

    # ===== MÉTODOS DE NEGOCIO =====
    
    def expiry_mail_reminder(self):
        """Envía recordatorios por correo sobre vencimiento de documentos.
        
        Envía notificaciones automáticas a los empleados cuando sus documentos
        de identificación o pasaporte están próximos a vencer:
        - ID: 14 días antes del vencimiento
        - Pasaporte: 180 días (6 meses) antes del vencimiento
        
        Este método es llamado típicamente por una tarea programada (cron).
        """
        # Fecha actual más un día para verificar próximos vencimientos
        current_date = fields.Date.context_today(self) + timedelta(days=1)
        
        # Busca empleados con documentos que tienen fecha de vencimiento
        employee_ids = self.search(['|', ('id_expiry_date', '!=', False),
                                    ('passport_expiry_date', '!=', False)])
        
        for employee in employee_ids:
            # Verifica vencimiento de ID (notifica 14 días antes)
            if employee.id_expiry_date:
                exp_date = fields.Date.from_string(
                    employee.id_expiry_date) - timedelta(days=14)
                if current_date >= exp_date:
                    mail_content = ("Hola " + employee.name + ",<br>Su ID "
                                    + employee.identification_id +
                                    " va a vencer el " +
                                    str(employee.id_expiry_date)
                                    + ". Por favor renuévelo antes de la fecha de vencimiento")
                    main_content = {
                        'subject': _('ID-%s Vence el %s') % (
                            employee.identification_id,
                            employee.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': employee.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
            
            # Verifica vencimiento de Pasaporte (notifica 180 días antes)
            if employee.passport_expiry_date:
                exp_date = fields.Date.from_string(
                    employee.passport_expiry_date) - timedelta(days=180)
                if current_date >= exp_date:
                    mail_content = ("Hola " + employee.name +
                                    ",<br>Su Pasaporte " + employee.passport_id
                                    +" va a vencer el " +
                                    str(employee.passport_expiry_date) +
                                    ". Por favor renuévelo antes de que expire")
                    main_content = {
                        'subject': _('Pasaporte-%s Vence el %s') % (
                            employee.passport_id,
                            employee.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': employee.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()

    def document_view(self):
        """Alias legacy para compatibilidad con botones antiguos."""
        return self.action_document_view()
