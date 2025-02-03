from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Visitas(models.Model):
    _name = 'control.visitas'
    _description = 'Control de Visitas'
    
    name = fields.Char(string='Nombre', required=True)
    fecha = fields.Date(string='Fecha')
    region = fields.Char(string='Region')
        