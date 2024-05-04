# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo.exceptions import Warning
import requests


class TypePartnerCompany(models.Model):
    _name = 'type.partner.company'
    _description = 'Tipos de empresas para clientes'

    name = fields.Char(string='Nombre', required=True, copy=False,)
    compañia = fields.Many2one('res.company', string='Compañia', required=True)
   