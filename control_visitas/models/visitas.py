from odoo import models, fields, api

class Visitas(models.Model):
    _name = 'registro.visitas'
    _description = 'Lleva el registro de las visitas a las diferentes areas de las sucursales.'
    
    name = fields.Char(string = 'Nombre')
    fecha = fields.Datetime(string = 'Fecha', default = fields.Datetime.now())
    region = fields.Char(string = 'Region', compute = "_compute_region", store=True)
    user_id = fields.Many2one('res.users', string = 'Usuario', default = lambda self: self.env.user)
    sucursal_id = fields.Many2one('res.partner', string = 'Sucursal')
    
    api.depends('user_id')
    def _compute_region(self):
        for record in self:
            record.region = record.user_id.region
            
    