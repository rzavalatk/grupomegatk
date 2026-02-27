# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrAnnouncement(models.Model):
    """Modelo que representa los Anuncios de Recursos Humanos.
    
    Este modelo permite crear y gestionar anuncios oficiales que pueden ser
    dirigidos a toda la empresa o a grupos específicos (empleados, departamentos
    o posiciones de trabajo). Incluye un sistema de aprobación y expiración
    automática de anuncios.
    """
    _name = 'hr.announcement'
    _description = 'Anuncio de RRHH'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ===== CAMPOS DEL MODELO =====
    
    name = fields.Char(
        string='Código No:',
        help="Secuencia del Anuncio")
    announcement_reason = fields.Text(
        string='Título', required=True,
        help="Asunto del anuncio")
    state = fields.Selection(
        selection=[('draft', 'Borrador'), 
                   ('to_approve', 'Esperando Aprobación'),
                   ('approved', 'Aprobado'), 
                   ('rejected', 'Rechazado'),
                   ('expired', 'Expirado')],
        string='Estado', default='draft', 
        help="Estado del anuncio.",
        track_visibility='always')
    requested_date = fields.Date(
        string='Fecha de Solicitud',
        default=fields.Datetime.now().strftime('%Y-%m-%d'),
        help="Fecha de creación del registro")
    attachment_id = fields.Many2many(
        'ir.attachment', 'doc_warning_rel', 'doc_id', 'attach_id4',
        string="Adjuntos", 
        help='Adjunte documentos relacionados con el anuncio')
    company_id = fields.Many2one(
        'res.company', string='Empresa',
        default=lambda self: self.env.user.company_id,
        readonly=True, help="Empresa del usuario que crea el anuncio")
    is_announcement = fields.Boolean(
        string='¿Es un Anuncio General?',
        help="Activar si este es un Anuncio General para toda la empresa")
    announcement_type = fields.Selection(
        [('employee', 'Por Empleado'), 
         ('department', 'Por Departamento'),
         ('job_position', 'Por Posición de Trabajo')], 
        string="Tipo de Anuncio",
        help="Por Empleado: Anuncio dirigido a empleados específicos.\n"
             "Por Departamento: Anuncio dirigido a empleados de "
             "departamentos específicos.\n"
             "Por Posición: Anuncio dirigido a empleados "
             "con posiciones de trabajo específicas")
    employee_ids = fields.Many2many(
        'hr.employee', 'hr_employee_announcements',
        'announcement', 'employee',
        string='Empleados',
        help="Empleados que podrán ver este anuncio")
    department_ids = fields.Many2many(
        'hr.department', 'hr_department_announcements',
        'announcement', 'department',
        string='Departamentos',
        help="Departamentos que podrán ver este anuncio")
    position_ids = fields.Many2many(
        'hr.job', 'hr_job_position_announcements',
        'announcement', 'job_position',
        string='Posiciones de Trabajo',
        help="Posiciones de los empleados autorizados "
             "a ver este anuncio.")
    announcement = fields.Html(
        string='Contenido', 
        help="Mensaje del anuncio")
    date_start = fields.Date(
        string='Fecha de Inicio', default=fields.Date.today(),
        required=True, help="Fecha de inicio del anuncio")
    date_end = fields.Date(
        string='Fecha de Fin', default=fields.Date.today(),
        required=True, help="Fecha de fin del anuncio")

    # ===== VALIDACIONES (CONSTRAINS) =====

    @api.constrains('date_start', 'date_end')
    def _check_date_start(self):
        """Valida que la fecha de inicio sea anterior a la fecha de fin.
        
        Raises:
            ValidationError: Si la fecha de inicio es mayor que la de fin
        """
        if self.date_start > self.date_end:
            raise ValidationError(_("La Fecha de Inicio debe ser anterior "
                                    "a la Fecha de Fin"))

    # ===== MÉTODOS DE CREACIÓN =====

    @api.model
    def create(self, vals):
        """Crea un nuevo anuncio asignando un número de secuencia.
        
        Asigna diferentes secuencias según sea un anuncio general o específico.
        
        Args:
            vals (dict): Diccionario con los valores del nuevo anuncio
            
        Returns:
            hr.announcement: Registro del anuncio creado
        """
        if vals.get('is_announcement'):
            # Secuencia para anuncios generales
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'hr.announcement.general')
        else:
            # Secuencia para anuncios específicos
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'hr.announcement')
        return super(HrAnnouncement, self).create(vals)

    # ===== ACCIONES DE BOTONES =====

    def action_reject_announcement(self):
        """Rechaza el anuncio.
        
        Ejecutado por el botón 'Rechazar' (solo gerentes de RRHH).
        """
        self.state = 'rejected'

    def action_approve_announcement(self):
        """Aprueba el anuncio.
        
        Ejecutado por el botón 'Aprobar' (solo gerentes de RRHH).
        """
        self.state = 'approved'

    def action_sent_announcement(self):
        """Envía el anuncio para aprobación.
        
        Ejecutado por el botón 'Enviar para Aprobación' (usuarios de RRHH).
        """
        self.state = 'to_approve'

    # ===== MÉTODOS AUTOMATIZADOS (CRON) =====

    def get_expiry_state(self):
        """Expira anuncios basándose en su fecha de fin.
        
        Este método es ejecutado por un trabajo programado (cron) que revisa
        todos los anuncios y marca como 'expirado' aquellos cuya fecha de fin
        ha pasado.
        """
        # Busca todos los anuncios que no estén rechazados
        announcements = self.search([('state', '!=', 'rejected')])
        for announcement in announcements:
            # Si la fecha de fin es anterior a hoy, marca como expirado
            if announcement.date_end < fields.Date.today():
                announcement.write({
                    'state': 'expired'
                })
