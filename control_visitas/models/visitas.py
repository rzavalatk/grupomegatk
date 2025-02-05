from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import pytz

class Visitas(models.Model):
    _name = 'control.visitas'
    _description = 'Control de Visitas'
    
    name = fields.Char(string='Nombre')
    fecha = fields.Datetime(string='Fecha', compute='_compute_fecha', store=True)
    region = fields.Char(string='Region', compute='_compute_region', store=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user)
    zona = fields.Char(string='Zona', compute='_compute_zona', store=True)
    
    @api.depends('user_id')
    def _compute_region(self):
        for record in self:
            record.region = record.user_id.ubicacion_vendedor
            
    @api.depends('user_id')
    def _compute_zona(self):
        for record in self:
            record.zona = record.user_id.tz

    @api.depends('user_id')
    def _compute_fecha(self):
        for record in self:
            record.fecha = datetime.now()
            
    @api.model
    def create(self, vals):
        user = self.env.user
        if user.ubicacion_vendedor == "SPS" and vals.get('name') in ["Visita Lenka", "Visita Clínica", "Visita Administración"]:
            raise ValidationError("No se pueden registrar esta visita en SPS")
        return super(Visitas, self).create(vals)    
        
    def visita_administracion(self):
        
        self.create({'name': 'Visita Administración'})

    def visita_tienda_megatk(self):
        
        self.create({'name': 'Visita Tienda Megatk'})

    def visita_tienda_meditek(self):
        
        self.create({'name': 'Visita Tienda Meditek'})

    def visita_lenka(self):
        
        self.create({'name': 'Visita Lenka'})

    def visita_clinica(self):
        
        self.redireccionar()
        self.create({'name': 'Visita Clínica'})
            
    def redireccionar(self): 
        return {
            'type': 'ir.actions.act_window',
            'name': 'Redireccionar',
            'res_model': 'control.visitas',
            'view_mode': 'form',
            'target': 'current',
        }
            