from odoo import fields, models


class BiometricSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = 'Ajustes biométricos'

    server_url = fields.Char(string='URL del Servidor')
    api_token = fields.Char(string='Token API')
    websocket_url = fields.Char(string='WebSocket URL')
    default_device_group = fields.Many2one(
        'res.groups',
        string='Grupo de Dispositivos',
        default_model='res.groups'
    )
    allow_command_execution = fields.Boolean(string='Permitir ejecución de comandos', default=True)

    def _company_id_from_input(self, company):
        if hasattr(company, 'id'):
            return company.id
        if company:
            return int(company)
        return self.env.company.id

    def get_values(self):
        res = super(BiometricSettings, self).get_values()
        config = self.env['biometric.config'].sudo().search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        if config:
            res.update(
                server_url=config.server_url or '',
                api_token=config.api_token or '',
                websocket_url=config.websocket_url or '',
                default_device_group=config.default_device_group.id if config.default_device_group else False,
                allow_command_execution=config.allow_command_execution,
            )
        return res

    def set_values(self):
        super(BiometricSettings, self).set_values()
        config_model = self.env['biometric.config'].sudo()
        config = config_model.search([('company_id', '=', self.env.company.id)], limit=1)
        vals = {
            'company_id': self.env.company.id,
            'server_url': self.server_url,
            'api_token': self.api_token,
            'websocket_url': self.websocket_url,
            'default_device_group': self.default_device_group.id if self.default_device_group else False,
            'allow_command_execution': self.allow_command_execution,
        }
        if config:
            config.write(vals)
        else:
            config_model.create(vals)
        # Intentar sincronizar inmediatamente al guardar la configuración
        try:
            cfg = config_model.search([('company_id', '=', self.env.company.id)], limit=1)
            if cfg:
                # Sincronizar persons, enrollInfo, devices y registros
                cfg.sync_persons()
                cfg.sync_enrollinfo()
                cfg.sync_devices()
                cfg.sync_records()
        except Exception:
            # No interrumpir el guardado si hay errores de red; el usuario puede reintentar manualmente
            pass
