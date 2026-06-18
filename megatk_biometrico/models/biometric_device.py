from odoo import fields, models, api

class BiometricDevice(models.Model):
    _name = 'biometric.device'
    _description = 'Dispositivo biométrico'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    sn = fields.Char(string='Serial Number', required=True, copy=False)
    ip = fields.Char(string='IP')
    status = fields.Selection([('connected','Conectado'),('disconnected','Desconectado')], string='Estado', default='disconnected')
    classroom_id = fields.Many2one('biometric.classroom', string='Aula')
    last_activity = fields.Datetime(string='Última actividad')
    active = fields.Boolean(default=True)
    record_count = fields.Integer(compute='_compute_record_count', string='Marcaciones')

    def _compute_record_count(self):
        for rec in self:
            rec.record_count = self.env['biometric.record'].search_count([('device_serial_num','=',rec.sn)])

    @api.model
    def action_sync_devices(self):
        """Acción para sincronizar dispositivos desde el servidor"""
        config = self.env['biometric.config'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not config:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'No hay configuración de servidor biométrico para esta compañía',
                    'sticky': True,
                    'type': 'danger',
                }
            }
        
        try:
            result = config.sync_devices()
            message = result['message']
            msg_type = 'success' if result['success'] else 'danger'
        except Exception as e:
            message = f'Error: {str(e)}'
            msg_type = 'danger'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronización de Dispositivos',
                'message': message,
                'sticky': True,
                'type': msg_type,
            }
        }

    def action_refresh_status(self):
        """Acción para refrescar el estado de este dispositivo"""
        config = self.env['biometric.config'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not config or not config.server_url:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'Servidor biométrico no configurado',
                    'sticky': True,
                    'type': 'danger',
                }
            }
        
        try:
            # Obtener información del dispositivo del servidor
            devices_response = config._make_request('GET', '/api/devices')
            
            if isinstance(devices_response, list):
                # Buscar este dispositivo en la respuesta
                device_info = next((d for d in devices_response if d.get('sn') == self.sn), None)
                if device_info:
                    status = 'connected' if device_info.get('status') == 1 else 'disconnected'
                    last_activity = config._parse_datetime_string(device_info.get('last_activity'))
                    self.write({
                        'status': status,
                        'ip': device_info.get('ip') or self.ip,
                        'last_activity': last_activity,
                    })
                    message = f"Estado actualizado: {status.upper()}"
                    msg_type = 'success'
                else:
                    message = "Dispositivo no encontrado en el servidor"
                    msg_type = 'warning'
            else:
                message = "Respuesta inválida del servidor"
                msg_type = 'danger'
                
        except Exception as e:
            message = f'Error: {str(e)}'
            msg_type = 'danger'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': f'Estado de {self.name}',
                'message': message,
                'sticky': True,
                'type': msg_type,
            }
        }

