# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

PRIORITIES = [
    ('0', 'Muy bajo'),
    ('1', 'Bajo'),
    ('2', 'Normal'),
    ('3', 'Alto'),
    ('4', 'Muy alto'),
]
RATING = [
    ('0', 'Muy bajo'),
    ('1', 'Bajo'),
    ('2', 'Normal'),
    ('3', 'Alto'),
    ('4', 'Muy alto'),  
    ('5', 'Extremadamente alto'),
]


class HelpTicket(models.Model):
    """Este modelo representa el Ticket de Mesa de Ayuda, que permite a los usuarios plantear
    entradas relacionadas con productos, servicios o cualquier otro tema. Cada billete tiene un
    nombre, información del cliente, descripción, equipo responsable del manejo
    solicitudes, proyecto asociado, nivel de prioridad, etapa, costo por hora, servicio
    producto, fechas de inicio y finalización, y tareas y facturas relacionadas."""

    _name = 'help.ticket'
    _description = 'Help Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', default=lambda self: _('New'),
                       readonly=True)
    active = fields.Boolean(default=True, help='Active', string='Activo')
    customer_id = fields.Many2one('res.partner', string='Cliente',)
    customer_name = fields.Char(string='Nombre del cliente',)
    subject = fields.Text(string='Asunto', required=True, help='Asunto del Ticket')
    description = fields.Text(string='Descripción', required=True, help='Descripción del Ticket')
    email = fields.Char(string='Correo electronico', help='Correo del cliente.')
    phone = fields.Char(string='Telefono', help='Telefono del cliente.')
    company_id = fields.Many2one('res.company', string='Compañia')
    team_id = fields.Many2one('help.team', string='Equipo de soporte',)
    product_ids = fields.Many2many('product.template', string='Producto',)
    project_id = fields.Many2one('project.project',
                                 string='Proyecto',
                                 readonly=False,
                                 related='team_id.project_id',
                                 store=True,
                                 help='El proyecto en el que se encuentran actualmente. ')
    priority = fields.Selection(PRIORITIES,
                                default='1',
                                help='Prioridad del Ticket',
                                string='Prioridad')
    stage_id = fields.Many2one('ticket.stage', string='Etapa',
                               default=lambda self: self.env[
                                   'ticket.stage'].search(
                                   [('name', '=', 'Draft')], limit=1).id,
                               tracking=True,
                               group_expand='_read_group_stage_ids',
                               help='Etapa del ticket.')
    user_id = fields.Many2one('res.users',
                              default=lambda self: self.env.user,
                              check_company=True,
                              index=True, tracking=True,
                              help='Usuario logueado en el sistema.')
    cost = fields.Float(string='Costo por hora', help='Costo por hora')
    service_product_id = fields.Many2one('product.product', string='Producto de servicio', domain=[('detailed_type', '=', 'service')])
    create_date = fields.Datetime(string='Fecha de creación',)
    start_date = fields.Datetime(string='Fecha de inicio',)
    end_date = fields.Datetime(string='Fecha de cierre', )
    public_ticket = fields.Boolean(string="Tciket publico", )
    invoice_ids = fields.Many2many('account.move', string='Facturas',)
    task_ids = fields.Many2many('project.task', string='Tareas',)
    color = fields.Integer(string="Color", help='Color')
    replied_date = fields.Datetime(string='Fecha de respuesta', help='Fecha de respuesta del Ticket')
    last_update_date = fields.Datetime(string='Fecha de última actualización',)
    ticket_type = fields.Many2one('helpdesk.types', string='Tipo de Ticket', help='Tipo de Ticket')
    team_head = fields.Many2one('res.users', string='Lider del team', compute='_compute_team_head',)
    assigned_user = fields.Many2one('res.users', string='Tecnico Asignado',
        domain=lambda self: [('groups_id', 'in', self.env.ref(
            'odoo_website_helpdesk.helpdesk_user').id)],)
    category_id = fields.Many2one('helpdesk.categories', string='Categoria', help='Categoría del Ticket')
    tags = fields.Many2many('helpdesk.tag', string='Etiquetas', help='Etiquetas del Ticket')
    assign_user = fields.Boolean(string='¿Usuario Asignado?',)
    attachment_ids = fields.One2many('ir.attachment',
                                     'res_id',
                                     string='Adjunto')
    merge_ticket_invisible = fields.Boolean(string='Fusionar ticket',)
    merge_count = fields.Integer(string='Recuento de fusiones', )
    
    tipo_soporte = fields.Selection([('llamada','Llamada'),('interno','Interno'),('visita','Visita'),('visita_sin_costo','Visita sin costo'),('taller','Taller'),('sin_costo','Sin Costo')], string='Tipo de Soporte', default='sin_costo')
    tipo_visita = fields.Selection([('cortesia','Cortesía'),('contado','Contado'),('garantia','Garantía'),('capacitacion','Capacitación'),('instalacion','Instalación')], string='Tipo de Visita')
    

    @api.onchange('team_id', 'team_head')
    def team_leader_domain(self):
        """Actualice el dominio para el usuario asignado según el equipo seleccionado.

        Este método de cambio se activa cuando el equipo de soporte técnico o el líder del equipo
        está cambiado. Actualiza el dominio para que el campo de usuario asignado incluya
        sólo los miembros del equipo seleccionado."""
        teams = []
        for rec in self.team_id.member_ids:
            teams.append(rec.id)
        return {'domain': {'assigned_user': [('id', 'in', teams)]}}

    @api.depends('team_id')
    def _compute_team_head(self):
        """Calcular el jefe del equipo en función del equipo seleccionado.

        Este método se activa cuando se cambia el equipo de asistencia técnica. Se calcula
        y actualiza el campo principal del equipo según el liderazgo del equipo.
       """
        self.team_head = self.team_id.team_lead_id.id

    @api.onchange('stage_id')
    def mail_snd(self):
        """Enviar un correo electrónico cuando se cambie la etapa del ticket.

        Este método de cambio se activa cuando la etapa del ticket se
        cambió. Actualiza la fecha de la última actualización, la fecha de inicio y la fecha de finalización.
        campos en consecuencia. Si una plantilla está asociada con la etapa del ticket,
        envía un correo electrónico utilizando esa plantilla."""
        rec_id = self._origin.id
        data = self.env['help.ticket'].search([('id', '=', rec_id)])
        data.last_update_date = fields.Datetime.now()
        if self.stage_id.starting_stage:
            data.start_date = fields.Datetime.now()
        if self.stage_id.closing_stage or self.stage_id.cancel_stage:
            data.end_date = fields.Datetime.now()
        if self.stage_id.template_id:
            mail_template = self.stage_id.template_id
            mail_template.send_mail(self._origin.id, force_send=True)

    def assign_to_teamleader(self):
        """Asigne el ticket al líder del equipo y envíe una notificación.

        Esta función comprueba si se ha seleccionado un equipo de asistencia técnica y asigna el
        líder del equipo al boleto. Luego envía un correo electrónico de notificación al
        jefe de equipo."""
        if self.team_id:
            self.team_head = self.team_id.team_lead_id.id
            mail_template = self.env.ref(
                'odoo_website_helpdesk.'
                'mail_template_odoo_website_helpdesk_assign')
            mail_template.sudo().write({
                'email_to': self.team_head.email,
                'subject': self.name
            })
            mail_template.sudo().send_mail(self.id, force_send=True)
        else:
            raise ValidationError("Please choose a Helpdesk Team")

    def _default_show_create_task(self):
        """Obtenga el valor predeterminado para el campo 'show_create_task'.

        Este método recupera el valor predeterminado para 'show_create_task'
        campo de los ajustes de configuración."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.show_create_task')

    show_create_task = fields.Boolean(string="Crear tarea",
                                      default=_default_show_create_task,
                                      compute='_compute_show_create_task',)
    create_task = fields.Boolean(string="Crear tarea", readonly=False,
                                 related='team_id.create_task',
                                 store=True,)
    billable = fields.Boolean(string="facturable", help='Indica si el ticket es facturable o no')

    def _default_show_category(self):
        """Muestra la categoría predeterminada."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.show_category')

    show_category = fields.Boolean(default=_default_show_category,
                                   compute='_compute_show_category',)
    customer_rating = fields.Selection(RATING, default='0', readonly=True,
                                       string='Calificación del cliente',)

    review = fields.Char(string='Comentario del cliente', readonly=True,)
    kanban_state = fields.Selection([
        ('normal', 'Listo'),
        ('done', 'En progreso'),
        ('blocked', 'Bloqueado'), ], default='normal')

    def _compute_show_category(self):
        
        show_category = self._default_show_category()
        for rec in self:
            rec.show_category = show_category

    def _compute_show_create_task(self):
        """Calcule el valor del campo 'show_create_task' para cada registro en
        el conjunto de registros actual."""
        show_create_task = self._default_show_create_task()
        for record in self:
            record.show_create_task = show_create_task

    def auto_close_ticket(self):
        """Cerrar automáticamente el ticket según la fecha de cierre."""
        auto_close = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.auto_close_ticket')
        if auto_close:
            no_of_days = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_website_helpdesk.no_of_days')
            records = self.env['help.ticket'].search([])
            for rec in records:
                days = (fields.Datetime.today() - rec.create_date).days
                if days >= int(no_of_days):
                    close_stage_id = self.env['ticket.stage'].search(
                        [('closing_stage', '=', True)])
                    if close_stage_id:
                        rec.stage_id = close_stage_id

    def default_stage_id(self):
        """Buscar etapa"""
        return self.env['ticket.stage'].search(
            [('name', '=', 'Draft')], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """
        Devuelve las etapas disponibles para agrupar.

        Este método estático se utiliza para proporcionar las etapas disponibles para
        agrupación al mostrar registros en una vista agrupada.

        """
        stage_ids = self.env['ticket.stage'].search([])
        return stage_ids

    @api.model
    def create(self, vals_list):
        """Cree un nuevo ticket de asistencia técnica.
        Este método se llama al crear un nuevo ticket de soporte técnico. Él
        genera un nombre único para el ticket usando una secuencia si no
        se proporciona el nombre.
        """
        if vals_list.get('name', _('New')) == _('New'):
            vals_list['name'] = self.env['ir.sequence'].next_by_code(
                'help.ticket') or _('New')
        return super().create(vals_list)

    def action_create_ticket_crm(self):
        # Crear el ticket de CRM usando self.env
        ticket = self.env['crm.lead'].create({
            'name': f'SPT/{self.customer_id.name}',   # Nombre del ticket
            'partner_id': self.customer_id.id,        # ID del cliente (partner)
            'user_id': self.assigned_user.id,             # Asignado a (usuario actual)
            'company_id': 8,   # Empresa relacionada (opcional)
            'description': self.description,
            'priority': self.priority,                     # Prioridad del ticket (opcional)
            'tipo_soporte': self.tipo_soporte,
            'tipo_visita': self.tipo_visita,
            'proposito': self.subject,
            'reporto': self.customer_name,
            'repor_tel': self.phone,
            'repor_email': self.email,
        })

        # Devolver la acción para redirigir al usuario al ticket recién creado
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ticket CRM',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': ticket.id,  # ID del ticket recién creado
            'target': 'current',  # Abrir en la misma ventana
        }

    def action_create_invoice(self):
        """Crear factura para ticket de la mesa de ayuda.
        Esta función crea una factura para el ticket de la mesa de ayuda basada en
        las tareas asociadas con horas facturadas.
        """
        tasks = self.env['project.task'].search(
            [('project_id', '=', self.project_id.id),
             ('ticket_id', '=', self.id)]).filtered(
            lambda line: line.ticket_billed == True)
        if not tasks:
            raise UserError('No hay tareas por facturar.')
        total = sum(x.effective_hours for x in tasks if x.effective_hours > 0)
        invoice_no = self.env['ir.sequence'].next_by_code(
            'ticket.invoice')
        self.env['account.move'].create([
            {
                'name': invoice_no,
                'move_type': 'out_invoice',
                'partner_id': self.customer_id.id,
                'ticket_id': self.id,
                'date': fields.Date.today(),
                'invoice_date': fields.Date.today(),
                'invoice_line_ids':
                    [(0, 0, {'product_id': self.service_product_id.id,
                             'name': self.service_product_id.name,
                             'quantity': total,
                             'product_uom_id': self.service_product_id.uom_id.id,
                             'price_unit': self.cost,
                             'account_id':
                                 self.service_product_id.categ_id.property_account_income_categ_id.id,
                             })],
            }, ])
        for task in tasks:
            task.ticket_billed = True
        return {
            'effect': {
                'fadeout': 'medium',
                'message': 'Facturación creada!',
                'type': 'rainbow_man',
            }
        }

    def action_create_tasks(self):
        """Crear tarea para ticket de soporte técnico
        Esta función crea una tarea asociada con el ticket de la mesa de ayuda.
        y actualiza el campo task_ids.
        """
        task_id = self.env['project.task'].create({
            'name': self.name + '-' + self.subject,
            'project_id': self.project_id.id,
            'company_id': self.env.company.id,
            'ticket_id': self.id,
        })
        self.write({
            'task_ids': [(4, task_id.id)]
        })
        return {
            'name': 'Tasks',
            'res_model': 'project.task',
            'view_id': False,
            'res_id': task_id.id,
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_open_tasks(self):
        
        return {
            'name': 'Tasks',
            'domain': [('ticket_id', '=', self.id)],
            'res_model': 'project.task',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def action_open_invoices(self):
        
        return {
            'name': 'Invoice',
            'domain': [('ticket_id', '=', self.id)],
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def action_open_merged_tickets(self):
        """Botón inteligente de los tickets fusionados"""
        ticket_ids = self.env['support.tickets'].search(
            [('merged_ticket', '=', self.id)])
        
        helpdesk_ticket_ids = ticket_ids.mapped('display_name')
        
        help_ticket_records = self.env['help.ticket'].search(
            [('name', 'in', helpdesk_ticket_ids)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Helpdesk Ticket',
            'view_mode': 'tree,form',
            'res_model': 'help.ticket',
            'domain': [('id', 'in', help_ticket_records.ids)],
            'context': self.env.context,
        }

    def action_send_reply(self):
        """ Redactar y enviar una respuesta al cliente.
        Esta función abre una ventana para redactar y enviar una respuesta a
        el cliente. Utiliza la plantilla de correo electrónico configurada para las respuestas.
       """
        template_id = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.reply_template_id'
        )
        template_id = self.env['mail.template'].browse(int(template_id))
        if template_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'mail',
                'res_model': 'mail.compose.message',
                'view_mode': 'form',
                'target': 'new',
                'views': [[False, 'form']],
                'context': {
                    'default_model': 'help.ticket',
                    'default_res_id': self.id,
                    'default_template_id': template_id.id
                }
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'mail',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'default_model': 'help.ticket',
                'default_res_id': self.id,
            }
        }
