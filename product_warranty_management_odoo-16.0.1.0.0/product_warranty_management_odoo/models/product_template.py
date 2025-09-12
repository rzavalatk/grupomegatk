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
    warranty_condition_compliance = fields.Many2one(
        'warranty.conditions', 
        string="Condiciones de Garantía",
        help="Selecciona las condiciones de garantía aplicables a este producto."
    )