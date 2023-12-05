# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    precio_id = fields.Many2one("lista.precios.producto", "Lista de Precio")
    precio_ids = fields.Many2one("lista.precios.producto", "Lista de Precio")
    nombreproducto = fields.Char(related='product_id.name')
    lista_precio = fields.Char("Lista de Precio", readonly=True,)
    
    @api.onchange('precio_id')
    def _onchange_precio_id(self):
        if self.precio_id:
            self.price_unit = self.precio_id.precio
            self.lista_precio = self.precio_id.name.name

    @api.onchange('price_unit', 'product_id')
    def _onchange_price_unit_product_id(self):
        if self.move_id.move_type == 'out_invoice':
            allowed_emails = [
                'lvilleda@printexhn.net', 'rzavala@megatk.com', 'lmoran@megatk.com', 'kromero@megatk.com',
                'eduron@megatk.com', 'jmoran@meditekhn.com', 'msauceda@megatk.com', 'nfuentes@meditekhn.com'
            ]
            if self.env.user.email not in allowed_emails:
                for line in self:
                    if line.product_id:
                        preciolista = self.env['lista.precios.producto']
                        preciodefaul = preciolista.search([('product_id', '=', line.product_id.product_tmpl_id.id)])

                        if self.move_id.currency_id.name == 'HNL':
                            if line.price_unit < line.product_id.list_price:
                                line.price_unit = line.product_id.list_price
                                for lista in preciodefaul:
                                    porcentaje = (((line.price_unit - line.product_id.list_price) * 100) /
                                                  line.product_id.list_price)
                                    porcentaje = round(porcentaje, 2)
                                    if porcentaje >= lista.descuento:
                                        line.precio_id = lista.id
    
    def create(self, values):
        line = super(AccountMoveLine, self).create(values)
        preciolista = self.env['lista.precios.producto']
        preciodefaul = preciolista.search([('product_id', '=', line.product_id.product_tmpl_id.id)])
        for lista in preciodefaul:
            porcentaje = (((line.price_unit - line.product_id.list_price) * 100) / line.product_id.list_price)
            porcentaje = round(porcentaje, 2)
            if porcentaje >= lista.descuento:
                line.precio_id = lista.id
        return line
    
    
    def write(self, values):
        #super(AccountMoveLine, self).write(values)
        for line in self:
            preciolista = self.env['lista.precios.producto']
            preciodefaul = preciolista.search([('product_id', '=', line.product_id.product_tmpl_id.id)])
            for lista in preciodefaul:
                porcentaje = (((line.price_unit - line.product_id.list_price) * 100) / line.product_id.list_price)
                porcentaje = round(porcentaje, 2)
                #if porcentaje >= lista.descuento:
                #    values['precio_id'] = int(lista.id)
        return super(AccountMoveLine, self).write(values)


   