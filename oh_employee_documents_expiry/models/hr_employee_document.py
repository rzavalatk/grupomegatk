# -*- coding: utf-8 -*-
from datetime import date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrEmployeeDocument(models.Model):
    """Modelo de Documentos de Empleados con Gestión de Vencimientos.
    
    Gestiona documentos relacionados con empleados y proporciona un sistema
    completo de notificaciones de vencimiento con múltiples estrategias:
    - Notificación única en la fecha de vencimiento
    - Notificación días antes del vencimiento
    - Notificaciones diarias hasta el vencimiento
    - Notificaciones en y después del vencimiento
    
    Ejemplos de documentos gestionados:
    - Pasaportes, licencias de conducir
    - Certificaciones profesionales
    - Permisos de trabajo
    - Contratos y acuerdos
    """
    _name = 'hr.employee.document'
    _description = 'Documentos de Empleados de RRHH'

    # ===== CAMPOS BÁSICOS =====
    
    name = fields.Char(string='Número de Documento', required=True, copy=False,
                       help='Puede ingresar el número de su documento.')
    description = fields.Text(string='Descripción', copy=False,
                              help="Descripción del documento.")
    expiry_date = fields.Date(string='Fecha de Vencimiento', copy=False,
                              help="Fecha de vencimiento del documento.")
    employee_ref_id = fields.Many2one('hr.employee', invisible=1,
                                      copy=False,
                                      help='Especifique el nombre del empleado.')
    doc_attachment_ids = fields.Many2many('ir.attachment',
                                          'doc_attach_rel',
                                          'doc_id', 'attach_id3',
                                          string="Adjunto",
                                          help='Puede adjuntar la copia de su'
                                               ' documento', copy=False)
    issue_date = fields.Date(string='Fecha de Emisión', default=fields.datetime.now(),
                             help="Fecha de emisión", copy=False)
    document_type_id = fields.Many2one('document.type',
                                       string="Tipo de Documento",
                                       help="Tipo del documento.")
    
    # ===== CONFIGURACIÓN DE NOTIFICACIONES =====
    
    before_days = fields.Integer(string="Días",
                                 help="Cuántos días antes para recibir "
                                      "el correo de notificación.")
    notification_type = fields.Selection([
        ('single', 'Notificación en fecha de vencimiento'),
        ('multi', 'Notificación días antes'),
        ('everyday', 'Todos los días hasta vencimiento'),
        ('everyday_after', 'Notificación en y después del vencimiento')
    ], string='Tipo de Notificación',
        help="Seleccione el tipo de notificación de vencimiento de documentos.")

    def mail_reminder(self):
        """Sending document expiry notification to employees."""
        for record in self.search([('expiry_date', '!=', False)]):
            exp_date = fields.Date.from_string(record.expiry_date)
            days_before = timedelta(days=record.before_days or 0)
            is_expiry_today = fields.Date.today() == exp_date
            is_notification_day = any([record.notification_type == 'single'
                                       and is_expiry_today,
                                       record.notification_type == 'multi'
                                       and (fields.Date.today() == fields.Date.
                                            from_string(
                                           record.expiry_date) - days_before
                                            or is_expiry_today),
                                       record.notification_type == 'everyday'
                                       and fields.Date.today() >= fields.Date.
                                      from_string(
                                           record.expiry_date) - days_before,
                                       record.notification_type ==
                                       'everyday_after'
                                       and fields.Date.today() <=
                                       fields.Date.from_string(
                                           record.expiry_date) + days_before,
                                       not record.notification_type and
                                       fields.Date.today() == fields.Date.
                                      from_string(
                                           record.expiry_date) - timedelta(
                                           days=7), ])
            if is_notification_day:
                employee_name = record.employee_ref_id.name
                document_name = record.name
                expiry_date_str = str(record.expiry_date)
                mail_content = (
                    f"Hello {employee_name},<br>Your Document {document_name} "
                    f"is going to expire on {expiry_date_str}. "
                    "Please renew it before the expiry date."
                )
                subject = _('Document-%s Expired On %s') % (
                    document_name, expiry_date_str)
                main_content = {
                    'subject': subject,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': record.employee_ref_id.work_email,
                }
                self.env['mail.mail'].create(main_content).send()

    # ===== MÉTODOS DE VALIDACIÓN =====
    
    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        """Valida que la fecha de vencimiento no esté en el pasado.
        
        Este método es llamado automáticamente como restricción cada vez que
        el campo 'expiry_date' de un registro 'hr.employee.document' es modificado.
        Previene la creación o actualización de documentos con fechas ya vencidas.
        
        Raises:
            UserError: Si la fecha de vencimiento es anterior a la fecha actual
        """
        for rec in self:
            if rec.expiry_date:
                exp_date = fields.Date.from_string(rec.expiry_date)
                if exp_date < date.today():
                    raise UserError(_('Su Documento Ya Está Vencido.'))
