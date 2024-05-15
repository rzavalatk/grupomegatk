
from odoo import models, fields, api
from odoo.exceptions import Warning


class StockHistory(models.TransientModel):
    _name = 'stock.history'
    
    movimiento_ids = fields.Many2one('stock.quant', string='movimiento')
    name = fields.Char('name')