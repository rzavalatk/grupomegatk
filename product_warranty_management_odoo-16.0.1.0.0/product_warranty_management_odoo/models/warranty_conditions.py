from odoo import models, fields

class WarrantyCondition(models.Model):
    _name = 'warranty.conditions'
    _description = 'Condiciones de garantía'

    name = fields.Char(string='Name', required=True)
    description = fields.Char(string='Description', required=True)