from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    credito= fields.Float(string='Crédito asignado', help='Crédito total del empleado')
    credito_disponible= fields.Float(string='Crédito Disponible', help='Crédito disponible del empleado')
    numero_tarjeta= fields.Char(string='Número de Tarjeta', help='Número de tarjeta del empleado')
    gastado = fields.Float(string='Gastado', help='Credito gastado desde el 1 del mes hasta la fecha')

    def reiniciar_credito_disponible(self):
        empleados = self.search([])  
        for empleado in empleados:
            empleado.write({'credito_disponible': empleado.credito})

    def gastos(self):
        empleados = self.search([])
        for empleado in empleados:
            empleado.write({'gastado': empleado.credito - empleado.credito_disponible})