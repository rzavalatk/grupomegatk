# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class Saleline(models.Model):
    _inherit = 'sale.order.line'

    precio_id = fields.Many2one("lista.precios.producto", "Lista de Precio")
    pricelist_id = fields.Many2one(related='order_id.pricelist_id', string='Field Label', )
    nombreproducto = fields.Integer(related='product_id.product_tmpl_id.id')

    @api.multi
    def _prepare_invoice_line(self, qty):
        values = super(Saleline, self)._prepare_invoice_line(qty)
        values['precio_id'] = self.precio_id.id
        return values

    @api.onchange("precio_id")
    def onchangedescuento(self):
        if self.precio_id:
            self.price_unit = self.precio_id.precio

    @api.onchange("product_id")
    def validatepreciocosto(self):
        if self.env.user.email not in ('leon.89.25@gmail.com','lvilleda@printexhn.net','lmoran@megatk.com','kromero@megatk.com','fvasquez@megatk.com','jmoran@meditekhn.com','msauceda@megatk.com','nfuentes@meditekhn.com'):
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
                                    
    @api.onchange("price_unit")
    def validatepreciounit(self):
        if self.env.user.email not in ('leon.89.25@gmail.com','lvilleda@printexhn.net','rzavala@megatk.com','lmoran@megatk.com','kromero@megatk.com','fvasquez@megatk.com','jmoran@meditekhn.com','msauceda@megatk.com','nfuentes@meditekhn.com'):
            for line in self:
                if line.product_id:
                    preciolista = self.env['lista.precios.producto']
                    preciodefaul = preciolista.search( [('product_id.id', '=', line.product_id.product_tmpl_id.id)])
                    if self.pricelist_id.currency_id.name == 'HNL':
                        if line.price_unit < line.product_id.list_price:
                            line.price_unit = line.product_id.list_price
                            for lista in preciodefaul:
                                porcentaje = (((line.price_unit - line.product_id.list_price)*100)/line.product_id.list_price)
                                porcentaje = round(porcentaje,2)
                                if porcentaje >= lista.descuento:
                                    line.precio_id = lista.id

    @api.model
    def create(self, values):
        line = super(Saleline, self).create(values)
        preciolista = self.env['lista.precios.producto']
        preciodefaul = preciolista.search( [('product_id.id', '=', line.product_id.product_tmpl_id.id)])
        for lista in preciodefaul:
            porcentaje= (((line.price_unit - line.product_id.list_price)*100)/line.product_id.list_price)
            porcentaje=round(porcentaje,2)
            if porcentaje >= lista.descuento:
                line.precio_id = lista.id
        return line
    
    @api.multi
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

   