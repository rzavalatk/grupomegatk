from odoo import models, fields

class estate_property(models.Model):
    _name = "estate.property"
    _description = "description of properties"
    
    name = fields.Char(string="Nombre", required=True)
    description = fields.Text(string="Descripcion")
    price = fields.Float(string="Precio", required=True)
    sold = fields.Boolean(string="Vendido")
    image = fields.Binary(string="Imagen")
    bedrooms = fields.Integer(string="Habitaciones", default=1)
    bathrooms = fields.Integer(string="Banios", default=1)
    living_area = fields.Integer(string="Area de vivienda", default=1)