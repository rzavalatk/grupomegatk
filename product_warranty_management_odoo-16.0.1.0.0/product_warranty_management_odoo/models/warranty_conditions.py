from odoo import models, fields

class WarrantyCondition(models.Model):
    _name = 'warranty.conditions'
    _description = 'Condiciones de garantía'

    name = fields.Char(string='Nombre', required=True)
    warranty_coverage = fields.Char(string='Cubre', required=True)
    not_cover_warranty = fields.Char(string='No Cubre', required=True)