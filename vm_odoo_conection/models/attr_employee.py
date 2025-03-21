from odoo import models, fields, api
from datetime import datetime

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    credito = fields.Float(string='Crédito asignado', help='Crédito total del empleado')
    credito_disponible = fields.Float(string='Crédito Disponible', help='Crédito disponible del empleado')
    numero_tarjeta = fields.Char(string='Número de Tarjeta', help='Número de tarjeta del empleado')
    monto_gastado = fields.Float(string='Monto Gastado', default=0.0, help='Monto gastado desde el 1 del mes hasta la fecha')
    gastado = fields.Float(string='Gastado', compute='_compute_gastado', store=True, help='Monto gastado calculado')

    def reiniciar_credito_disponible(self):
        empleados = self.search([])
        for empleado in empleados:
            empleado.write({
                'credito_disponible': empleado.credito,
                'monto_gastado': 0.0 
            })

    @api.depends('monto_gastado')
    def _compute_gastado(self):
        for empleado in self:
            empleado.gastado = empleado.monto_gastado