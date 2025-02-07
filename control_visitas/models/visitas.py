from odoo import models, fields, api
from odoo.exceptions import ValidationError
from reports import ReportVisita as rp
import logging
from datetime import datetime

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
        
    datos = lambda self: self.env['report.control_visitas.report_visita']._get_report_values([1])
    _logger.info(f"Datos obtenidos: {datos}")