# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    """Para la elaboración de los medicamentos utilizados en la clínica dental."""
    _inherit = 'product.template'

    is_medicine = fields.Boolean('¿Es medicina?',
                                 help="¿Es un medicamento?")
    generic_name = fields.Char(string="Nombre",
                               required=True,
                               help="nombre del medicamento")
    dosage_strength = fields.Integer(string="Fuerza de dosificación",
                                     required=True,
                                     help="Dosis del medicamento")
