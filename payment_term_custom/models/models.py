# -*- coding: utf-8 -*-

from odoo import models, api,fields


class TermPament(models.Model):
    _inherit = "account.payment.term"
    
    public = fields.Boolean("Publico",default=False)
    
class Facturas(models.Model):
    _inherit = "account.invoice"
    
    @api.one
    def _payment_term_compute(self):
        self.payment_term_compute = self.payment_term_id.sudo().name
        
    
    payment_term_compute = fields.Char("Plazo de pago(computado)",compute=_payment_term_compute)