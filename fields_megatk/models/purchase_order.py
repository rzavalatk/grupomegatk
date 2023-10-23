# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Purchase(models.Model):
    _inherit = "purchase.order"

    x_enviar = fields.Text("Enviar a")
    etapa_orden = fields.Selection([('orden_p_s','Orden Pendiente de Solicitud'),('orden_p_t','Orden Pendiente de Transferencia'),('orden_p_d','Orden Pendiente de Despacho'),('orden_t','Orden en Tránsito'),('orden_a','Producto en Aduana'),('orden_i','Ingresó a Bodega'),('orden_l','Listo')],string='Etapa de orden', default='orden_p_s', required=True,)
        
class PurchaseLine(models.Model):
    _inherit = "purchase.order.line"

    x_codigo = fields.Char(related='product_id.barcode', string="Codigo")
