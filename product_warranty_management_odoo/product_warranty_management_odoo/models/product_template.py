# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    """Inherited product template to add fields"""
    _inherit = 'product.template'

    is_warranty_available = fields.Boolean(string="Garantia Disponible",
                                           help="Campo booleano para verificar"
                                                "la disponibilidad de la garantia")
    warranty_duration = fields.Integer(string="Duracion de la garantia (meses)",
                                       help="Duracion de garantia")
    warranty_expiry = fields.Date(string="Fecha de expiración de garantia",
                                  help="Fecha de expiración de garantia")
    warranty_coverage = fields.Many2one(
        'warranty.conditions', 
        string="La garantía cubre",
        help="Selecciona las condiciones de garantía aplicables a este producto."
    )
    not_cover_warranty = fields.Many2one(
        'warranty.conditions', 
        string="La garantía no cubre",
        help="Selecciona las condiciones que no están cubiertas por la garantía para este producto."
    )
    def get_sale_orders(self):
        """Obtiene las órdenes de venta relacionadas con este producto"""
        self.ensure_one()
        
        # Buscar líneas de orden de venta que contengan este producto
        sale_order_lines = self.env['sale.order.line'].search([
            ('product_id.product_tmpl_id', '=', self.id),
            ('state', 'in', ['sale', 'done'])
        ], order='create_date desc')
        
        # Obtener las órdenes de venta únicas
        sale_orders = sale_order_lines.mapped('order_id')
        return sale_orders