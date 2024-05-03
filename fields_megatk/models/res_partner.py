# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

#CAMPOS EN FORMULARIO CONTACTO/VENTAS Y COMPRAS/VARIOS
class Campos_clientes(models.Model):
    _inherit = "res.partner"

    x_zonac = fields.Selection([('centro','Centro (Teg, Comayagua, Sigua)'),('norte','Norte (SPS, Pto Cortez, Ceiba)')
    	,('oriente','Oriente (Danli y El Paraiso)'),('sur','Sur (Choluteca, San Lor, Amap)')],string = 'Zona cliente')
    
    x_customer = fields.Boolean(string='Es cliente ', default=False)
    x_supplier = fields.Boolean(string='Es proveedor', default=False)
    
    """def create(self, vals):
        res = super(Campos_clientes, self).create(vals)
        # Verificar existencia del NIF
        if not self.env['res.partner'].search([('vat', '=', vals.get('vat'))]):
            return res
        else:
            raise ValidationError("El RTN ya existe")"""
        
    def create(self, vals):
        res = super(Campos_clientes, self).create(self, vals)
        if not vals[0]['vat']:
            raise Warning(_('Set a journal and a sequence'))
        return res