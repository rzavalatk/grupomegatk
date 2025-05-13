from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, time
from dateutil.parser import isoparse
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
    tiempo_usado = fields.Char('Tiempo Usado')
    check_in = fields.Boolean('Check-in', default=False)
    state = fields.Selection([
        ('new', 'Nuevo'),
        ('ongoing', 'En Curso'),
        ('finished', 'Finalizado')
    ], default='new')
    
    
    @api.model
    def create(self, vals):
        # Verificamos si se quiere crear el viaje directamente como 'ongoing'
        if vals.get('state') == 'ongoing' and vals.get('device_id'):
            existing_trip = self.search([
                ('device_id', '=', vals['device_id']),
                ('state', '=', 'ongoing')
            ], limit=1)
            if existing_trip:
                raise ValidationError("Ya existe un viaje en curso para este dispositivo.")

        return super(GpsDeviceTrip, self).create(vals)
    
    # def check_trips(self):
    #     trip = self.search([('state','in',['ongoing','finished','new'])])
    #     _logger.warning(f"Cantidad de viajes: {len(trip)}")
    #     new  = 0
    #     ongoing = 0
    #     finished = 0
    #     for trip in self:          
    #         if trip.state == 'new':
    #             new += 1
    #         if trip.state == 'ongoing':
    #             ongoing += 1
    #         if trip.state == 'finshed':
    #             finished += 1
                
    #     if new > 0 or ongoing > 0:
    #         return True
                
    #     if finished == len(trip):
    #         return False
                
    @api.model
    def start_trip(self, device_id):
        """Iniciar un nuevo viaje"""
        viaje_encurso = self.search([
            ('device_id','=',device_id),
            ('state','=','ongoing')
            ],limit=1)
        if viaje_encurso:
            raise ValidationError(f"Ya hay un viaje en curso para este dispositivo ({viaje_encurso.name})")
        
        trip = self.create({
            'name': f'Viaje {device_id} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'device_id': device_id,
            'start_time': fields.Datetime.now(),
            'check_in': True,
            'state': 'ongoing'
        })
        
        self.write({'state': 'ongoing'})
        self.fetch_device_positions()
        return trip
    
    # def action_start_trip(self):
    #     for trip in self:
    #         existing = self.search([
    #             ('device_id','=',trip.device_id),
    #             ('state','=','ongoing'),
    #             ('id','!=',trip.id),
    #             ], limit=1)
            
    #         if existing:
    #             raise ValidationError(f"Ya hay un viaje en curso para este dispositivo")
            
    #         trip.write({
    #             'name': f'Viaje {trip.device_id} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    #             'start_time': fields.Datetime.now(),
    #             'state': 'ongoing',
    #         })
            
    #     active = self.check_trips()
    #     if active:

    #         cron = self.env.ref('gps_tracking.ir_cron_update_gps_positions')
    #         cron.write({'active': True, 'nextcall': fields.Datetime.now()})
    #     else:
    #         cron = self.env.ref('gps_tracking.ir_cron_update_gps_positions')
    #         cron.write({'active': False, 'nextcall': fields.Datetime.now()})

    def finish_trip(self, id_device):
        """Finalizar un viaje"""
        for trip in self:
            if id_device == trip.device_id:
                trip.end_time = fields.Datetime.now()
                trip.write({
                    'state': 'finished',
                    'check_in': False
                })
                return trip;
            _logger.warning(trip.end_time)

                
    def fetch_device_positions(self):
        _logger.warning("entrooo")
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
                    _logger.warning(f"Traccar Unique ID: {traccar_unique_id}")
                    if traccar_unique_id == trip.device_id:
                        _logger.warning(f"Traccar Unique ID: {traccar_unique_id}")
                        _logger.warning(f"Odoo Device ID: {trip.device_id}")
                        dev_id = str(dev.get('id'))
                        _logger.warning(f"Traccar Device ID: {dev_id}")
                        break

                for pos in positions:
                    traccar_device_id = str(pos.get('deviceId'))
                    
                    try:
                        device_time = pos.get('deviceTime')
                        timestamp = False
            
                        if device_time:
                            # Parsear el formato ISO
                            dt = isoparse(device_time)
                            # Convertir a formato Odoo
                            timestamp = fields.Datetime.to_string(dt)
                    
                        if dev_id == traccar_device_id:
                            
                            # Crear una nueva ubicación
                            self.env['gps.device.location'].create({
                                'trip_id': trip.id,
                                'device_id': traccar_unique_id,
                                'latitude': pos.get('latitude'),
                                'longitude': pos.get('longitude'),
                                'timestamp': timestamp,
                                'address': pos.get('address', ''),
                            })
                    except Exception as e:
                        _logger.error(f"Error al crear la ubicación: {e}")
            else:
                _logger.error(f"Error al conectar a Traccar: Positions {response_pos.status_code} - Devices {response_dev.status_code}")
            
        return True
    
    def cron_fetch_positions(self):
        viajes = self.search([('state','=','ongoing')])
        _logger.warning(f"Cron: se encontraron {len(viajes)} viajes en curso para actualizar")
        viajes.fetch_device_positions()
    


