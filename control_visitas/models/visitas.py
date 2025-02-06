from odoo import models, fields, api
from odoo.exceptions import ValidationError


from datetime import datetime

class Visitas(models.Model):
    _name = 'control.visitas'
    _description = 'Control de Visitas'
    
    name = fields.Char(string='Nombre')
    fecha = fields.Datetime(string='Fecha', compute='_compute_fecha', store=True)
    region = fields.Char(string='Region', compute='_compute_region', store=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user)
    
    @api.depends('user_id')
    def _compute_region(self):
        for record in self:
            record.region = record.user_id.ubicacion_vendedor

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
    
      
    # @api.model   
    # def visita_administracion(self, vals):
    #     user = self.env.user
    #     if user.ubicacion_vendedor == "SPS" and vals.get('name') in ["Visita Lenka", "Visita Clínica", "Visita Administración"]:
    #         raise ValidationError("No se pueden registrar esta visita en SPS")
    #     else:
    #         self.create({'name': 'Visita Administración'})
    # @api.model
    # def visita_tienda_megatk(self, vals):
    #     user = self.env.user
    #     if user.ubicacion_vendedor == "SPS" and vals.get('name') in ["Visita Lenka", "Visita Clínica", "Visita Administración"]:
    #         raise ValidationError("No se pueden registrar esta visita en SPS")
    #     else:
    #         self.create({'name': 'Visita Tienda Megatk'})

    # @api.model
    # def visita_tienda_meditek(self, vals):
    #     user = self.env.user
    #     if user.ubicacion_vendedor == "SPS" and vals.get('name') in ["Visita Lenka", "Visita Clínica", "Visita Administración"]:
    #         raise ValidationError("No se pueden registrar esta visita en SPS")
    #     else:    
    #         self.create({'name': 'Visita Tienda Meditek'})
    
    # @api.model
    # def visita_lenka(self, vals):
    #     user = self.env.user
    #     if user.ubicacion_vendedor == "SPS" and vals.get('name') in ["Visita Lenka", "Visita Clínica", "Visita Administración"]:
    #         raise ValidationError("No se pueden registrar esta visita en SPS")
    #     else:
    #         self.create({'name': 'Visita Lenka'})
    
    # @api.model
    # def visita_clinica(self, vals):
    #     # user = self.env.user
    #     # if user.ubicacion_vendedor == "SPS" and vals.get('name') in ["Visita Lenka", "Visita Clínica", "Visita Administración"]:
    #     #     raise ValidationError("No se pueden registrar esta visita en SPS")
    #     # else:
    #     #     self.env['control.visitas'].create({'name': 'Visita Clínica'})
    #     pass
            