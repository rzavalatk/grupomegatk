
from odoo import models, fields, api
from odoo.exceptions import Warning


class StockHistory(models.TransientModel):
    _name = 'stock.history'
    
    movimiento_ids = fields.Many2many('stock.quant', string='movimiento')
    
    print("Hola")