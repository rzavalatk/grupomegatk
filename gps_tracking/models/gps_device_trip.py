from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta
from dateutil.parser import isoparse
import pytz
import requests
import logging

_logger = logging.getLogger(__name__)

class GpsDeviceTrip(models.Model):
    _name = 'gps.device.trip'
    _description = 'Viaje del Dispositivo GPS'

    name = fields.Char('Nombre del Viaje', required=True, default=lambda self: 'Nuevo Viaje')
    device_id = fields.Char('ID del Dispositivo', required=True)
    start_date = fields.Date('Fecha de Inicio', compute='_define_date', store=True)
    end_date = fields.Date('Fecha de Fin')
    start_time = fields.Char('Hora de Inicio', compute='_define_time', store=True)
    end_time = fields.Char('Hora de Fin')
    location_ids = fields.One2many('gps.device.location', 'trip_id', string='Ubicaciones')
    tiempo_usado = fields.Char('Tiempo Usado')
    check_in = fields.Boolean('Check-in', default=False)
    id_employee = fields.Many2one('hr.employee', 'Empleado', required=True)
    code = fields.Char(string='Código de Viaje')
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
            
        
            if vals.get('code', '/') == '/':
                vals['code'] = self.env['ir.sequence'].next_by_code('trip.id') or '/'

        return super(GpsDeviceTrip, self).create(vals)
     
    def _define_time(self):
        hora_utc = datetime.now(pytz.utc)
        zona_horaria_usuario = self.env.user.tz or 'UTC'
        if hasattr(zona_horaria_usuario, 'zone'):
            zona_horaria = zona_horaria_usuario
        else:
            zona_horaria = pytz.timezone(zona_horaria_usuario)
            hora_local = hora_utc.astimezone(zona_horaria).strftime('%H:%M:%S')
            _logger.warning(f"Hora local: {zona_horaria_usuario}")
        hora_inicio = hora_local
        return hora_inicio
    
    def _define_date(self):
        fecha = date.today()
        return fecha
                
    @api.model
    def start_trip(self, device_id, employee_id):
        """Iniciar un nuevo viaje"""
        viaje_encurso = self.search([
            ('device_id','=',device_id),
            ('id_employee','=',employee_id),
            ('state','=','ongoing')
            ],limit=1)
        if viaje_encurso:
            raise ValidationError(f"Ya hay un viaje en curso para este dispositivo ({viaje_encurso.name})")
        
        trip = self.create({
            'code': self.env['ir.sequence'].next_by_code('trip.id') or '/',
            'name': f'Viaje {device_id} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'device_id': device_id,
            'id_employee': employee_id,
            'start_time': self._define_time(),
            'start_date': self._define_date(),
            'check_in': True,
            'state': 'ongoing'
        })
        
        self.write({'state': 'ongoing'})
        self.fetch_device_positions()
        return {
            'device_id': device_id,
            'id_employee': employee_id,
            'start_time': trip.start_time,
            'start_date': trip.start_date,
            'check_in': trip.check_in,
            'state': trip.state,
        }
        
    @api.model
    def finish_trip(self, id_device, employee_id):
        """Finalizar un viaje"""
        _logger.warning(f"desde finish employee {employee_id}")
        trip = self.search([
            ('device_id','=',id_device),
            ('id_employee','=',employee_id),
            ('state','=','ongoing')
            ],limit=1)
        trip2 = self.search([
            ('device_id','=',id_device),
            
            ('state','=','ongoing')
            ],limit=1)
        _logger.warning(f"desde finish trip {trip}")
        if trip:
            trip.end_time = self._define_time()
            trip.end_date = self._define_date()
            trip.write({
                'state': 'finished',
                'check_in': False
            })
        _logger.warning(f"desde finish trip {trip}")
            
        return {
            'device_id': trip.device_id,
            'start_time': trip.start_time,
            'end_time': trip.end_time,
            'end_date': trip.end_date,
            'check_in': trip.check_in,
            'state': trip.state,
        }
                
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

                # Obtener la última ubicación registrada para este viaje
                last_location = self.env['gps.device.location'].search([
                    ('trip_id', '=', trip.id)
                ], order='timestamp desc', limit=1)
                
                last_timestamp = last_location.timestamp if last_location else False
                _logger.info(f"Última ubicación registrada: {last_timestamp}")
                
                new_positions_count = 0
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
                            # Verificar si la posición es nueva (posterior a la última registrada)
                            if last_timestamp and timestamp:
                                if fields.Datetime.from_string(timestamp) <= last_timestamp:
                                    _logger.debug(f"Posición ya registrada o antigua, omitiendo: {timestamp}")
                                    continue
                            
                            # Verificar si ya existe esta ubicación exacta (por timestamp y trip_id)
                            existing_location = self.env['gps.device.location'].search([
                                ('trip_id', '=', trip.id),
                                ('timestamp', '=', timestamp)
                            ], limit=1)
                            
                            if existing_location:
                                _logger.debug(f"Ubicación duplicada encontrada, omitiendo: {timestamp}")
                                continue
                            
                            # Obtener datos de calidad GPS
                            accuracy = pos.get('accuracy', 0)  # Precisión en metros
                            speed = pos.get('speed', 0)  # Velocidad
                            valid = pos.get('valid', True)  # Posición válida
                            
                            # Filtrar posiciones de baja calidad para mejor routing
                            # Solo registrar si la precisión es menor a 50 metros y la posición es válida
                            if not valid:
                                _logger.debug(f"Posición GPS inválida, omitiendo: {timestamp}")
                                continue
                                
                            if accuracy and accuracy > 50:
                                _logger.debug(f"Baja precisión GPS ({accuracy}m), omitiendo: {timestamp}")
                                continue
                            
                            # Crear una nueva ubicación solo si es nueva y de buena calidad
                            self.env['gps.device.location'].create({
                                'trip_id': trip.id,
                                'device_id': traccar_unique_id,
                                'latitude': pos.get('latitude'),
                                'longitude': pos.get('longitude'),
                                'timestamp': timestamp,
                                'address': pos.get('address', ''),
                                'accuracy': accuracy,
                                'speed': speed,
                                'valid': valid,
                            })
                            new_positions_count += 1
                            _logger.info(f"Nueva ubicación creada: {timestamp} - Lat: {pos.get('latitude')}, Lon: {pos.get('longitude')}, Precisión: {accuracy}m, Velocidad: {speed}km/h")
                    except Exception as e:
                        _logger.error(f"Error al crear la ubicación: {e}")
                        
                _logger.info(f"Viaje {trip.name}: Se agregaron {new_positions_count} nuevas posiciones")
            else:
                _logger.error(f"Error al conectar a Traccar: Positions {response_pos.status_code} - Devices {response_dev.status_code}")
            
        return True
    @api.model
    def get_locations(self, id_trip):
        locations = self.env['gps.device.trip'].search([('code','=',id_trip)])
        coords = []
        for location in locations.location_ids:
            _logger.warning(f"Coords: [{location.latitude},{location.longitude}]")
            coords.append([location.latitude, location.longitude])
            
        _logger.warning(f"Coords: {coords}")
        return coords
    
    @api.model
    def get_info (self, id_trip):
        data = self.env['gps.device.trip'].search([('code','=',id_trip)])
        if not data:
            return {
                'id_employee': False,
                'id_device': False,
                'start_date': False,
                'used_time': '00:00:00', # Devolver un valor por defecto si no se encuentra el viaje
            }

        _logger.warning(f"start: {data.start_time} end: {data.end_time}")
        _logger.warning(f"start: {type(data.start_time)} end: {type(data.end_time)}")
        
        # Odoo ya maneja los campos de tiempo como objetos time o datetime
        # No es necesario hacer strptime si los campos start_time y end_time son fields.Char de tiempo
        # Si son fields.Datetime o fields.Date, la lógica es diferente.
        # Asumo que start_time y end_time son strings 'HH:MM:SS' o fields.Char que almacenan tiempo.

        # Convertir a objetos datetime para la resta, usando una fecha base para el cálculo
        # La fecha es arbitraria ya que solo nos interesa la parte de la hora.
        dummy_date = datetime(2000, 1, 1) # Una fecha cualquiera para poder crear el objeto datetime

        try:
            t1 = datetime.combine(dummy_date.date(), datetime.strptime(data.start_time, '%H:%M:%S').time())
            t2 = datetime.combine(dummy_date.date(), datetime.strptime(data.end_time, '%H:%M:%S').time())
            
            diferencia = t2 - t1
            
            # Manejar el caso si el tiempo final es menor que el inicial (e.g., cruza la medianoche)
            if diferencia < timedelta(0):
                diferencia += timedelta(days=1) # Añadir un día para obtener la duración correcta
            
            _logger.warning(f"Diferencia: {diferencia}")

            # Formatear el timedelta a HH:MM:SS
            # Calcula los segundos totales para formatear
            total_seconds = int(diferencia.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # Usa f-strings para un formato con ceros iniciales
            formatted_used_time = f"{hours:02}:{minutes:02}:{seconds:02}"
            
        except ValueError:
            _logger.error(f"Error al parsear el tiempo para el viaje {id_trip}: start={data.start_time}, end={data.end_time}")
            formatted_used_time = 'Error de formato'
        except Exception as e:
            _logger.error(f"Error inesperado al calcular la diferencia de tiempo para el viaje {id_trip}: {e}")
            formatted_used_time = 'Error de cálculo'


        return {
            'id_employee': data.id_employee.name,
            'id_device': data.device_id,
            'start_date': data.start_date, # Este es un campo Date, no Datetime
            'used_time': formatted_used_time, # <-- ¡Ahora es un string HH:MM:SS!
        }
    
    @api.model    
    def check_code(self, trip_code):
        trip = self.env['gps.device.trip'].search([('code','=',trip_code)])
        if not trip:
            return False
        return True
    
    @api.model    
    def check_id(self, id_device):
        traccar_url = 'http://18.222.109.183:8082/api/devices'
        auth = ('areyes@megatk.com', 'admin') 

        try:
            response = requests.get(traccar_url, auth=auth, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Error al conectar con Traccar: {e}")
        
        ids = response.json()
        
        for id in ids:
            _logger.warning(f"Traccar Unique ID: {id.get('uniqueId')}")
            _logger.warning(f"Unique ID: {id_device}")
            if id.get('uniqueId') == id_device:
                return True
            
        return False
    
    def cron_fetch_positions(self):
        viajes = self.search([('state','=','ongoing')])
        _logger.warning(f"Cron: se encontraron {len(viajes)} viajes en curso para actualizar")
        viajes.fetch_device_positions()
  

