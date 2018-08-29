# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPickingLine(models.Model):
    _inherit = "stock.move"

    x_arancelstock = fields.Char(related = 'product_id.x_arancel', string = "Arancel")
    x_costo_realstock = fields.Float(related = 'product_id.x_costo_real', string = "Costo Honduras")
