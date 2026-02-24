# -*- coding: utf-8 -*-

from odoo import models, api,fields
from odoo.exceptions import UserError


class Users(models.Model):
    _inherit = "res.users"
    
    vendor=fields.Boolean("Vendedor")
    

class Leads(models.Model):
    _inherit = "crm.lead"
    
    @api.model_create_multi
    def unlink(self):
        if self.env.user.vendor:
            raise UserError("No tiene permisos para realizar esta acción. Consulte con su Administrador.")
        else:
            return super(Leads, self).unlink()
        
class ProductNoCreate(models.Model):
    _inherit = "product.product"
    
    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.vendor:
            raise UserError("No tiene permisos para realizar esta acción. Consulte con su Administrador.")
        else:
            return super(ProductNoCreate, self).create(vals_list)
        
    """@api.model_create_multi
    def write(self, vals):
        if self.env.user.vendor:
            raise UserError("No tiene permisos para realizar esta acción. Consulte con su Administrador.")
        else:
            return super(ProductNoCreate, self).write(vals)"""
        
class ProductTemplateNoCreate(models.Model):
    _inherit = "product.template"
    
    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.vendor:
            raise UserError("No tiene permisos para realizar esta acción. Consulte con su Administrador.")
        else:
            return super(ProductTemplateNoCreate, self).create(vals_list)
        
    """@api.model_create_multi
    def write(self, vals):
        if self.env.user.vendor:
            raise UserError("No tiene permisos para realizar esta acción. Consulte con su Administrador.")
        else:
            return super(ProductTemplateNoCreate, self).write(vals)"""
    