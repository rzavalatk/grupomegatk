# -*- coding:utf-8 -*-
from odoo import fields, models


class ConnectionApi(models.Model):
    """Esta clase se utiliza para crear un modelo api en el que podemos crear registros con modelos y campos, y además podemos especificar métodos."""
    _name = 'connection.api'
    _rec_name = 'model_id'

    model_id = fields.Many2one('ir.model', string="Model",
                               domain="[('transient', '=', False)]",)
    is_get = fields.Boolean(string='GET',)
    is_post = fields.Boolean(string='POST',)
    is_put = fields.Boolean(string='PUT',)
    is_delete = fields.Boolean(string='DELETE',)
