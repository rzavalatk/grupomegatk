from odoo import models, fields

class attributes_employee(models.Model):
    _name = "attr.employee"
    _inherit = "hr.employee"
    _description = "Empleado"

    credit = fields.Float(string ='Credito Semanal', default=100)
    number_card = fields.Integer(string='Número de tarjeta')
    available_credit = fields.Float(string = 'Credito disponible', default = 0)

       