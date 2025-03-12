from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    credito= fields.Float(string='Crédito por semana', help='Crédito total del empleado', default=100.0)
    credito_disponible= fields.Float(string='Crédito Disponible', help='Crédito disponible del empleado', default =0.0)
    numero_tarjeta= fields.Char(string='Número de Tarjeta', help='Número de tarjeta del empleado', default='vacio')
    credito_a_recargar = fields.Float(string='Prueba')

    def recargar_credito(self):
        self.credito = self.credito_a_recargar
        return True

    @api.model
    def actualizar_creditos_mensualmente(self):
        hoy = date.today()
        if hoy.day == 1:  # Verifica si es el primer día del mes
            empleados = self.search([])  # Obtiene todos los empleados
            for empleado in empleados:
                empleado.credito = empleado.credito_a_recargar