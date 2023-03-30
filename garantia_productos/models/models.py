# -*- coding: utf-8 -*-

from odoo import models, api, fields


class MoveLine(models.Model):
    _inherit = "stock.move.line"
    
    
    x_serie = fields.Char("No. Serie")
    

class Move(models.Model):
    _inherit = "stock.move"
    
    
    x_period = fields.Char("Tiempo Garantía")


class Stock(models.Model):
    _inherit = "stock.picking"
        
        
    def letter_of_warranty(self):
        return self.env.ref('garantia_productos.stock_picking_letter_warrenty_custom').report_action(self)