from odoo import models,fields

class state_property_type (models.Model):
    _name = "type.property"
    _description = "Tipo_propiedades"

    name = fields.Char('Nombre', required=True)
