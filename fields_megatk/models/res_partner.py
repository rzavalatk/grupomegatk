# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

#CAMPOS EN FORMULARIO CONTACTO/VENTAS Y COMPRAS/VARIOS
class Campos_clientes(models.Model):
    _inherit = "res.partner"

    x_zonac = fields.Selection([('centro','Centro (Teg, Comayagua, Sigua)'),('norte','Norte (SPS, Pto Cortez, Ceiba)')
    	,('oriente','Oriente (Danli y El Paraiso)'),('sur','Sur (Choluteca, San Lor, Amap)')],string = 'Zona cliente')
    
    x_customer = fields.Boolean(string='Es cliente ', default=False)
    x_supplier = fields.Boolean(string='Es proveedor', default=False)
    
    #x_clientes_varios = fields.Boolean(string='Clientes varios', default=False)
    
    """@api.model_create_multi
    def create(self, vals_list):
        #Condicion que busca el vat de todos los clientes y luego verifica si ya existe.
        
        partner = self.env['res.partner'].search([('vat', '=', self.vat)])
        
        if partner:
            raise UserError(_("Usuario ya creado con este RTN / En caso de duplicar este contacto con un numero diferente de RTN se le multara."))
        
        return super().create(vals_list)"""