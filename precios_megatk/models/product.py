# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Product(models.Model):
    _inherit = "product.template"

    # x_comisiones = fields.One2many('lista.precios.producto', 'product_id')
    x_comisiones = fields.One2many('lista.precios.megatk.line', 'product_id')

    @api.onchange('list_price')
    def _onchange_precio_lista(self):
        for list_precio in self.x_comisiones:
            list_precio.write({'precio_publico': self.list_price, 'precio_descuento': self.list_price + ((self.list_price*list_precio.x_descuento)/100)})

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.onchange('lst_price')
    def _onchange_precio_lista(self):
        for list_precio in self.product_tmpl_id.x_comisiones:
            list_precio.write({'precio_publico': self.lst_price, 'precio_descuento': self.lst_price + ((self.lst_price*list_precio.x_descuento)/100)})

