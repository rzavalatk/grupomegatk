from odoo import models,fields

class etiquetas(models.fields):
    _name = "tag.property"
    _description = "Etiquetas"

    name = fields.Char('Nombre', required=True)
    