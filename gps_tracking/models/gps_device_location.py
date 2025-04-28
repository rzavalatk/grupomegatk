import datetime
from odoo import models, fields, api
from datetime import datetime, timezone
from dateutil.parser import isoparse
import requests
import logging

_logger = logging.getLogger(__name__)

class GpsDeviceLocation(models.Model):
    _name = 'gps.device.location'
    _description = 'Ubicación del Dispositivo GPS'

    device_id = fields.Char('ID del Dispositivo')
    latitude = fields.Float('Latitud')
    longitude = fields.Float('Longitud')
    speed = fields.Float('Velocidad')
    timestamp = fields.Datetime('Fecha y Hora')
    address = fields.Char('Dirección')
    
    @api.model
    def fetch_traccar_positions(self, cr=None, uid=None, context=None):
        # Configura tu IP, usuario y contraseña de Traccar
        traccar_url = 'http://18.222.109.183:8082/api/positions'
        auth = ('areyes@megatk.com', 'admin')  # Cambiar por tus credenciales reales

        try:
            response = requests.get(traccar_url, auth=auth, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Error al conectar con Traccar: {e}")

        positions = response.json()
        _logger.warning(f"Posiciones: {positions}")
        for pos in positions:
            _logger.warning(f"Posicion: {pos}")

        # for pos in positions:
        #     self.create({
        #         'device_id': pos.get('deviceId'),
        #         'latitude': pos.get('latitude'),
        #         'longitude': pos.get('longitude'),
        #         'speed': pos.get('speed'),
        #         'timestamp': datetime.fromtimestamp(pos.get('fixTime') // 1000, tz=timezone.utc) else False,
        #         'address': pos.get('address', ''),
        #     })
        # from datetime import datetime, timezone


        for pos in positions:
            fix_time = pos.get('fixTime')
            t_stamp = False
            if fix_time:
                if isinstance(fix_time, (int, float)):
                    # Si es numérico (timestamp en milisegundos)
                    t_stamp = datetime.fromtimestamp(float(fix_time)/1000, tz=timezone.utc)
                elif isinstance(fix_time, str):
                    # Si es string en formato ISO
                    t_stamp = isoparse(fix_time)
                    # Asegurar que esté en UTC
                    if t_stamp.tzinfo is None:
                        t_stamp = t_stamp.replace(tzinfo=timezone.utc)
                    else:
                        t_stamp = t_stamp.astimezone(timezone.utc)
            
            self.create({
                'device_id': pos.get('deviceId'),
                'latitude': pos.get('latitude'),
                'longitude': pos.get('longitude'),
                'speed': pos.get('speed'),
                'timestamp': t_stamp,
                'address': pos.get('address', ''),
            })