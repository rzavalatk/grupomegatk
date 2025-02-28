from odoo import models, fields, api
from datetime import date, datetime
import logging
import pytz

_logger = logging.getLogger(__name__)

class ControlViaje(models.Model):
    _name = 'viaje.check'
    _description = 'Controla las coordenadas de los viajes'
    
    name = fields.Char(string='Nombre', default=lambda self: self.env.user.name)
    fecha = fields.Date(string='Fecha', compute='_compute_fecha', store=True)
    hora = fields.Char(string='Hora', compute='_compute_hora', store=True)
    check_latitude = fields.Char(string='Check In Latitude', store=True, help="Check in latitude of the User")    
    check_longitude = fields.Char(string='Check In Longitude', store=True, help="Check in longitude of the User")
    check_location = fields.Char(string='Check In Location Link', store=True, help="Check in location link of the User")

    @api.depends('name')
    def _compute_fecha(self):
        for record in self:
            record.fecha = date.today()
            
    @api.depends('name')
    def _compute_hora(self):
        for record in self:
            hora_utc = datetime.now(pytz.utc)
            
            zona_horaria_usuario = self.env.user.tz or 'UTC'
            
            if hasattr(zona_horaria_usuario, 'zone'):
                zona_horaria = zona_horaria_usuario
            else:
                zona_horaria = pytz.timezone(zona_horaria_usuario)
            
            hora_local = hora_utc.astimezone(zona_horaria).strftime('%H:%M:%S')
            _logger.warning(f"Hora local: {zona_horaria_usuario}")
            record.hora = hora_local