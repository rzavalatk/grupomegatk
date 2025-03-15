from odoo import models, fields, api
from datetime import date, datetime, timedelta
import pytz
import logging

_logger = logging.getLogger(__name__)

class GpsLocation(models.Model):
    _name = 'gps.location'
    _description = 'Ubicación GPS'

    name = fields.Char(string="Nombre", required=True)
    latitude = fields.Float(string="Latitud", digits=(16, 6))
    longitude = fields.Float(string="Longitud", digits=(16, 6))
    user_id = fields.Many2one('res.users', string="Usuario", default=lambda self: self.env.user)
    fecha = fields.Date(string='Fecha', compute='_compute_fecha', store=True)
    hora = fields.Char(string='Hora', compute='_compute_hora', store=True)
    
    
    @api.depends('user_id')
    def _compute_fecha(self):
        for record in self:
            record.fecha = date.today()
            
    @api.depends('user_id')
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