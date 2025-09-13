from odoo import models, fields

class WarrantyCondition(models.Model):
    _name = 'warranty.conditions'
    _description = 'Condiciones de garantía'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Char(string='Descripción', required=True)