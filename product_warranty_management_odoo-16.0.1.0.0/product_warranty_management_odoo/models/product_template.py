# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
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
        
        # Obtener las órdenes de venta únicas y ordenar por fecha más reciente
        sale_orders = sale_order_lines.mapped('order_id')
        
        # Ordenar por fecha de orden (más reciente primero)
        sale_orders = sale_orders.sorted(key=lambda r: r.date_order or r.create_date, reverse=True)
        
        return sale_orders

    def print_warranty_for_current_order(self):
        """Imprimir garantía para la orden de venta actual del contexto"""
        self.ensure_one()
        sale_order_id = self._context.get('current_sale_order_id')
        
        if sale_order_id:
            # Buscar la orden específica
            sale_order = self.env['sale.order'].browse(sale_order_id)
            # Pasar la orden específica al contexto del reporte
            return self.env.ref('product_warranty_management_odoo.action_report_product_warranty').report_action(
                self, data={'sale_order_id': sale_order_id}
            )
        else:
            # Fallback al comportamiento original
            return self.env.ref('product_warranty_management_odoo.action_report_product_warranty').report_action(self)