# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectTask(models.Model):
    """
    Esta clase extiende el modelo 'project.task' en Odoo para agregar un campo personalizado
     llamado 'ticket_billed' y 'ticket_id'.
     ticket_billed: campo booleano que indica si el billete tiene
     sido facturado o no.
     ticket_id: un campo many2One para vincular la tarea
    con un ticket de ayuda
    """
    _inherit = 'project.task'

    ticket_billed = fields.Boolean(string='Facturado',)
    ticket_id = fields.Many2one('help.ticket', string='Ticket',)
