# -*- coding: utf-8 -*-

from odoo import models, api,fields
from odoo.exceptions import Warning


class Users(models.Model):
    _inherit = "res.users"
    
    vendor=fields.Boolean("Vendedor")
    

class Leads(models.Model):
    _inherit = "crm.lead"
    
    #@api.multi
    def unlink(self):
        if self.env.user.vendor:
            raise Warning("No tiene permisos para realizar esta acción. Consulte con su Administrador.")
        else:
            return super(Leads, self).unlink()
    