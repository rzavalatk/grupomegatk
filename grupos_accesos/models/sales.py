# -*- coding: utf-8 -*-
from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)

class Vendors(models.Model):
    _inherit = "sale.order"
    
    
    @api.model_create_multi
    def create(self, vals_list):
        

        ids = self.env['res.config.settings'].sudo().get_usuarios_vendedores()
        _logger.warning(ids)
        if ids is not None and self.env.user.id in ids:
                partner_id = self.env['res.partner'].browse(self.partner_id.id)
                if partner_id.user_id:
                    vals_list['user_id'] = partner_id.user_id
                    for item in vals_list:
                        if item == 'order_line':
                            for i in vals_list[item]:
                                i[2]['x_user_id'] = partner_id.user_id.id
        res = super(Vendors,self).create(vals_list)
        return res
        
class VendorsInvoices(models.Model):
    _inherit = "account.move"
    
    #@api.model
    def create(self, vals_list):
        ids = self.env['res.config.settings'].sudo().get_usuarios_vendedores()
        if ids is not None and self.env.user.id in ids:
            partner_id = self.env['res.partner'].browse(vals_list['partner_id'])
            if partner_id.user_id:
                vals_list['invoice_user_id'] = partner_id.user_id.id
                for item in vals_list:
                    if item == 'invoice_line_ids':
                        for i in vals_list[item]:
                            i[2]['x_user_id'] = partner_id.user_id.id
        res = super(VendorsInvoices,self).create(vals_list)
        return res 
    
class DefaultVendor(models.Model):
    _inherit = "res.partner"
    
    user_id = fields.Many2one("res.users","Comercial",default=lambda self : self.env.user.id)