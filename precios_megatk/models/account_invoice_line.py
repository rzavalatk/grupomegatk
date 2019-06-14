# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    precio_id = fields.Many2one("lista.precios.producto", "Lista de Precio")
    nombreproducto = fields.Char(related='product_id.name')
    
    @api.onchange("precio_id")
    def onchangedescuento(self):
        if self.precio_id:
            self.price_unit = self.precio_id.precio

    @api.onchange("price_unit", "product_id")
    def validatepreciocosto(self):
        if self.env.user.email not in ('lvilleda@printexhn.net','rzavala@megatk.com','lmoran@megatk.com','kromero@megatk.com','fvasquez@megatk.com','jmoran@meditekhn.com','msauceda@megatk.com','nfuentes@meditekhn.com'):
            for line in self:
                if line.product_id:
                    preciolista = self.env['lista.precios.producto']
                    preciodefaul = preciolista.search( [('product_id.id', '=', line.product_id.product_tmpl_id.id)])
                    
                    if self.currency_id.name == 'HNL':
                        if line.price_unit < line.product_id.list_price:
                            line.price_unit = line.product_id.list_price
                            for lista in preciodefaul:
                                porcentaje = (((line.price_unit - line.product_id.list_price)*100)/line.product_id.list_price)
                                porcentaje = round(porcentaje,2)
                                if porcentaje >= lista.descuento:
                                    line.precio_id = lista.id

    @api.model
    def create(self, values):
        line = super(AccountInvoiceLine, self).create(values)
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
        super(AccountInvoiceLine, self).write(values)
        for line in self:
            preciolista = self.env['lista.precios.producto']
            preciodefaul = preciolista.search( [('product_id.id', '=', line.product_id.product_tmpl_id.id)])
            for lista in preciodefaul:
                porcentaje = 0
                porcentaje = (((line.price_unit - line.product_id.list_price)*100)/line.product_id.list_price)
                porcentaje = round(porcentaje,2)
                if porcentaje >= lista.descuento:
                    values['precio_id'] = lista.id
        return super(AccountInvoiceLine, self).write(values)

   