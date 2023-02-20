# -*- coding: utf-8 -*-

from odoo import models, api,fields,_
from odoo.exceptions import Warning


class TermPament(models.Model):
    _inherit = "account.payment.term"
    
    public = fields.Boolean("Publico",default=False)
    
class Facturas(models.Model):
    _inherit = "account.invoice"
    
    @api.one
    def _payment_term_compute(self):
        self.payment_term_compute = self.payment_term_id.sudo().name
        
    
    payment_term_compute = fields.Char("Plazo de pago(computado)",compute=_payment_term_compute)
    
    
    @api.model
    def create(self,vals):
        try:
            payment_term = self.env['account.payment.term'].browse(vals['payment_term_id'])
            payment_term.name
            res = super(Facturas,self).create(vals)
            return res
        except :
            raise Warning(_('Acceso Denegado: Esta usuario no tiene permiso para autorizar créditos, contacte a los(as) encargados(as) de Administración o Gerencia para que se autorice su crédito o cambie el "Plazo de pago" a "contado"'))

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
        self.payment_term_id = self.payment_term
    
    @api.model
    def create(self,vals):
        vals['payment_term_id'] = vals['payment_term']
        vals['payment_term'] = None
        res = super(Sales,self).create(vals)
        return res
    
    def _exist_index(self,index,array):
        try:
            array[index]
            return True
        except :
            return False
    
    
    @api.model
    def write(self,vals):
        if self._exist_index('payment_term',vals):
            vals['payment_term_id'] = vals['payment_term']
            vals['payment_term'] = None
        res = super(Sales,self).write(vals)
        return res
 