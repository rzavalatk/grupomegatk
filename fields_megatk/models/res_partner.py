# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

#CAMPOS EN FORMULARIO CONTACTO/VENTAS Y COMPRAS/VARIOS
class Campos_clientes(models.Model):
    _inherit = "res.partner"

    x_zonac = fields.Selection([('centro','Centro (Teg, Comayagua, Sigua)'),('norte','Norte (SPS, Pto Cortez, Ceiba)')
    	,('oriente','Oriente (Danli y El Paraiso)'),('sur','Sur (Choluteca, San Lor, Amap)')],string = 'Zona cliente')
    x_zona_cliente_id = fields.Many2one(
        'zona.cliente',
        string='Zona cliente (catalogo)',
        compute='_compute_x_zona_cliente_id',
        inverse='_inverse_x_zona_cliente_id',
        search='_search_x_zona_cliente_id',
        store=False,
    )
    
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

            vals['company_id'] = company_id

        return super().create(vals_list)

    def write(self, vals):
        return super().write(vals)

    @api.onchange('x_zona_cliente_id')
    def _onchange_x_zona_cliente_id(self):
        self.x_zonac = self.x_zona_cliente_id.code if self.x_zona_cliente_id else False

    @api.depends('x_zonac')
    def _compute_x_zona_cliente_id(self):
        zonas = self.env['zona.cliente'].search([])
        zonas_by_code = {zona.code: zona for zona in zonas}
        for partner in self:
            partner.x_zona_cliente_id = zonas_by_code.get(partner.x_zonac)

    def _inverse_x_zona_cliente_id(self):
        for partner in self:
            partner.x_zonac = partner.x_zona_cliente_id.code if partner.x_zona_cliente_id else False

    def _search_x_zona_cliente_id(self, operator, value):
        if operator in ('=', '!=') and not value:
            return [('x_zonac', operator, False)]

        if operator in ('=', '!='):
            zona = self.env['zona.cliente'].browse(value)
            return [('x_zonac', operator, zona.code if zona else False)]

        if operator in ('in', 'not in'):
            zona_ids = value if isinstance(value, list) else [value]
            zonas = self.env['zona.cliente'].browse(zona_ids)
            codes = [z.code for z in zonas if z.code]
            if not codes:
                return [('id', '=', 0)] if operator == 'in' else []
            return [('x_zonac', operator, codes)]

        return [('id', '=', 0)]
    
    