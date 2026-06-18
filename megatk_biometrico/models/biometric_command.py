from odoo import fields, models, api
from odoo.exceptions import UserError
import requests
import json


class BiometricCommand(models.Model):
    _name = 'biometric.command'
    _description = 'Comando biométrico'
    _order = 'created_at desc'

    serial = fields.Char(string='Serial Dispositivo', required=True)
    device_id = fields.Many2one('biometric.device', string='Dispositivo', compute='_compute_device')
    command_type = fields.Selection([
        ('getuserlist', 'Obtener Lista de Usuarios'),
        ('setuserinfo', 'Agregar Usuario'),
        ('deleteuser', 'Eliminar Usuario'),
        ('deleteuser-complete', 'Quitar Acceso Completo')
    ], string='Tipo de Comando', required=True)
    person_id = fields.Many2one('biometric.person', string='Usuario', domain="[('active', '=', True)]")
    name = fields.Char(string='Nombre del Comando', required=True, compute='_compute_name', store=True)
    content = fields.Text(string='Contenido JSON', required=True, compute='_compute_content', store=True)
    status = fields.Selection([
        ('0','Pendiente'),
        ('1','Enviado'),
        ('2','Completado'),
        ('3','Error')
    ], string='Estado', default='0')
    send_status = fields.Selection([
        ('0','No enviado'),
        ('1','Enviado')
    ], string='Estado de envío', default='0')
    err_count = fields.Integer(string='Errores', default=0)
    run_time = fields.Datetime(string='Última ejecución')
    created_at = fields.Datetime(string='Creado', default=fields.Datetime.now)
    message = fields.Text(string='Mensaje de Resultado')

    def _compute_device(self):
        """Obtiene el dispositivo basado en el serial"""
        for rec in self:
            rec.device_id = self.env['biometric.device'].search([('sn', '=', rec.serial)], limit=1)

    @api.depends('command_type', 'serial', 'person_id')
    def _compute_name(self):
        """Genera automáticamente el nombre del comando"""
        for rec in self:
            type_names = {
                'getuserlist': 'Obtener Lista',
                'setuserinfo': 'Agregar Usuario',
                'deleteuser': 'Eliminar Usuario',
                'deleteuser-complete': 'Quitar Acceso'
            }
            type_name = type_names.get(rec.command_type, 'Comando')
            person_name = f" - {rec.person_id.name}" if rec.person_id else ""
            rec.name = f"{type_name} ({rec.serial}){person_name}"

    @api.depends('command_type', 'serial', 'person_id')
    def _compute_content(self):
        """Genera automáticamente el JSON del comando"""
        for rec in self:
            if rec.command_type == 'getuserlist':
                content = {
                    "cmd": "getuserlist",
                    "sn": rec.serial
                }
            elif rec.command_type == 'setuserinfo':
                if not rec.person_id:
                    raise UserError('Debe seleccionar un usuario para agregar')
                # La contraseña no puede ir vacía al crear usuario en el dispositivo
                if not rec.person_id.password:
                    raise UserError('El usuario seleccionado no tiene contraseña. Agrega una contraseña en Usuarios Biométricos antes de ejecutar este comando.')
                content = {
                    "cmd": "setuserinfo",
                    "enrollid": rec.person_id.enroll_id,
                    "sn": rec.serial,
                    "password": rec.person_id.password,
                }
            elif rec.command_type in ['deleteuser', 'deleteuser-complete']:
                if not rec.person_id:
                    raise UserError('Debe seleccionar un usuario para eliminar')
                content = {
                    "cmd": rec.command_type,
                    "enrollid": rec.person_id.enroll_id,
                    "sn": rec.serial
                }
            else:
                content = {}
            
            rec.content = json.dumps(content) if content else ""

    def execute_command(self):
        """
        Ejecuta el comando en el servidor biométrico
        
        Envía el comando al endpoint correspondiente del servidor FastAPI
        """
        if not self.serial:
            raise UserError('Serial del dispositivo no configurado')
        
        config = self.env['biometric.config'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not config or not config.server_url:
            raise UserError('Servidor biométrico no configurado')
        
        try:
            # Mapear comando a endpoint
            endpoint_map = {
                'getuserlist': f'/api/commands/getuserlist/{self.serial}',
                'setuserinfo': f'/api/commands/setuserinfo/{self.serial}/{self.person_id.enroll_id}' if self.person_id else None,
                'deleteuser': f'/api/commands/deleteuser/{self.serial}/{self.person_id.enroll_id}' if self.person_id else None,
                'deleteuser-complete': f'/api/commands/deleteuser-complete/{self.serial}/{self.person_id.enroll_id}' if self.person_id else None,
            }
            
            endpoint = endpoint_map.get(self.command_type)
            if not endpoint:
                raise UserError(f'Tipo de comando no soportado: {self.command_type}')
            
            # Realizar petición HTTP
            url = f"{config.server_url.rstrip('/')}{endpoint}"
            headers = config._get_headers()
            
            # Enviar contenido JSON del comando en el body (incluye contraseña si aplica)
            headers_with_json = headers.copy() if headers else {}
            headers_with_json.update({'Content-Type': 'application/json'})
            response = requests.post(url, headers=headers_with_json, data=self.content, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Actualizar estado del comando
            self.write({
                'status': '2',  # Completado
                'send_status': '1',  # Enviado
                'message': json.dumps(data, ensure_ascii=False, indent=2)
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Comando Ejecutado',
                    'message': f"✅ Comando ejecutado exitosamente\n\n{data.get('message', 'OK')}",
                    'sticky': True,
                    'type': 'success',
                }
            }
            
        except Exception as e:
            # Registrar error
            self.write({
                'status': '3',  # Error
                'err_count': self.err_count + 1,
                'message': str(e)
            })
            
            raise UserError(f'Error ejecutando comando: {str(e)}')

    @api.model
    def action_create_getuserlist(self):
        """Acción rápida para crear comando de obtener lista de usuarios"""
        if not self.env.context.get('active_id'):
            raise UserError('Debes seleccionar un dispositivo')
        
        device = self.env['biometric.device'].browse(self.env.context.get('active_id'))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'biometric.command',
            'view_mode': 'form',
            'context': {
                'default_serial': device.sn,
                'default_command_type': 'getuserlist'
            }
        }

    @api.model
    def action_create_setuserinfo(self):
        """Acción rápida para crear comando de agregar usuario"""
        if not self.env.context.get('active_id'):
            raise UserError('Debes seleccionar un dispositivo')
        
        device = self.env['biometric.device'].browse(self.env.context.get('active_id'))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'biometric.command',
            'view_mode': 'form',
            'context': {
                'default_serial': device.sn,
                'default_command_type': 'setuserinfo'
            }
        }


class BiometricPerson(models.Model):
    """Modelo para usuarios biométricos (enrollid + nombre)"""
    _name = 'biometric.person'
    _description = 'Usuario Biométrico'
    enroll_id = fields.Integer(string='Enroll ID', required=True, unique=True, index=True)
    name = fields.Char(string='Nombre', required=True)
    password = fields.Char(string='Contraseña', help='Contraseña usada para crear el usuario en el dispositivo')
    active = fields.Boolean(default=True)
    created_at = fields.Datetime(string='Creado', default=fields.Datetime.now)

