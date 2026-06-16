from odoo import fields, models

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
