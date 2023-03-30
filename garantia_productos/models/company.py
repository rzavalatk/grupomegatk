# -*- coding: utf-8 -*-

from odoo import models, api, fields


class Companies(models.Model):
    _inherit = "res.company"
    
    
    logo_garantia = fields.Binary("Imagen para Garantias")