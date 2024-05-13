
from odoo import models, fields, api
from odoo.exceptions import Warning


class StockHistory(models.TransientModel):
    _name = 'stock.history'
    
    