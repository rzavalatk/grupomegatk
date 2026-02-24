# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ot_observaciones = fields.Text(string='Observaciones',)
    ot_arte = fields.Boolean(string='Entrego Arte',)
    ot_insumos = fields.Boolean(string='Trajo los Insumos',)
    ot_oc = fields.Boolean(string='OC',)
    ot_cort = fields.Boolean(string='Cort',)
    ot_arte_impresa = fields.Boolean(string='Vio Arte Impresa',)
    ot_ojetes = fields.Boolean(string='Lleva Ojetes',)
    ot_instalacion = fields.Boolean(string='Con Instalacion',)