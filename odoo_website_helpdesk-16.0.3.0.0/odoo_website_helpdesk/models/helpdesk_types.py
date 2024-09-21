# -*- coding: utf-8 -*-
from odoo import fields, models


class HelpdeskTypes(models.Model):
    """Su identificador para controlar los tipos de tickets de la mesa de ayuda."""
    _name = 'helpdesk.types'
    _description = 'Helpdesk Types'

    name = fields.Char(string='Tipo', help='Tipos de tickets de ayuda')
