# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrAnnouncementTable(models.Model):
    _name = 'hr.announcement'
    _description = 'HR Announcement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='No. codigo:', help="NUmero de secuencia")
    announcement_reason = fields.Text(string='Titulo', states={'draft': [('readonly', False)]}, required=True,
                                      readonly=True, help="Asunto de comunicado")
    state = fields.Selection([('draft', 'Borrador'), ('to_approve', 'Esperando aprobación'),
                          ('approved', 'Aprobado'), ('rejected', 'Rechazado'), ('expired', 'Expirado')],
                         string='Estado',  default='draft',
                         track_visibility='always')
    requested_date = fields.Date(string='Fecha solicitada', default=datetime.now().strftime('%Y-%m-%d'),
                                help="Fecha de creación del registro")
    attachment_id = fields.Many2many('ir.attachment', 'doc_warning_rel', 'doc_id', 'attach_id4',
                                    string="Adjuntos", help='Puedes adjuntar la copia de tu carta')
    company_id = fields.Many2one('res.company', string='Compañía',
                                default=lambda self: self.env.user.company_id, readonly=True, help="Compañía del usuario actual")
    is_announcement = fields.Boolean(string='¿Es un anuncio general?', help="Marcar para definir el anuncio como general")
    announcement_type = fields.Selection([('employee', 'Por empleado'), ('department', 'Por departamento'), ('job_position', 'Por puesto de trabajo')],
                         string='Tipo de comunicado',)
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_announcements', 'announcement', 'employee',
                                    string='Empleados', help="Empleados que deben ver este anuncio")
    department_ids = fields.Many2many('hr.department', 'hr_department_announcements', 'announcement', 'department',
                                    string='Departamentos', help="Departamentos que deben ver este anuncio")
    position_ids = fields.Many2many('hr.job', 'hr_job_position_announcements', 'announcement', 'job_position',
                                    string='Puestos de trabajo', help="Puestos que deben ver este anuncio")
    announcement = fields.Html(string='Carta', states={'draft': [('readonly', False)]}, readonly=True, help="Contenido del anuncio")
    date_start = fields.Date(string='Fecha de inicio', default=fields.Date.today(), required=True, help="Fecha desde la cual se debe mostrar el anuncio")
    date_end = fields.Date(string='Fecha de finalización', default=fields.Date.today(), required=True, help="Fecha hasta la cual se debe mostrar el anuncio")

    def reject(self):
        self.state = 'rejected'

    def approve(self):
        self.state = 'approved'

    def sent(self):
        self.state = 'to_approve'

    @api.constrains('date_start', 'date_end')
    def validation(self):
        if self.date_start > self.date_end:
            raise ValidationError("La fecha de inicio debe ser menor que la fecha de finalización")

    @api.model
    def create(self, vals):
        if vals.get('is_announcement'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.announcement.general')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.announcement')
        return super(HrAnnouncementTable, self).create(vals)

    def get_expiry_state(self):
        """
        La función se utiliza para marcar como expirados los anuncios en base a su fecha de vencimiento.
        Se activa desde una tarea programada (cron).
        """
        now = datetime.now()
        now_date = now.date()
        ann_obj = self.search([('state', '!=', 'rejected')])
        for recd in ann_obj:
            if recd.date_end < now_date:
                recd.write({
                    'state': 'expired'
                })
