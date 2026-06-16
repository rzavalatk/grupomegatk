from odoo import fields, models

class BiometricCommand(models.Model):
    _name = 'biometric.command'
    _description = 'Comando biométrico'
    _order = 'created_at desc'

    serial = fields.Char(string='Serial Dispositivo', required=True)
    name = fields.Char(string='Nombre del Comando', required=True)
    content = fields.Text(string='Contenido JSON', required=True)
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
