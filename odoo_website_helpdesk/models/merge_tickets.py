# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MergeTickets(models.Model):
    """
       Esta clase permite a los usuarios fusionar tickets de soporte o crear otros nuevos.
    Proporciona funcionalidad para consolidar información de múltiples tickets.
    """
    _name = 'merge.tickets'
    _description = 'Merge Tickets'
    _rec_name = 'support_ticket_id'

    user_id = fields.Many2one('res.partner',
                              string='Usuario responsable',
                              help='Nombre del usuario responsable',
                              default=lambda self: self.env.user.partner_id.id)
    support_team_id = fields.Many2one('help.team',
                                      string='Equipo de soporte',
                                      help='Nombre del equipo de soporte',)
    customer_id = fields.Many2one('res.partner',
                                  string='Cliente',
                                  help='Nombre del cliente',
                                  )
    support_ticket_id = fields.Many2one('help.ticket',
                                        string='Ticket de soporte',)
    new_ticket = fields.Boolean(string='¿Crear nuevo ticket?',)
    subject = fields.Char(string='Asunto', help='Asunto del Ticket')
    merge_reason = fields.Char(string='Razon de Fusion', help='Razon de Fusion')
    support_ticket_ids = fields.One2many('support.tickets',
                                         'support_ticket_id',
                                         string='Tickets de soporte',
                                         helps='Tickets fusionados')
    active = fields.Boolean(string='desactivar registro',)

    def default_get(self, fields_list):
        
        defaults = super().default_get(fields_list)
        active_ids = self._context.get('active_ids', [])
        selected_tickets = self.env['help.ticket'].browse(active_ids)
        customer_ids = selected_tickets.mapped('customer_id')
        subjects = selected_tickets.mapped('subject')
        display_names = selected_tickets.mapped('display_name')
        helpdesk_team = selected_tickets.mapped('team_id')
        descriptions = selected_tickets.mapped('description')
        
        if len(customer_ids):
            defaults.update({
                'customer_id': customer_ids[0].id,
                'support_team_id': helpdesk_team,

                'support_ticket_ids': [(0, 0, {
                    'subject': subject,
                    'display_name': display_name,
                    'description': description,

                }) for subject, display_name, description in
                                       zip(subjects, display_names,
                                           descriptions)]
            })
        return defaults

    def action_merge_ticket(self):
        
        if self.new_ticket:
            description = "\n\n".join(
                f"{ticket.subject}\n{'-' * len(ticket.subject)}\n"
                f"{ticket.description}"
                for ticket in self.support_ticket_ids
            )
            self.env['help.ticket'].create({
                'subject': self.subject,
                'description': description,
                'customer_id': self.customer_id.id,
                'team_id': self.support_team_id.id,
            })
        else:
            if len(self.support_ticket_ids):
                description = "\n\n".join(
                    f"{ticket.subject}\n{'-' * len(ticket.subject)}\n"
                    f"{ticket.description}"
                    for ticket in self.support_ticket_ids
                )
                
                self.support_ticket_id.write({
                    'description': description,
                    'merge_ticket_invisible': True,
                    'merge_count': len(self.support_ticket_ids),
                })

    @api.onchange('support_ticket_id')
    def _onchange_support_ticket_id(self):
        
        self.support_ticket_ids.write({
            'merged_ticket': self.support_ticket_id
        })
