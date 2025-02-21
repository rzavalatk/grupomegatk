from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    credito = fields.Float(string='Crédito por semana', help='Crédito total del empleado', default= 100.0)
    credito_disponible = fields.Float(string='Crédito Disponible', help='Crédito disponible del empleado', default = credito)
    numero_tarjeta = fields.Char(string='Número de Tarjeta', help='Número de tarjeta del empleado', default='vacio')