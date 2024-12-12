# -*- coding:utf-8 -*-

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Empleado'

    slip_ids = fields.One2many('hr.payslip', 'employee_id', string='Nóminas', readonly=True, help="Nóminas")
    payslip_count = fields.Integer(compute='_compute_payslip_count', string='Cantidad de nóminas')

    def _compute_payslip_count(self):
        """ Calcula la cantidad de nóminas asociadas a cada empleado. """
        payslip_data = self.env['hr.payslip'].sudo().read_group(
            [('employee_id', 'in', self.ids)], ['employee_id'], ['employee_id']
        )
        result = dict((data['employee_id'][0], data['employee_id_count']) for data in payslip_data)
        for employee in self:
            employee.payslip_count = result.get(employee.id, 0)



