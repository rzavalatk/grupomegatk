from odoo import fields, models

class BiometricClassroom(models.Model):
    _name = 'biometric.classroom'
    _description = 'Aula Biométrica'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código')
    floor = fields.Integer(string='Piso')
    capacity = fields.Integer(string='Capacidad')
    building = fields.Char(string='Edificio')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'El código del aula debe ser único.')
    ]
