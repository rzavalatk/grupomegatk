import datetime
from odoo import models, fields, api
from datetime import datetime, timezone
from dateutil.parser import isoparse
import requests
import logging

_logger = logging.getLogger(__name__)

class GpsDeviceLocation(models.Model):
    _name = 'gps.location'
    _description = 'Ubicación del Dispositivo GPS'
    
    trip_id = fields.Many2one('gps.device.trip', 'Viaje')
    device_id = fields.Char('ID del Dispositivo')
    latitude = fields.Char('Latitud')
    longitude = fields.Char('Longitud')
    timestamp = fields.Datetime('Fecha')
    fetched_at = fields.Datetime('Hora de Consulta', default=fields.Datetime.now)
    address = fields.Char('Dirección')