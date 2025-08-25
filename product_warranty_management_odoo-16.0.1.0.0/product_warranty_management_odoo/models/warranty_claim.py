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


class WarrantyClaim(models.Model):
    """ Warranty claim class to add fields for warranty claim"""
    _name = 'warranty.claim'
    _rec_name = "sale_order_id"
    _description = 'Warranty Claim'

    customer_id = fields.Many2one('res.partner',
                                  string='Nombre del cliente',
                                  help="seleccionar el cliente",
                                  required=True)
    sale_order_id = fields.Many2one('sale.order',
                                    help="seleccionar la orden de venta",
                                    string='orden de venta')
    product_id = fields.Many2one('product.product',
                                 string='Producto',
                                 help="Seleccionar el producto",
                                 required=True)
    partner_id = fields.Many2one('res.users', string='Usuario',
                                 help="Seleccionar el usuario",
                                 default=lambda self: self.env.user)
    state = fields.Selection(
        [('draft', 'Borrador'), ('approved', 'Aprobado'),
         ('rejected', 'Rechazado')], default='draft', String="Status",
        help="Seleccionar el estado del reclamo")
    product_expiry_date = fields.Date(
        string='Fecha de caducidad de garantia', help="Obtener la fecha de vencimiento de la garantia",
        related='product_id.product_tmpl_id.warranty_expiry',
        store=True, readonly=True)

    def change_status_approved(self):
        """ Function to change the status of the claim to approved"""
        self.state = 'approved'

    def change_status_rejected(self):
        """ Function to change the status of the claim to rejected"""
        self.state = 'rejected'
