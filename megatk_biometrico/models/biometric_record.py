from odoo import fields, models

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
