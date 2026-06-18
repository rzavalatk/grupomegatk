from odoo import fields, models, api
from datetime import datetime
import requests
import json
from requests.exceptions import RequestException, Timeout


class BiometricConfig(models.Model):
    _name = 'biometric.config'
    _description = 'Configuración biométrica'

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company.id,
    )
    server_url = fields.Char(string='URL del Servidor', help='Ej: http://13.58.64.227:7792')
    api_token = fields.Char(string='Token API')
    websocket_url = fields.Char(string='WebSocket URL')
    default_device_group = fields.Many2one('res.groups', string='Grupo de Dispositivos')
    allow_command_execution = fields.Boolean(string='Permitir ejecución de comandos', default=True)

    _sql_constraints = [
        ('biometric_config_unique_company', 'unique(company_id)', 'Solo puede existir una configuración por compañía.'),
    ]

    def _get_headers(self):
        """Obtiene headers para las peticiones HTTP"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        return headers

    def _make_request(self, method, endpoint, timeout=10, **kwargs):
        """
        Realiza petición HTTP al servidor biométrico
        
        Args:
            method: GET, POST, PUT, DELETE
            endpoint: ruta del endpoint (ej: /api/devices)
            timeout: timeout en segundos
            **kwargs: argumentos adicionales para requests
            
        Returns:
            dict con respuesta JSON o None si falla
        """
        if not self.server_url:
            raise ValueError('URL del servidor no configurada')
        
        url = f"{self.server_url.rstrip('/')}{endpoint}"
        headers = self._get_headers()
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout, **kwargs)
            elif method == 'POST':
                response = requests.post(url, headers=headers, timeout=timeout, **kwargs)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, timeout=timeout, **kwargs)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout, **kwargs)
            else:
                raise ValueError(f'Método HTTP no soportado: {method}')
            
            response.raise_for_status()  # Lanza excepción si status >= 400
            return response.json()
            
        except Timeout:
            raise TimeoutError(f'Timeout al conectar a {url} (>{timeout}s)')
        except RequestException as e:
            raise ConnectionError(f'Error de conexión: {str(e)}')
        except json.JSONDecodeError:
            raise ValueError(f'Respuesta inválida del servidor: {response.text}')

    def _parse_datetime_string(self, value):
        """Parsea timestamps ISO y permite microsegundos."""
        if not value:
            return False
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(value, str):
            text = value.strip()
            # Odoo no siempre maneja bien el formato ISO con microsegundos o Z
            if text.endswith('Z'):
                text = text[:-1]
            text = text.replace('T', ' ')
            try:
                dt = datetime.fromisoformat(text)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
            try:
                dt = datetime.strptime(text, '%Y-%m-%d %H:%M:%S.%f')
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
            try:
                dt = datetime.strptime(text, '%Y-%m-%d %H:%M:%S')
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                return text
        return value

    def sync_devices(self):
        """
        Sincroniza dispositivos desde el servidor biométrico
        
        Obtiene todos los dispositivos de `/api/devices` y:
        - Crea nuevos dispositivos si no existen
        - Actualiza estado (connected/disconnected) de dispositivos existentes
        """
        if not self.server_url:
            raise ValueError('URL del servidor no configurada')
        
        try:
            # Obtener dispositivos del servidor
            response = self._make_request('GET', '/api/devices')
            
            if not isinstance(response, list):
                raise ValueError(f'Respuesta inválida: esperaba lista, recibió {type(response)}')
            
            created = 0
            updated = 0
            
            for device_data in response:
                sn = device_data.get('sn')
                if not sn:
                    continue
                
                # Buscar dispositivo existente
                device = self.env['biometric.device'].search([('sn', '=', sn)], limit=1)
                
                last_activity = self._parse_datetime_string(device_data.get('last_activity'))
                if device:
                    # Actualizar estado y IP
                    status = 'connected' if device_data.get('status') == 1 else 'disconnected'
                    device.write({
                        'status': status,
                        'ip': device_data.get('ip') or device.ip,
                        'last_activity': last_activity,
                    })
                    updated += 1
                else:
                    # Crear nuevo dispositivo
                    self.env['biometric.device'].create({
                        'name': device_data.get('sn'),
                        'sn': sn,
                        'ip': device_data.get('ip'),
                        'status': 'connected' if device_data.get('status') == 1 else 'disconnected',
                        'last_activity': last_activity,
                    })
                    created += 1
            
            return {
                'success': True,
                'created': created,
                'updated': updated,
                'message': f'{created} dispositivos creados, {updated} actualizados'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Error sincronizando dispositivos: {str(e)}'
            }

    def sync_records(self):
        """
        Sincroniza registros/marcaciones desde el servidor biométrico
        
        Si el servidor tiene endpoint /api/records, los obtiene
        De lo contrario, intenta obtener registros desde cada dispositivo
        """
        if not self.server_url:
            raise ValueError('URL del servidor no configurada')
        
        try:
            # Intentar obtener registros del endpoint /api/records
            response = self._make_request('GET', '/api/records')
            
            if not isinstance(response, list):
                raise ValueError(f'Respuesta inválida: esperaba lista')
            
            created = 0
            for record_data in response:
                record_time_raw = record_data.get('records_time')
                record_time = self._parse_datetime_string(record_time_raw)
                if not record_time:
                    continue

                # Verificar si el registro ya existe
                existing = self.env['biometric.record'].search([
                    ('device_serial_num', '=', record_data.get('device_serial_num')),
                    ('enroll_id', '=', record_data.get('enroll_id')),
                    ('records_time', '=', record_time),
                ], limit=1)
                
                if not existing:
                    self.env['biometric.record'].create({
                        'device_serial_num': record_data.get('device_serial_num'),
                        'enroll_id': record_data.get('enroll_id'),
                        'records_time': record_time,
                        'mode': str(record_data.get('mode', 0)),
                        'inout': str(record_data.get('inout', 0)),
                        'event': record_data.get('event', 0),
                        'temperature': record_data.get('temperature', 0),
                        'image': record_data.get('image'),
                    })
                    created += 1
            
            return {
                'success': True,
                'created': created,
                'message': f'{created} registros sincronizados'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Error sincronizando registros: {str(e)}'
            }

    def sync_persons(self):
        """
        Sincroniza usuarios desde el servidor (/persons)
        Crea/actualiza registros en `biometric.person` con enroll_id y nombre
        """
        if not self.server_url:
            raise ValueError('URL del servidor no configurada')

        try:
            response = self._make_request('GET', '/persons')
            if not isinstance(response, list):
                raise ValueError('Respuesta inválida: se esperaba lista de persons')

            created = 0
            updated = 0
            for p in response:
                enroll = p.get('id') or p.get('enroll_id') or p.get('enrollid')
                name = p.get('name') or p.get('username') or p.get('display_name')
                if enroll is None:
                    continue
                existing = self.env['biometric.person'].search([('enroll_id', '=', int(enroll))], limit=1)
                vals = {
                    'enroll_id': int(enroll),
                    'name': name or f'User {enroll}',
                    'active': True,
                }
                if existing:
                    existing.write(vals)
                    updated += 1
                else:
                    self.env['biometric.person'].create(vals)
                    created += 1

            return {'success': True, 'created': created, 'updated': updated, 'message': f'{created} creados, {updated} actualizados'}

        except Exception as e:
            return {'success': False, 'error': str(e), 'message': f'Error sincronizando persons: {str(e)}'}

    def sync_enrollinfo(self):
        """
        Sincroniza información biométrica (enrollInfo) desde `/enrollInfo`
        Guarda los datos en `biometric.enrollinfo` vinculados al usuario.
        """
        if not self.server_url:
            raise ValueError('URL del servidor no configurada')

        try:
            response = self._make_request('GET', '/enrollInfo')
            if not isinstance(response, list):
                raise ValueError('Respuesta inválida: se esperaba lista de enrollInfo')

            created = 0
            updated = 0
            for e in response:
                enroll_id = e.get('enroll_id') or e.get('enrollId') or e.get('id')
                backupnum = e.get('backupnum')
                signature = e.get('signature') or e.get('signatures') or e.get('data')
                if enroll_id is None:
                    continue

                person = self.env['biometric.person'].search([('enroll_id', '=', int(enroll_id))], limit=1)
                vals = {
                    'enroll_id': int(enroll_id),
                    'backupnum': backupnum,
                    'signature': signature if signature is not None else False,
                    'person_id': person.id if person else False,
                }

                existing = self.env['biometric.enrollinfo'].search([('enroll_id', '=', int(enroll_id)), ('backupnum', '=', backupnum)], limit=1)
                if existing:
                    existing.write(vals)
                    updated += 1
                else:
                    self.env['biometric.enrollinfo'].create(vals)
                    created += 1

            return {'success': True, 'created': created, 'updated': updated, 'message': f'{created} enrollinfo creados, {updated} actualizados'}

        except Exception as e:
            return {'success': False, 'error': str(e), 'message': f'Error sincronizando enrollInfo: {str(e)}'}

    def sync_all(self):
        """Sincroniza toda la información biométrica desde el servidor."""
        results = []
        for method_name in ('sync_persons', 'sync_enrollinfo', 'sync_devices', 'sync_records'):
            try:
                method = getattr(self, method_name)
                result = method()
                results.append(f"{method_name}: {result.get('message', 'OK')}")
            except Exception as e:
                results.append(f"{method_name}: ERROR {e}")

        return {
            'success': True,
            'message': '\n'.join(results)
        }

    @api.model
    def _get_config(self):
        """Obtiene la configuración para la compañía actual"""
        return self.search([('company_id', '=', self.env.company.id)], limit=1)
