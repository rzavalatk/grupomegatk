# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    es_conciliado = fields.Boolean("Conciliado")
    

class AccountMove(models.Model):
    _inherit = "account.move"
    
    es_conciliado = fields.Boolean("Conciliado")
    conciliacion_id = fields.Many2one("conicliacion.bancaria", "Conciliación")
    