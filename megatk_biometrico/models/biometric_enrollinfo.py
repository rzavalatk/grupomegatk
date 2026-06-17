from odoo import fields, models


class BiometricEnrollInfo(models.Model):
    _name = 'biometric.enrollinfo'
    _description = 'Información biométrica (EnrollInfo)'

    enroll_id = fields.Integer(string='Enroll ID', required=True, index=True)
    backupnum = fields.Char(string='Backup Num')
    signature = fields.Text(string='Firma/Template')
    person_id = fields.Many2one('biometric.person', string='Usuario')
    created_at = fields.Datetime(string='Creado', default=fields.Datetime.now)
