# -*- coding: utf-8 -*-

from odoo import models, api,fields,_

class TermPament(models.Model):
    _inherit = "account.payment.term"
    
    public = fields.Boolean("Publico",default=False)
    credit = fields.Boolean("¿Es Crédito?", default=False)
    
class Facturas(models.Model):
    _inherit = "account.move"
    
    #@api.one
    def _payment_term_compute(self):
        self.payment_term_compute = self.invoice_payment_term_id.sudo().name
        
    
    payment_term_compute = fields.Char("Plazo de pago(computado)",compute=_payment_term_compute)
    
    
    
class Sales(models.Model):
    _inherit = "sale.order"
    
    def _payment_term_dynamic(self):
        payment_term = self.env['account.payment.term'].sudo().search([('active','=',True),('company_id','=',self.env.user.company_id.id)])
        vals = []
        for item in payment_term:
            if item.sudo().public:
                vals.append((item.sudo().id,item.sudo().name + "*"))
            else:
                vals.append((item.sudo().id,item.sudo().name))
        return vals
    
    payment_term = fields.Selection(selection=lambda self: self._payment_term_dynamic(),string="Plazos de pago(Editable)")
    
    
    @api.onchange('payment_term')
    def _onchange_payment_term(self):
        self.payment_term = self.payment_term
    
    #@api.model
    #def create(self,vals):
    #    if self._exist_index('payment_term', vals):
    #        del vals['payment_term']  # Eliminar la clave 'payment_term' del diccionario vals
    #    res = super(Sales, self).write(vals)
    #    return res
    
    def _exist_index(self,index,array):
        try:
            array[index]
            return True
        except :
            return False
    
    
    @api.model
    def write(self, vals):
        if self._exist_index('payment_term', vals):
            del vals['payment_term']  # Eliminar la clave 'payment_term' del diccionario vals
        res = super(Sales, self).write(vals)
        return res

 