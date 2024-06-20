from odoo import models, fields

class etiquetas(models.Model):
    _name = "tag.property"
    _description = "Etiquetas"

    name = fields.Char('Nombre', required=True)