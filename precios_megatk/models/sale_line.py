# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Saleline(models.Model):
    _inherit = 'sale.order.line'

    precio_id = fields.Many2one("lista.precios.producto", "Lista del Precio")
    precio_ids = fields.Many2one("lista.precios.producto", "Lista del Precios (editable)")
    pricelist_id = fields.Many2one(related='order_id.pricelist_id', string='Field Label', )
    nombreproducto = fields.Integer(related='product_id.product_tmpl_id.id', string="nombre producto")
    lista_precio = fields.Char("Lista de Precio",)
   
    def _prepare_invoice_line(self, **optional_values):
        values = super(Saleline, self)._prepare_invoice_line(**optional_values)
        values['precio_id'] = self.precio_id.id
        values['lista_precio'] = self.lista_precio
        return values
    
    @api.onchange("precio_id")
    def onchangedescuento(self):
        if self.precio_id:
            self.price_unit = self.precio_id.precio
            self.lista_precio = self.precio_id.name.name
    

    #codigo original, quitar comentarios al arreglar el problema con el dominio en precio_id
    @api.onchange("product_id")
    def validatepreciocosto(self):
        if self.env.user.email not in ('dzuniga@megatk.com', 'lmoran@megatk.com', 'dvasquez@megatk.com', 'yalvarado@megatk.com', 'jmoran@meditekhn.com', 'msauceda@megatk.com', 'nfuentes@meditekhn.com'):
            for line in self:
                if line.product_id:
                    preciolista = self.env['lista.precios.producto']
                    preciodefaul = preciolista.search( [('product_id.id', '=', line.product_id.product_tmpl_id.id)])
                    for x in preciodefaul:
                        for y in x.name:
                            if y.name == self.order_id.pricelist_id.name:
                                self.precio_id = x.id
                    if self.pricelist_id.currency_id.name == 'HNL':
                        if line.price_unit < line.product_id.list_price:
                            line.price_unit = line.product_id.list_price
                            for lista in preciodefaul:
                                porcentaje = (((line.price_unit - line.product_id.list_price)*100)/line.product_id.list_price)
                                porcentaje = round(porcentaje,2)
                                if porcentaje >= lista.descuento:
                                    line.precio_id = lista.id
                        
                                    
                               
    @api.onchange('price_unit', 'product_id')
    def _onchange_price_unit_product_id(self):
        
        
        allowed_emails = [
            'dzuniga@megatk.com', 'lmoran@megatk.com', 'dvasquez@megatk.com',
            'yalvarado@megatk.com', 'jmoran@meditekhn.com', 'msauceda@megatk.com', 'nfuentes@meditekhn.com'
        ]
        
        if self.env.user.email not in allowed_emails:
            for line in self:
                if line.product_id:
                    preciolista = self.env['lista.precios.producto']
                    preciodefaul = preciolista.search([('product_id', '=', line.product_id.product_tmpl_id.id)])

                    if self.order_id.currency_id.name == 'HNL':
                        if line.price_unit < line.product_id.list_price:
                            line.price_unit = line.product_id.list_price
                            for lista in preciodefaul:
                                porcentaje = (((line.price_unit - line.product_id.list_price) * 100) /
                                                line.product_id.list_price)
                                porcentaje = round(porcentaje, 2)
                                if porcentaje >= lista.descuento:
                                    line.precio_id = lista.id
    @api.model_create_multi 
    def create(self, values):
        lines = super(Saleline, self).create(values)
        preciolista = self.env['lista.precios.producto']
        
        for line in lines:
            preciodefaul = preciolista.search([('product_id.id', '=', line.product_id.product_tmpl_id.id)])
            
            best_discount = -1
            best_price_id = None
            
            for lista in preciodefaul:
                porcentaje = (((line.price_unit - line.product_id.list_price) * 100) / line.product_id.list_price)
                porcentaje = round(porcentaje, 2)
                if porcentaje >= lista.descuento:
                    if lista.descuento > best_discount:
                        best_discount = lista.descuento
                        best_price_id = lista.id
            
            if best_price_id:
                line.precio_id = best_price_id
            
        return lines

    def write(self, values):
        super(Saleline, self).write(values)
        for line in self:
            preciolista = self.env['lista.precios.producto']
            preciodefaul = preciolista.search( [('product_id.id', '=', line.product_id.product_tmpl_id.id)])
            for lista in preciodefaul:
                porcentaje = 0
                porcentaje = (((line.price_unit - line.product_id.list_price)*100)/line.product_id.list_price)
                porcentaje = round(porcentaje,2)
                if porcentaje >= lista.descuento:
                    values['precio_id'] = lista.id
        return super(Saleline, self).write(values)
    
   
