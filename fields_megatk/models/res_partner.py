# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


#CAMPOS EN FORMULARIO CONTACTO/VENTAS Y COMPRAS/VARIOS
class Campos_clientes(models.Model):
    _inherit = "res.partner"
    
    encontrado = False

    x_zonac = fields.Selection([('centro','Centro (Teg, Comayagua, Sigua)'),('norte','Norte (SPS, Pto Cortez, Ceiba)')
    	,('oriente','Oriente (Danli y El Paraiso)'),('sur','Sur (Choluteca, San Lor, Amap)')],string = 'Zona cliente')
    
    #clientes_varios = fields.Boolean(string='Clientes varios', default=False)
    x_customer = fields.Boolean(string='Es cliente ', default=False)
    x_supplier = fields.Boolean(string='Es proveedor', default=False)
    
    @api.onchange("vat")
    def onchangevay(self):         
        
        partner = self.env['res.partner'].search([('vat', '=', self.vat)])
        
        if partner:
            self.encontrado = True
    
    
    @api.model_create_multi
    def create(self, vals_list):
        """Condicion que busca el vat de todos los clientes y luego verifica si ya existe."""
  
        _logger.warning("Nombre del contacto encontrado: " + self.encontrado)
        
        if self.encontrado:
            raise UserError(_("Usuario ya creado con este RTN / En caso de duplicar este contacto con un numero diferente de RTN se le multara."))
        
        return super().create(vals_list)