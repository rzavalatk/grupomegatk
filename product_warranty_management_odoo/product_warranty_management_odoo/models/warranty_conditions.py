from odoo import models, fields

class WarrantyCondition(models.Model):
    _name = 'warranty.conditions'
    _description = 'Condiciones de garantía'

    name = fields.Char(string='Nombre', required=True)
    warranty_coverage = fields.Html(string='Cubre', required=True)
    not_cover_warranty = fields.Html(string='No Cubre', required=True)