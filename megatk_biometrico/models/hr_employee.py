from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    enroll_id = fields.Integer(
        string='Enroll ID Biométrico',
        help='ID de inscripción en el dispositivo biométrico',
        index=True
    )
