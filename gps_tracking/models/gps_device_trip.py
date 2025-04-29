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
    ], default='ongoing')

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
            trip.state.write('finished')
            
    def fetch_device_positions(self):
        """Buscar nuevas posiciones del dispositivo asociado al viaje"""
        traccar_url_positions = 'http://18.222.109.183:8082/api/positions'
        traccar_url_devices = 'http://18.222.109.183:8082/api/devices'
        username = 'areyes@megatk.com'
        password = 'admin'

        headers = {
            'Accept': 'application/json',
        }

        auth = (username, password)

        for trip in self:
            if trip.state != 'ongoing':
                continue

            # Llamada al API de Traccar
            response_pos = requests.get(traccar_url_positions, auth=auth, headers=headers)
            response_dev = requests.get(traccar_url_devices, auth=auth, headers=headers)
            if response_pos.status_code == 200 and response_dev.status_code == 200:
                positions = response_pos.json()
                devices = response_dev.json()
                dev_id = ''
                
                for dev in devices:
                    traccar_unique_id = str(dev.get('uniqueId'))
                    if traccar_unique_id == trip.device_id:
                        dev_id = str(dev.get('id'))
                        break

                for pos in positions:
                    if dev_id == trip.device_id:

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
