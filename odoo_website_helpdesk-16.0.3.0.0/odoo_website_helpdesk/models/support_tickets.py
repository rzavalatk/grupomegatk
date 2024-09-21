# -*- coding: utf-8 -*-
from odoo import fields, models


class SupportTickets(models.Model):
    """Creando un modelo onetoMany para manejar el ticket de fusión"""
    _name = 'support.tickets'
    _description = 'Support Tickets'

    subject = fields.Char(string='Asunto de fusión',)
    display_name = fields.Char(string='Nombre para mostrar',
                               help='Nombre para mostrar para los tickets fusionados',)
    description = fields.Char(string='Descripción de fusion',
                              help='Description of the tickets')
    support_ticket_id = fields.Many2one('merge.tickets',
                                        string='Tickets',)
    merged_ticket = fields.Integer(string='ID de Ticket fusionado',)
