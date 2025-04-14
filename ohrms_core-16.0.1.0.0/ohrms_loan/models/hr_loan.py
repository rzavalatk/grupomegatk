# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get(self, field_list):
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        return result

    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            loan.total_amount = loan.loan_amount
            loan.balance_amount = balance_amount
            loan.total_paid_amount = total_paid

    name = fields.Char(string="Nombre prestamo", default="/", readonly=True, help="Nonbre prestamo")
    date = fields.Date(string="Fecha", default=fields.Date.today(), readonly=True, help="Fecha")
    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True, help="Empleado")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Departamento", help="Empleado")
    installment = fields.Integer(string="Numero de cuotas", default=1, help="Numero de cuotas")
    payment_date = fields.Date(string="Fecha de inicio del pago", required=True, default=fields.Date.today(), help="Fecha de inicio del pago")
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Línea de préstamo", index=True)
    company_id = fields.Many2one('res.company', 'Compañia', readonly=True, help="Compañia",
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Divisa', required=True, help="Divisa",
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Puesto de trabajo",
                                   help="Puesto de trabajo")
    loan_amount = fields.Float(string="Monto del prestamo", required=True, help="Monto del prestamo")
    total_amount = fields.Float(string="Total del monto", store=True, readonly=True, compute='_compute_loan_amount',
                                help="Total del monto del prestamo")
    balance_amount = fields.Float(string="Monto del saldo", store=True, compute='_compute_loan_amount', help="Monto del saldo")
    total_paid_amount = fields.Float(string="Importe total pagado", store=True, compute='_compute_loan_amount',
                                     help="Importe total pagado")

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('waiting_approval_1', 'En espera de aprobación'),
        ('approve', 'Aprobado'),
        ('refuse', 'Rechazado'),
        ('cancel', 'Cancelado'),
    ], string="Estado", default='draft', track_visibility='onchange', copy=False, )

    @api.model
    def create(self, values):
        loan_count = self.env['hr.loan'].search_count(
            [('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
             ('balance_amount', '!=', 0)])
        if loan_count:
            raise ValidationError(_("El empleado tiene pago de cuotas pendientes"))
        else:
            values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
            res = super(HrLoan, self).create(values)
            return res

    def compute_installment(self):
        """Esto crea automáticamente la cuota que el empleado debe pagar a la empresa según la fecha de inicio del pago y el número de cuotas..
            """
        for loan in self:
            loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                date_start = date_start + relativedelta(months=1)
            loan._compute_loan_amount()
        return True

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        self.write({'state': 'waiting_approval_1'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Por favor calcule las cuotas del prestamo"))
            else:
                self.write({'state': 'approve'})

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(
                    'NO puedes borrar un prestamo que no este en borrador o cancelado')
        return super(HrLoan, self).unlink()


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="Fecha de pago", required=True, help="Fecha de pago")
    employee_id = fields.Many2one('hr.employee', string="Empleado", help="Empleado")
    amount = fields.Float(string="Monto", required=True, help="Monto")
    paid = fields.Boolean(string="¿Pagodo?", help="¿Pagado?")
    loan_id = fields.Many2one('hr.loan', string="Prestamo Ref.", help="Prestamo")
    payslip_id = fields.Many2one('hr.payslip', string="Nomina Ref.", help="Nomina")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_employee_loans(self):
        """Este cálculo calcula el monto del préstamo y el recuento total de préstamos de un empleado..
            """
        self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])

    loan_count = fields.Integer(string="Recuento de préstamos", compute='_compute_employee_loans')
