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
    _order = 'timestamp desc'
    
    trip_id = fields.Many2one('gps.device.trip', 'Viaje', index=True)
    device_id = fields.Char('ID del Dispositivo', index=True)
    latitude = fields.Char('Latitud')
    longitude = fields.Char('Longitud')
    timestamp = fields.Datetime('Fecha', index=True)
    fetched_at = fields.Datetime('Hora de Consulta', default=fields.Datetime.now)
    address = fields.Char('Dirección')
    map_url = fields.Char(string="Ver en Google Maps", compute="_compute_map_url", store=False)
    map_btn = fields.Html(string="Ver en Google Maps", compute="_compute_map_btn", store=False)
    
    @api.model
    def fetch_traccar_positions(self, cr=None, uid=None, context=None):
        # Configura tu IP, usuario y contraseña de Traccar
        traccar_url = 'http://18.222.109.183:8082/api/positions'
        auth = ('areyes@megatk.com', 'admin') 

        try:
            response = requests.get(traccar_url, auth=auth, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Error al conectar con Traccar: {e}")

        positions = response.json()
        _logger.warning(f"Posiciones: {positions}")
        for pos in positions:
            _logger.warning(f"Posicion: {pos}")

        for pos in positions:
            fix_time = pos.get('fixTime')
            t_stamp = False
            if fix_time:
                if isinstance(fix_time, (int, float)):
                    # Si es numérico (timestamp en milisegundos)
                    t_stamp = datetime.fromtimestamp(float(fix_time)/1000, tz=timezone.utc)
                elif isinstance(fix_time, str):
                    # Si es string en formato ISO
                    dt = isoparse(fix_time)
                    t_stamp = dt.replace(tzinfo=None)
                    
            self.create({
                'device_id': pos.get('deviceId'),
                'latitude': pos.get('latitude'),
                'longitude': pos.get('longitude'),
                'timestamp': t_stamp,
                'fetched_at': fields.Datetime.now(),
                'address': pos.get('address', ''),
                'map_url': self.map_url
            })
            
    def _compute_map_url(self):
        for record in self:
            if record.latitude and record.longitude:
                record.map_url = f"https://www.google.com/maps?q={record.latitude},{record.longitude}"
            else:
                record.map_url = ""
                
    def _compute_map_btn(self):
        for record in self:
            if record.map_url:
                record.map_btn = f"""
                    <a href="{record.map_url}" target="_blank"
                    style="text-decoration: none;">
                        <span style="color: #007bff; cursor:pointer;">
                            Ver en Mapa
                        </span>
                    </a>
                """
            else:
                record.map_btn = "-"