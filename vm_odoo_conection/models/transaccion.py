from odoo import models, fields

class Transaccion(models.Model):
    _name = 'transaccion'
    _description = 'Transacciones realizadas por los empleados'

    empleado_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    fecha_transaccion = fields.Datetime(string='Fecha de Transacción', default=fields.Datetime.now, required=True)
    producto_consumido = fields.Char(string='Producto Consumido', required=True)
    cantidad_gastada = fields.Float(string='Cantidad Gastada', required=True)