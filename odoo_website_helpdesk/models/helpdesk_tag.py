# -*- coding: utf-8 -*-
from odoo import fields, models


class HelpdeskTag(models.Model):
    """ Su identificador para controlar las etiquetas de los tickets del servicio de asistencia técnica."""
    _name = 'helpdesk.tag'
    _description = 'Helpdesk Tag'

    name = fields.Char(string='Etiqueta', help='Elige las etiquetas')
