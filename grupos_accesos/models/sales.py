# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Vendors(models.Model):
    _inherit = "sale.order"
    
    #@api.model
    def create(self,vals):
        ids = self.env['res.config.settings'].sudo().get_usuarios_vendedores()
        if ids is not None and self.env.user.id in ids:
                partner_id = self.env['res.partner'].browse(vals['partner_id'])
                if partner_id.user_id:
                    vals['user_id'] = partner_id.user_id.id
                    for item in vals:
                        if item == 'order_line':
                            for i in vals[item]:
                                i[2]['x_user_id'] = partner_id.user_id.id
        res = super(Vendors,self).create(vals)
        return res
    
class VendorsInvoices(models.Model):
    _inherit = "account.move"
    
    #@api.model
    def create(self,vals):
        ids = self.env['res.config.settings'].sudo().get_usuarios_vendedores()
        if ids is not None and self.env.user.id in ids:
            partner_id = self.env['res.partner'].browse(vals['partner_id'])
            if partner_id.user_id:
                vals['user_id'] = partner_id.user_id.id
                for item in vals:
                    if item == 'invoice_line_ids':
                        for i in vals[item]:
                            i[2]['x_user_id'] = partner_id.user_id.id
        res = super(VendorsInvoices,self).create(vals)
        return res

class DefaultVendor(models.Model):
    _inherit = "res.partner"
    
    user_id = fields.Many2one("res.users","Comercial",default=lambda self : self.env.user.id)