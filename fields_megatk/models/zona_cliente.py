# -*- coding: utf-8 -*-
from odoo import fields, models


class ZonaCliente(models.Model):
    _name = 'zona.cliente'
    _description = 'Zona de cliente'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Codigo', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(string='Activo', default=True)

    _sql_constraints = [
        ('zona_cliente_code_unique', 'unique(code)', 'El codigo de zona ya existe.'),
    ]
