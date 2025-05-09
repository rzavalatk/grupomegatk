from odoo import models, fields

class LeafletLocation(models.Model):
    _name = "leaflet.location"
    _description = "Leaflet Location"

    name = fields.Char(string="Name")
    latitude = fields.Float(string="Latitude", default=19.4326)
    longitude = fields.Float(string="Longitude", default=-99.1332)
    map_js = fields.Html(string="Map")