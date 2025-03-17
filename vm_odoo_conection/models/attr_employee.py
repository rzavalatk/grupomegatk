from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    credito= fields.Float(string='Crédito asignado', help='Crédito total del empleado')
    credito_disponible= fields.Float(string='Crédito Disponible', help='Crédito disponible del empleado')
    numero_tarjeta= fields.Char(string='Número de Tarjeta', help='Número de tarjeta del empleado')
    gastado = fields.Float(string='Gastado',help='Crédito gastado desde el 1 del mes hasta la fecha',compute='_compute_gastado',store=True)

    def reiniciar_credito_disponible(self):
        empleados = self.search([])  
        for empleado in empleados:
            empleado.write({'credito_disponible': empleado.credito})

    @api.depends('credito', 'credito_disponible')
    def _compute_gastado(self):
        for empleado in self:
            empleado.gastado = empleado.credito - empleado.credito_disponible