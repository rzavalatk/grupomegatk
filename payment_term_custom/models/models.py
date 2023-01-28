# -*- coding: utf-8 -*-

from odoo import models, api,fields


class TermPament(models.Model):
    _inherit = "account.payment.term"
    
    public = fields.Boolean("Publico",default=False)