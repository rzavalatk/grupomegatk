# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPickingLine(models.Model):
    _inherit = "stock.move"

    x_series = fields.Text(related = 'sale_line_id.x_series', string = "Series" )