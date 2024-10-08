# -*- coding: utf-8 -*-
from odoo import fields, models


class HelpdeskCategories(models.Model):
    """Esta clase representa las categorías de soporte técnico y proporciona información
    sobre las diferentes categorías que se pueden asignar a los elementos del servicio de asistencia técnica.
   """
    _name = 'helpdesk.categories'
    _description = 'Helpdesk Categories'

    name = fields.Char(string='Nombre', help='Nombre de la categoria')
    sequence = fields.Integer(string='Secuencia', default=0,
                              help='Secuencia de la categoria')
