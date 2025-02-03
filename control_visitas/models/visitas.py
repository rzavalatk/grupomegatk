from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Visitas(models.Model):
    _name = 'control.visitas'
    _description = 'Control de Visitas'
    
    name = fields.Char(string='Nombre', required=True)
    fecha = fields.Date(string='Fecha', default=fields.Date.now)
    region = fields.Char(string='Region', store=True)
    #user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user)
