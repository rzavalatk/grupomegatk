# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    precio_id = fields.Many2one("lista.precios.producto", "Lista de Precio", required=True)

    @api.onchange("precio_id")
    def onchangedescuento(self):
        if self.precio_id:
            self.price_unit = self.precio_id.precio

    @api.onchange("price_unit", "product_id")
    def validatepreciocosto(self):
        if self.env.user.email not in ('rzavala@megatk.com','jmadrid@megatk.com','lmoran@megatk.com','kromero@megatk.com','fvasquez@megatk.com','jmoran@meditekhn.com','msauceda@megatk.com','nfuentes@meditekhn.com'):
            if self.invoice_id.type in ('out_invoice', 'out_refund'):
            	if self.product_id:
    	            if self.price_unit < self.product_id.list_price:
    	                raise Warning(_('No esta permitido establecer precios de ventas por debajo del precio de lista'))
    	            if self.price_unit < self.precio_id.precio:
    	                raise Warning(_('No esta permitido establecer precios de ventas por debajo del precio mayorista'))


