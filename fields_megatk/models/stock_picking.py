# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

#CAMPOS EN INVENTARIO/SECCION/FORMULARIO (NUEVO O CREADO) SECCION INFERIOR PAGE OPERACIONES
class StockPickingLine(models.Model):
    _inherit = "stock.move"

    x_arancelstock = fields.Char(related = 'product_id.x_arancel', string = "Arancel")
    
