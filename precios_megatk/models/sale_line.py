# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class Saleline(models.Model):
    _inherit = 'sale.order.line'

    precio_id = fields.Many2one("lista.precios.producto", "Lista de Precio")
   
    @api.multi
    def _prepare_invoice_line(self, qty):
        values = super(Saleline, self)._prepare_invoice_line(qty)
        values['precio_id'] = self.precio_id.id
        return values


    @api.onchange("precio_id")
    def onchangedescuento(self):
        if self.precio_id:
            self.price_unit = self.precio_id.precio

    @api.onchange("price_unit", "product_id")
    def validatepreciocosto(self):
        if self.env.user.email not in ('rzavala@megatk.com','jmadrid@megatk.com','lmoran@megatk.com','kromero@megatk.com','fvasquez@megatk.com','jmoran@meditekhn.com','msauceda@megatk.com','nfuentes@meditekhn.com'):
            for line in self:
                if line.product_id:
                    # preciolista = self.env['lista.precios.producto']
                    # preciodefaul = preciolista.search( [('product_id.id', '=', line.product_id.id)])
                    # for x in preciodefaul:
                    #     for y in x.name:
                    #         if y.name == self.order_id.pricelist_id.name:
                    #             line.precio_id = x.id
                                    
                    if line.price_unit < line.product_id.list_price:
                        line.price_unit = line.product_id.list_price
                    if line.price_unit < self.precio_id.precio:
                        line.price_unit = self.precio_id.precio

