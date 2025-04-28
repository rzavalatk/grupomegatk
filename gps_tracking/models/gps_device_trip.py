from odoo import models, fields, api
from datetime import datetime
import requests
import logging

_logger = logging.getLogger(__name__)

class GpsDeviceTrip(models.Model):
    _name = 'gps.device.trip'
    _description = 'Viaje del Dispositivo GPS'

    name = fields.Char('Nombre del Viaje', required=True, default=lambda self: 'Nuevo Viaje')
    device_id = fields.Char('ID del Dispositivo', required=True)
    start_time = fields.Datetime('Hora de Inicio', default=lambda self: fields.Datetime.now())
    end_time = fields.Datetime('Hora de Fin')
    location_ids = fields.One2many('gps.device.location', 'trip_id', string='Ubicaciones')
    state = fields.Selection([
        ('ongoing', 'En Curso'),
        ('finished', 'Finalizado')
    ], default='ongoing', string='Estado')

    @api.model
    def start_trip(self, device_id):
        """Iniciar un nuevo viaje"""
        trip = self.create({
            'name': f'Viaje {device_id} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'device_id': device_id,
            'start_time': fields.Datetime.now(),
            'state': 'ongoing',
        })
        return trip

    def finish_trip(self):
        """Finalizar un viaje"""
        for trip in self:
            trip.end_time = fields.Datetime.now()
            trip.state = 'finished'
            
    def fetch_device_positions(self):
        """Buscar nuevas posiciones del dispositivo asociado al viaje"""
        traccar_url = 'http://<IP_PUBLICA_TRACCAR>:8082/api/positions'
        username = '<TU_EMAIL_TRACCAR>'
        password = '<TU_PASSWORD_TRACCAR>'

        headers = {
            'Accept': 'application/json',
        }

        auth = (username, password)

        for trip in self:
            if trip.state != 'ongoing':
                continue

            # Llamada al API de Traccar
            response = requests.get(traccar_url, auth=auth, headers=headers)
            if response.status_code == 200:
                positions = response.json()

                for pos in positions:
                    if str(pos.get('deviceId')) != trip.device_id:
                        continue

                    # Crear una nueva ubicación
                    self.env['gps.device.location'].create({
                        'trip_id': trip.id,
                        'device_id': str(pos.get('deviceId')),
                        'latitude': pos.get('latitude'),
                        'longitude': pos.get('longitude'),
                        'speed': pos.get('speed', 0.0),
                        'timestamp': fields.Datetime.from_string(pos.get('deviceTime')),
                        'address': pos.get('address', ''),
                    })
            else:
                _logger.error(f"Error al conectar a Traccar: {response.status_code}")
