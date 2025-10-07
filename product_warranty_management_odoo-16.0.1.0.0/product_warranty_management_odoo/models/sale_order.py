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
from dateutil.relativedelta import relativedelta
from odoo import fields, models


class SaleOrder(models.Model):
    """Inherited sale order to super functions to add additional
    functionalities"""
    _inherit = 'sale.order'

    is_warranty_check = fields.Boolean(string='Verificación de garantía',
                                       help='Marque esta casilla si el artículo tiene'
                                            ' garantía.')

    def action_confirm(self):
        result = super(SaleOrder, self).action_confirm()
        
        # Verificar si alguna línea tiene productos con garantía
        has_warranty_products = any(
            line.product_id.is_warranty_available 
            for line in self.order_line
            if line.product_id
        )
        
        self.is_warranty_check = has_warranty_products
        
        return result

    def action_open_smart_tab(self):
        """ To open warranty smart tab"""
        domain = [
            ('id', 'in', self.order_line.mapped('product_id.product_tmpl_id.id')),
            ('is_warranty_available', '=', True),
        ]
        
        products_with_warranty = self.env['product.template'].search(domain)
        
        for product in products_with_warranty:
            if self.date_order and product.warranty_duration:
                warranty_expiry_date = self.date_order + relativedelta(
                    months=product.warranty_duration)
                product.write({'warranty_expiry': warranty_expiry_date})
        
        # Usar vistas estándar de product.template en lugar de personalizadas
        return {
            'type': 'ir.actions.act_window',
            'name': 'Detalles de Garantía',
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'views': [
                (False, 'tree'),
                (False, 'form')
            ],
            'domain': domain,
            'context': {
                'create': False, 
                'current_sale_order_id': self.id,
                'search_default_is_warranty_available': 1  # Filtrar por garantía disponible
            },
            'target': 'current',
        }
