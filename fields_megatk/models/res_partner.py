# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

#CAMPOS EN FORMULARIO CONTACTO/VENTAS Y COMPRAS/VARIOS
class Campos_clientes(models.Model):
    _inherit = "res.partner"

    x_zonac = fields.Selection([('centro','Centro (Teg, Comayagua, Sigua)'),('norte','Norte (SPS, Pto Cortez, Ceiba)')
    	,('oriente','Oriente (Danli y El Paraiso)'),('sur','Sur (Choluteca, San Lor, Amap)')],string = 'Zona cliente')
    x_zona_cliente_id = fields.Many2one('zona.cliente', string='Zona cliente (catalogo)', ondelete='restrict')
    
    x_customer = fields.Boolean(string='Es cliente ', default=False)
    x_supplier = fields.Boolean(string='Es proveedor', default=False)
    
    #x_clientes_varios = fields.Boolean(string='Clientes varios', default=False)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Condicion que busca el vat de todos los clientes y luego verifica si ya existe."""

        company_id = self.env.user.company_id.id
        for vals in vals_list:
            vat = vals.get('vat')
            if vat:
                partner = self.env['res.partner'].search(['&',('vat', '=', vat),('company_id', '=', self.env.user.company_id.id)], limit=1)
                if partner:
                    raise UserError(_("Usuario ya creado con este RTN / En caso de duplicar este contacto con un numero diferente de RTN se le multara."))

            zona_id = vals.get('x_zona_cliente_id')
            if zona_id and not vals.get('x_zonac'):
                zona = self.env['zona.cliente'].browse(zona_id)
                vals['x_zonac'] = zona.code

            zona_code = vals.get('x_zonac')
            if zona_code and not vals.get('x_zona_cliente_id'):
                zona = self.env['zona.cliente'].search([('code', '=', zona_code)], limit=1)
                if zona:
                    vals['x_zona_cliente_id'] = zona.id

            vals['company_id'] = company_id

        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if vals.get('x_zona_cliente_id') and not vals.get('x_zonac'):
            zona = self.env['zona.cliente'].browse(vals['x_zona_cliente_id'])
            vals['x_zonac'] = zona.code

        if vals.get('x_zonac') and not vals.get('x_zona_cliente_id'):
            zona = self.env['zona.cliente'].search([('code', '=', vals['x_zonac'])], limit=1)
            if zona:
                vals['x_zona_cliente_id'] = zona.id

        return super().write(vals)

    @api.onchange('x_zona_cliente_id')
    def _onchange_x_zona_cliente_id(self):
        if self.x_zona_cliente_id:
            self.x_zonac = self.x_zona_cliente_id.code
    
    