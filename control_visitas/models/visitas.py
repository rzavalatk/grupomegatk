from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Visitas(models.Model):
    _name = 'control.visitas'
    _description = 'Control de Visitas'
    
    name = fields.Char(string='Nombre', required=True)
    fecha = fields.Date(string='Fecha', default=fields.Date.now)
    region = fields.Char(string='Region', compute='_compute_region', store=True)
    #user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user)
    
    @api.depends('region')
    def _compute_region(self):
        for record in self:
            record.region = record.user_id.region
            
    @api.model
    def create(self, vals):
        user = self.env.user
        if user.region == "SPS" and vals.get('name') in ["Visita Lenka", "Visita Clínica", "Visita Administración"]:
            raise ValidationError("No se pueden registrar esta visita en SPS")
        return super(Visitas, self).create(vals)
        
        