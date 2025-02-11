from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pdf
from datetime import datetime
import logging
import base64

_logger = logging.getLogger(__name__)

class Visitas(models.Model):
    _name = 'control.visitas'
    _description = 'Control de Visitas'
    
    name = fields.Char(string='Nombre')
    fecha = fields.Datetime(string='Fecha y Hora', compute='_compute_fecha', store=True)
    region = fields.Char(string='Region', compute='_compute_region', store=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user, store=True)
    
    @api.depends('user_id')
    def _compute_region(self):
        for record in self:
            if record.user_id.ubicacion_vendedor == '3':
                record.region = 'TGU'
            if record.user_id.ubicacion_vendedor == '2':
                record.region = 'SPS'

    @api.depends('user_id')
    def _compute_fecha(self):
        
        lista = self._search([('region', '=', 'TGU')], limit=1)
        _logger.warning(f"Registros obtenidos: {lista.id}, {lista.name}, {lista.region}")
        for record in self:
            record.fecha = datetime.now()
 
    @api.model
    def create(self, vals):
         user = self.env.user
         if user.ubicacion_vendedor == "2" and vals.get('name') in ["Visita Lenka", "Visita Clínica", "Visita Administración"]:
             raise ValidationError("No se puede registrar esta visita en SPS")
         return super(Visitas, self).create(vals)  
      
    @api.model   
    def visita_administracion(self, admin):
        self.create({'name': 'Visita Administración'})
            
    @api.model
    def visita_tienda_megatk(self, vals):
        self.create({'name': 'Visita Tienda Megatk'})

    @api.model
    def visita_tienda_meditek(self, vals):    
        self.create({'name': 'Visita Tienda Meditek'})
    
    @api.model
    def visita_lenka(self, vals):    
        self.create({'name': 'Visita Lenka'})
    
    @api.model
    def visita_clinica(self, vals):
        self.env['control.visitas'].create({'name': 'Visita Clínica'})    
    
    # # def send_email(self,email,cc="",contexto={}):
    #     template = self.env.ref('control_visitas.email_template_visita')
    #     email_values = {
    #         'email_from': 'azelaya@megatk.com',
    #         'email_to': "alexdreyesmt@gmail.com",
    #         'email_cc': cc
    #     }
    #     template.with_context(contexto).send_mail(self.id, email_values=email_values, force_send=True)
    #     self.write({
    #         'state': 'done'
    #     })
    #     return True  
    