from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    credito = fields.Float(string='Crédito', help='Crédito total del empleado')
    credito_disponible = fields.Float(string='Crédito Disponible', help='Crédito disponible del empleado')
    numero_tarjeta = fields.Char(string='Número de Tarjeta', help='Número de tarjeta del empleado')
       