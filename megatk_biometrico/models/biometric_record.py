from odoo import fields, models, api

class BiometricRecord(models.Model):
    _name = 'biometric.record'
    _description = 'Registro biométrico'
    _order = 'records_time desc'

    device_serial_num = fields.Char(string='Serial Dispositivo', required=True)
    enroll_id = fields.Integer(string='Enroll ID', required=True)
    records_time = fields.Datetime(string='Hora de Marcación', required=True)
    mode = fields.Selection([
        ('0','Huella'),
        ('1','PIN'),
        ('2','Tarjeta'),
        ('3','Rostro'),
        ('4','Otro')
    ], string='Modo', default='0')
    inout = fields.Selection([
        ('0','Entrada'),
        ('1','Salida'),
        ('4','Ambos')
    ], string='In/Out', default='0')
    event = fields.Integer(string='Evento')
    temperature = fields.Float(string='Temperatura')
    image = fields.Char(string='Imagen/base64')
    device_id = fields.Many2one('biometric.device', string='Dispositivo', compute='_compute_device')

    def _compute_device(self):
        for rec in self:
            rec.device_id = self.env['biometric.device'].search([('sn', '=', rec.device_serial_num)], limit=1)

    @api.model
    def action_sync_records(self):
        """Acción para sincronizar registros desde el servidor"""
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
            result = config.sync_records()
            message = result['message']
            msg_type = 'success' if result['success'] else 'danger'
        except Exception as e:
            message = f'Error: {str(e)}'
            msg_type = 'danger'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronización de Marcaciones',
                'message': message,
                'sticky': True,
                'type': msg_type,
            }
        }

