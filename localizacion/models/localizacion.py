from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime

class Localizacion(models.Model):
    _name = "localizacion"
    _description = "Localizacion"
    
    name = fields.Char("Localizacion")
    fecha = fields.Date("Fecha")