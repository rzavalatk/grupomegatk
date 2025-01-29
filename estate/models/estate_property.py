from odoo import models, fields

class estate_property(models.Model):
    _name = "estate.property"
    _description = "description of properties"
    
    name = fields.Char(string="Nombre", required=True)
    description = fields.Text(string="Descripcion")
    postcode = fields.Char(string="Codigo postal")
    fecha_exist = fields.Date(string="En venta desde")
    price_exp = fields.Float(string="Precio Esperado", required=True)
    price_sell = fields.Float(string="Precio de venta", readonly=True)
    image = fields.Binary(string="Imagen")
    bedrooms = fields.Integer(string="Habitaciones", default=1)
    bathrooms = fields.Integer(string="Banios", default=1)
    active = fields.Boolean(string="Activo", default=True)
    garage = fields.Boolean(string="Garage", default=True)
    living_area = fields.Integer(string="Area de vivienda", default=1)