# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class Campos_clientes(models.Model):
    _inherit = "res.partner"

    cedula = fields.Char('Cedula')
    int_morat = fields.Float(string='Interés Moratorio',default=2)
    int_corrint = fields.Float(string='Interés Corriente',)

# class grupomegatk/campos_lenka(models.Model):
#     _name = 'grupomegatk/campos_lenka.grupomegatk/campos_lenka'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100