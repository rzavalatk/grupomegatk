from odoo import fields, models

class BiometricSettings(models.TransientModel):
    _name = 'biometric.settings'
    _inherit = 'res.config.settings'
    _description = 'Ajustes biométricos'

    server_url = fields.Char(string='URL del Servidor', config_parameter='biometric.server_url')
    api_token = fields.Char(string='Token API', config_parameter='biometric.api_token')
    websocket_url = fields.Char(string='WebSocket URL', config_parameter='biometric.websocket_url')
    default_device_group = fields.Many2one('res.groups', string='Grupo de Dispositivos', config_parameter='biometric.default_device_group')
    allow_command_execution = fields.Boolean(string='Permitir ejecución de comandos', default=True, config_parameter='biometric.allow_command_execution')
