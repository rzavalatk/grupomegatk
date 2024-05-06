# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
import math


_logger = logging.getLogger(__name__)

#CAMPOS EN FORMULARIO CONTACTO/VENTAS Y COMPRAS/VARIOS
class Campos_clientes(models.Model):
    _inherit = "res.partner"

    x_zonac = fields.Selection([('centro','Centro (Teg, Comayagua, Sigua)'),('norte','Norte (SPS, Pto Cortez, Ceiba)')
    	,('oriente','Oriente (Danli y El Paraiso)'),('sur','Sur (Choluteca, San Lor, Amap)')],string = 'Zona cliente')
    
    x_customer = fields.Boolean(string='Es cliente ', default=False)
    x_supplier = fields.Boolean(string='Es proveedor', default=False)
    
    #x_type_company = fields.Many2one('tpartner.company', string='Tipo de empresa')
    
    
    def create(self, vals):
        
        # Verificar existencia del NIF
        if self.env['res.partner'].search([('vat', '=', vals.get('vat'))]):
            return super(Campos_clientes, self).create(vals)
        else:
            raise ValidationError("El RTN ya existe")