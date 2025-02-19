from odoo import models, fields

class attributes_employee(models.Model):
    _name = 'attr.employee'
    _inherit = "hr.employee"
    _description = "Empleado"

    """name = fields.Many2one('hr.employee',string='Nombre')"""
    credit = fields.Float('Credito')
    number_card = fields.Integer(string='Número de tarjeta')
    available_credit = fields.Float('Credito disponible')

       