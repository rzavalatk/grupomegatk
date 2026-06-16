from odoo import fields, models, api


class BiometricConfig(models.Model):
    _name = 'biometric.config'
    _description = 'Configuración biométrica'

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company.id,
    )
    server_url = fields.Char(string='URL del Servidor')
    api_token = fields.Char(string='Token API')
    websocket_url = fields.Char(string='WebSocket URL')
    default_device_group = fields.Many2one('res.groups', string='Grupo de Dispositivos')
    allow_command_execution = fields.Boolean(string='Permitir ejecución de comandos', default=True)

    _sql_constraints = [
        ('biometric_config_unique_company', 'unique(company_id)', 'Solo puede existir una configuración por compañía.'),
    ]
