# -*- coding:utf-8 -*-


import uuid
from odoo import fields, models


class UserLogin(models.Model):
    """Esta clase se utiliza para heredar usuarios y añadir la generación de claves api"""
    _inherit = 'res.users'

    api_key = fields.Char(string="API Key", readonly=True,
                          help="Api key Generada con el metodo odoo_connect del main de los controllers")

    def generate_api(self, username):
        """Esta función se utiliza para generar api-key para cada usuario"""
        users = self.env['res.users'].sudo().search([('login', '=', username)])
        if not users.api_key:
            users.api_key = str(uuid.uuid4())
            key = users.api_key
        else:
            key = users.api_key
        return key
