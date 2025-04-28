# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import fields, models, api, _
from odoo import exceptions
from odoo.exceptions import UserError


class SalaryAdvancePayment(models.Model):
    _name = "salary.advance"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', readonly=True, default=lambda self: 'Adv/')
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, help="Empleado")
    date = fields.Date(string='Fecha', required=True, default=lambda self: fields.Date.today(), help="Fecha de solicitud")
    reason = fields.Text(string='Motivo', help="Motivo")
    currency_id = fields.Many2one('res.currency', string='Moneda', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one('res.company', string='Empresa', required=True,
                                 default=lambda self: self.env.user.company_id)
    advance = fields.Float(string='Anticipo', required=True)
    payment_method = fields.Many2one('account.journal', string='Método de pago')
    exceed_condition = fields.Boolean(string='Excede el máximo permitido',
                                      help="El anticipo excede el porcentaje máximo en la estructura salarial")
    department = fields.Many2one('hr.department', string='Departamento')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('submit', 'Enviado'),
        ('waiting_approval', 'Esperando aprobación'),
        ('approve', 'Aprobado'),
        ('cancel', 'Cancelado'),
        ('reject', 'Rechazado')
    ], string='Estado', default='draft', track_visibility='onchange')
    debit = fields.Many2one('account.account', string='Cuenta de débito')
    credit = fields.Many2one('account.account', string='Cuenta de crédito')
    journal = fields.Many2one('account.journal', string='Diario')
    employee_contract_id = fields.Many2one('hr.contract', string='Contrato')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        department_id = self.employee_id.department_id.id
        domain = [('employee_id', '=', self.employee_id.id)]
        return {'value': {'department': department_id}, 'domain': {
            'employee_contract_id': domain,
        }}

    @api.onchange('company_id')
    def onchange_company_id(self):
        company = self.company_id
        domain = [('company_id.id', '=', company.id)]
        result = {
            'domain': {
                'journal': domain,
            },
        }
        return result

    def submit_to_manager(self):
        self.state = 'submit'

    def cancel(self):
        self.state = 'cancel'

    def reject(self):
        self.state = 'reject'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('salary.advance.seq') or ' '
        res_id = super(SalaryAdvancePayment, self).create(vals)
        return res_id

    def approve_request(self):
        """Este método aprueba la solicitud de anticipo salarial del empleado."""
        emp_obj = self.env['hr.employee']
        address = emp_obj.browse([self.employee_id.id]).address_home_id
        if not address.id:
            raise UserError('Defina la dirección particular del empleado, es decir, la dirección en la información privada del empleado.')

        salary_advance_search = self.search([('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
                                             ('state', '=', 'approve')])
        current_month = datetime.strptime(str(self.date), '%Y-%m-%d').date().month
        for each_advance in salary_advance_search:
            existing_month = datetime.strptime(str(each_advance.date), '%Y-%m-%d').date().month
            if current_month == existing_month:
                raise UserError('Solo se puede solicitar un anticipo por mes.')

        if not self.employee_contract_id:
            raise UserError('Debe definir un contrato para el empleado.')

        struct_id = self.employee_contract_id.struct_id
        adv = self.advance
        amt = self.employee_contract_id.wage
        if adv > amt and not self.exceed_condition:
            raise UserError('El monto del anticipo excede el permitido.')

        if not self.advance:
            raise UserError('Debe ingresar el monto del anticipo salarial.')

        payslip_obj = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id),
                                                     ('state', '=', 'done'), ('date_from', '<=', self.date),
                                                     ('date_to', '>=', self.date)])
        if payslip_obj:
            raise UserError("El salario de este mes ya fue calculado.")

        for slip in self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id)]):
            slip_month = datetime.strptime(str(slip.date_from), '%Y-%m-%d').date().month
            if current_month == slip_month + 1:
                slip_day = datetime.strptime(str(slip.date_from), '%Y-%m-%d').date().day
                current_day = datetime.strptime(str(self.date), '%Y-%m-%d').date().day
                if current_day - slip_day < struct_id.advance_date:
                    raise exceptions.Warning(
                        _('La solicitud solo se puede realizar después de "%s" días desde el salario del mes anterior') % struct_id.advance_date)

        self.state = 'waiting_approval'

    def approve_request_acc_dept(self):
        """Este método aprueba la solicitud de anticipo salarial desde el departamento contable."""
        salary_advance_search = self.search([('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
                                             ('state', '=', 'approve')])
        current_month = datetime.strptime(str(self.date), '%Y-%m-%d').date().month
        for each_advance in salary_advance_search:
            existing_month = datetime.strptime(str(each_advance.date), '%Y-%m-%d').date().month
            if current_month == existing_month:
                raise UserError('Solo se puede solicitar un anticipo por mes.')

        if not self.debit or not self.credit or not self.journal:
            raise UserError("Debe ingresar las cuentas de débito, crédito y el diario para aprobar.")

        if not self.advance:
            raise UserError('Debe ingresar el monto del anticipo salarial.')

        move_obj = self.env['account.move']
        print('===========================move_obj :', move_obj, '==============================')
        timenow = time.strftime('%Y-%m-%d')
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0

        for request in self:
            amount = request.advance
            request_name = request.employee_id.name
            reference = request.name
            journal_id = request.journal.id
            move = {
                'narration': 'Anticipo salarial de ' + request_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
            }

            debit_account_id = request.debit.id
            credit_account_id = request.credit.id

            if debit_account_id:
                debit_line = (0, 0, {
                    'name': request_name,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

            if credit_account_id:
                credit_line = (0, 0, {
                    'name': request_name,
                    'account_id': credit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            move.update({'line_ids': line_ids})
            draft = move_obj.create(move)
            draft.action_post()
            self.state = 'approve'
            return True

