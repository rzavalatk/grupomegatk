# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning, AccessError
from collections import defaultdict


class HrEmployeeDocument(models.Model):
    _name = 'hr.employee.document'
    _description = 'HR Employee Documents'

    def mail_reminder(self):
        """Mandar una notificación cuando se vaya a vencer el documento del empleado."""

        date_now = fields.Date.today()
        match = self.search([])
        for i in match:
            if i.expiry_date:
                if i.notification_type == 'single':
                    exp_date = fields.Date.from_string(i.expiry_date)
                    print('exp_date :', exp_date)
                    if date_now == i.expiry_date:
                        mail_content = "  Hola  " + i.employee_ref.name + ",<br> su documento " + i.name + " esta por expirar " + \
                                       str(i.expiry_date) + ". Por favor renueve el documento antes de expirar"
                        main_content = {
                            'subject': _('Documento-%s Expira en %s') % (
                                i.name, i.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': i.employee_ref.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
                elif i.notification_type == 'multi':
                    exp_date = fields.Date.from_string(
                        i.expiry_date) - timedelta(days=i.before_days)
                    if date_now == exp_date or date_now == i.expiry_date:  
                        mail_content = "  Hola  " + i.employee_ref.name + ",<br>su Documento " + i.name + \
                                       " esta por expirar " + str(
                            i.expiry_date) + \
                                       ". Por favor renueve antes de expirar"
                        main_content = {
                            'subject': _('Documento-%s a expirar en %s') % (
                                i.name, i.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': i.employee_ref.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
                elif i.notification_type == 'everyday':
                    exp_date = fields.Date.from_string(
                        i.expiry_date) - timedelta(days=i.before_days)
                    if date_now >= exp_date or date_now == i.expiry_date:
                        mail_content = "  Hola  " + i.employee_ref.name + ",<br>Su documento " + i.name + \
                                       " va a expirar en " + str(
                            i.expiry_date) + \
                                       ". Renuevelo antes de la fecha."
                        main_content = {
                            'subject': _('Documento-%s a expirar el %s') % (
                                i.name, i.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': i.employee_ref.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
                elif i.notification_type == 'everyday_after':
                    exp_date = fields.Date.from_string(
                        i.expiry_date) + timedelta(days=i.before_days)
                    if date_now <= exp_date or date_now == i.expiry_date:
                        mail_content = "  Hola  " + i.employee_ref.name + ",<br>Su documento " + i.name + \
                                       " Expira el " + str(i.expiry_date) + \
                                       ". Por favor renuevelo antes de la fecha."
                        main_content = {
                            'subject': _('Documento-%s Expira el %s') % (
                                i.name, i.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': i.employee_ref.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()
                else:
                    exp_date = fields.Date.from_string(
                        i.expiry_date) - timedelta(days=7)
                    if date_now == exp_date:
                        mail_content = "  Hola  " + i.employee_ref.name + ",<br>Su documento " + i.name + \
                                       " va a expirar en " + \
                                       str(i.expiry_date) + ". Renuevelo antes de la fecha."
                        main_content = {
                            'subject': _('Documento-%s Expira el %s') % (
                                i.name, i.expiry_date),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': i.employee_ref.work_email,
                        }
                        self.env['mail.mail'].create(main_content).send()

    @api.constrains('expiry_date')
    def check_expr_date(self):
        for each in self:
            if each.expiry_date:
                exp_date = fields.Date.from_string(each.expiry_date)
                if exp_date < date.today():
                    raise Warning('Su documento expiro.')

    name = fields.Char(string='Numero de documento', required=True, copy=False,)
    description = fields.Text(string='Descripción', copy=False, help="Descripción")
    expiry_date = fields.Date(string='Fecha de expiración', copy=False, help="Fecha de expiración")
    employee_ref = fields.Many2one('hr.employee', invisible=1, copy=False)
    doc_attachment_id = fields.Many2many('ir.attachment', 'doc_attach_rel',
                                         'doc_id', 'attach_id3',
                                         string="Adjunto",
                                         help='Puede adjuntar copia de su documento',
                                         copy=False)
    issue_date = fields.Date(string='Fecha de asunto', default=fields.datetime.now(),
                             help="Fecha de asunto", copy=False)
    document_type = fields.Many2one('document.type', string="Tipo de documento",
                                    help="Tipo de documento")
    before_days = fields.Integer(string="Dias",
                                 help="¿Cuántos días antes debo recibir el correo electrónico de notificación?")
    notification_type = fields.Selection([
        ('single', 'Notificación sobre la fecha de vencimiento'),
        ('multi', 'Notificación con unos días de antelación'),
        ('everyday', 'Todos los días hasta la fecha de caducidad.'),
        ('everyday_after', 'Notificación sobre el vencimiento y después del mismo')
    ], string='Tipo de notificación',
        help="""
        Notificación sobre la fecha de vencimiento: Recibirá una notificación solo en la fecha de vencimiento.
        Notificación en pocos días: Recibirá una notificación en 2 días. En la fecha de vencimiento y el número de días antes de la fecha.
        Todos los días hasta la fecha de vencimiento: Recibirá una notificación desde el número de días hasta la fecha de vencimiento del documento.
        Notificación al vencimiento y después del vencimiento: Recibirá una notificación en la fecha de vencimiento y hasta 7 días.
        Si no seleccionó ninguna opción, recibirá una notificación antes de 7 días del vencimiento del documento.""")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _document_count(self):
        for each in self:
            document_ids = self.env['hr.employee.document'].sudo().search(
                [('employee_ref', '=', each.id)])
            each.document_count = len(document_ids)

    def document_view(self):
        self.ensure_one()
        domain = [
            ('employee_ref', '=', self.id)]
        return {
            'name': _('Documentos'),
            'domain': domain,
            'res_model': 'hr.employee.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click para crear nuevos documentos
                        </p>'''),
            'limit': 80,
            'context': "{'default_employee_ref': %s}" % self.id
        }

    document_count = fields.Integer(compute='_document_count',
                                    string='# Documentos')


class HrEmployeeAttachment(models.Model):
    _inherit = 'ir.attachment'

    doc_attach_rel = fields.Many2many('hr.employee.document',
                                      'doc_attachment_id', 'attach_id3',
                                      'doc_id',
                                      string="Adjunto", invisible=1)
    attach_rel = fields.Many2many('hr.document', 'attach_id', 'attachment_id3',
                                  'document_id',
                                  string="Adjunto", invisible=1)

    @api.model
    def check(self, mode, values=None):
        """ Restringe el acceso a un archivo adjunto ir, según el modo al que se refiere """
        if self.env.is_superuser():
            return True
        # Siempre requiere que un usuario interno (es decir, un empleado) acceda a un archivo adjunto
        if not (self.env.is_admin() or self.env.user._is_internal()):
            if not self.env.user.has_group('hr.group_hr_manager'):
                raise AccessError(
                    _("Lo sentimos, no tienes permiso para acceder a este documento.."))
        # Recopilar los registros para comprobar (por modelo)
        model_ids = defaultdict(set)  # {model_name: set(ids)}
        if self:
            # DLE P173: `test_01_portal_attachment`
            self.env['ir.attachment'].flush_model(
                ['res_model', 'res_id', 'create_uid', 'public', 'res_field'])
            self._cr.execute(
                'SELECT res_model, res_id, create_uid, public, res_field FROM ir_attachment WHERE id IN %s',
                [tuple(self.ids)])
            for res_model, res_id, create_uid, public, res_field in self._cr.fetchall():
                if public and mode == 'read':
                    continue
                if not self.env.is_system() and (res_field or (
                        not res_id and create_uid != self.env.uid)):
                    if not self.env.user.has_group('hr.group_hr_manager'):
                        raise AccessError(
                            _("Lo sentimos, no tienes permiso para acceder a este documento."))
                if not (res_model and res_id):
                    continue
                model_ids[res_model].add(res_id)
        if values and values.get('res_model') and values.get('res_id'):
            model_ids[values['res_model']].add(values['res_id'])

        for res_model, res_ids in model_ids.items():
            if res_model not in self.env:
                continue
            if res_model == 'res.users' and len(
                    res_ids) == 1 and self.env.uid == list(res_ids)[0]:
               
                continue
            records = self.env[res_model].browse(res_ids).exists()
            
            access_mode = 'write' if mode in ('create', 'unlink') else mode
            records.check_access_rights(access_mode)
            records.check_access_rule(access_mode)
