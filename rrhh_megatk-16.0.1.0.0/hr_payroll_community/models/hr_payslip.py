# -*- coding:utf-8 -*-

import logging
import babel
from collections import defaultdict
from datetime import date, datetime, time
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from pytz import timezone
from pytz import utc
import pytz
import io
import base64
import xlsxwriter

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_utils

_logger = logging.getLogger(__name__)
honduras_tz = pytz.timezone('America/Tegucigalpa')

# This will generate 16th of days
ROUNDING_FACTOR = 16


class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _description = 'Pay Slip'

    struct_id = fields.Many2one('hr.payroll.structure', string='Estructura',
                                readonly=True,
                                states={'draft': [('readonly', False)]},
                                help='Define las reglas que deben aplicarse a este recibo de nómina, en consecuencia '
                                     'al contrato elegido. Si deja vacío el campo contrato, este campo no es '
                                     'ya no es obligatorio y, por lo tanto, las reglas aplicadas serán todas las reglas establecidas en el '
                                     'estructura de todos los contratos del empleado válidos para el período elegido')
    name = fields.Char(string='Nombre de nomina', readonly=True, compute='_compute_payslip_name',
                       states={'draft': [('readonly', False)]})
    number = fields.Char(string='Referencia', readonly=True, copy=False,
                         help="References",
                         states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Empleado',
                                  required=True, readonly=True, help="Empleado",
                                  states={'draft': [('readonly', False)]})
    date_from = fields.Date(string='Fecha desde', readonly=True, required=True,
                            help="Fecha de inicio",
                            default=lambda self: fields.Date.to_string(
                                date.today().replace(day=1)),
                            states={'draft': [('readonly', False)]})
    date_to = fields.Date(string='Fecha hasta', readonly=True, required=True,
                          help="Fecha final",
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1,
                                                              days=-1)).date()),
                          states={'draft': [('readonly', False)]})
    total_payment = fields.Float(
        'Total a pagar', readonly=True, compute='_compute_total_payment')
    deduction = fields.Float('Deducción')
    accreditation = fields.Float('Acreditación')
    # this is chaos: 4 states are defined, 3 are used ('verify' isn't) and 5 exist ('confirm' seems to have existed)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('verify', 'Esperando'),
        ('done', 'Hecho'),
        ('cancel', 'Rechazado'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* Cuando se crea el recibo de nómina el estado es \'Borrador\'
                \n* Si el recibo de sueldo está bajo verificación, el estado es \'En espera\'.
                \n* Si se confirma el recibo de sueldo, el estado se establece en \'Listo\'.
                \n* Cuando el usuario cancela el recibo de pago, el estado es \'Rechazado\'.""")
    line_ids = fields.One2many('hr.payslip.line', 'slip_id',
                               string='Líneas de nómina', readonly=True,
                               states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Compañia', readonly=True,
                                 copy=False, help="Compañia",
                                 default=lambda self: self.env[
                                     'res.company']._company_default_get(),
                                 states={'draft': [('readonly', False)]})
    worked_days_line_ids = fields.One2many('hr.payslip.worked_days',
                                           'payslip_id',
                                           string='Días Laborados',
                                           copy=True, readonly=True,
                                           help="Nómina Días Laborados",
                                           states={
                                               'draft': [('readonly', False)]})
    input_line_ids = fields.One2many('hr.payslip.input', 'payslip_id',
                                     string='Entradas de nómina',
                                     readonly=True,
                                     states={'draft': [('readonly', False)]})
    paid = fields.Boolean(string='¿Orden de pago realizada? ', readonly=True,
                          copy=False,
                          states={'draft': [('readonly', False)]})
    note = fields.Text(string='Notas internas', readonly=True,
                       states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Contrato',
                                  readonly=True, help="Contrato",
                                  states={'draft': [('readonly', False)]})
    details_by_salary_rule_category = fields.One2many('hr.payslip.line',
                                                      compute='_compute_details_by_salary_rule_category',
                                                      string='Detalles por categoría de regla salarial',
                                                      help="Detalles por categoría de regla salarial")
    credit_note = fields.Boolean(string='Nota de credito', readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 help="Indica que esta nómina tiene un reembolso de otro")
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Lotes de nóminas',
                                     readonly=True,
                                     copy=False,
                                     states={'draft': [('readonly', False)]})
    payslip_count = fields.Integer(compute='_compute_payslip_count',
                                   string="Detalles del cálculo del recibo de nómina")

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if self.contract_id.salary_type == 'quincenal':
            self.total_payment = self.contract_id.wage / 2
        else:
            self.total_payment = self.contract_id.wage

    def action_send_email(self):
        res = self.env.user.has_group(
            'hr_payroll_community.group_hr_payroll_community_manager')
        if res:
            email_values = {
                'email_from': self.env.user.work_email,
                'email_to': self.employee_id.work_email,
                'subject': self.name
            }
            mail_template = self.env.ref(
                'hr_payroll_community.payslip_email_template').sudo()

            mail_template.send_mail(self.id, force_send=True,
                                    email_values=email_values)

    def _compute_total_payment(self):
        if self.contract_id.salary_type == 'quincenal':
            self.total_payment = self.contract_id.wage / 2
        else:
            self.total_payment = self.contract_id.wage

    def _compute_details_by_salary_rule_category(self):
        for payslip in self:
            payslip.details_by_salary_rule_category = payslip.mapped(
                'line_ids').filtered(lambda line: line.category_id)

    def _compute_payslip_count(self):
        for payslip in self:
            payslip.payslip_count = len(payslip.line_ids)

    def _compute_payslip_name(self):
        for payslip in self:
            payslip.name = f"Nomina de {payslip.employee_id.name} para el periodo de {payslip.date_from} - {payslip.date_to}"

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):

        if any(self.filtered(
                lambda payslip: payslip.date_from > payslip.date_to)):
            raise ValidationError(
                _("La 'Fecha desde' del recibo de nómina debe ser anterior a la 'Fecha hasta'."))

    def action_payslip_draft(self):
        return self.write({'state': 'draft'})

    def action_payslip_done(self):
        self.compute_sheet()
        return self.write({'state': 'done'})

    def action_payslip_cancel(self):
        return self.write({'state': 'cancel'})

    def refund_sheet(self):
        for payslip in self:
            copied_payslip = payslip.copy(
                {'credit_note': True, 'name': _('Refund: ') + payslip.name})
            copied_payslip.compute_sheet()
            copied_payslip.action_payslip_done()
        formview_ref = self.env.ref('hr_payroll_community.view_hr_payslip_form',
                                    False)
        treeview_ref = self.env.ref('hr_payroll_community.view_hr_payslip_tree',
                                    False)
        return {
            'name': ("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % copied_payslip.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }

    def check_done(self):

        return True

    def unlink(self):

        if any(self.filtered(
                lambda payslip: payslip.state not in ('draft', 'cancel'))):
            raise UserError(
                _('¡No se puede eliminar una nómina que no esté girada o cancelada!'))
        return super(HrPayslip, self).unlink()

    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: registro de los empleados
        @param date_from: campo de fecha
        @param date_to: campo de fecha
        @return: devuelve los identificadores de todos los contratos para el empleado determinado que deben considerarse para las fechas dadas
        """
        # un contrato es válido si finaliza entre las fechas indicadas
        clause_1 = ['&', ('date_end', '<=', date_to),
                    ('date_end', '>=', date_from)]
        # O si comienza entre las fechas indicadas
        clause_2 = ['&', ('date_start', '<=', date_to),
                    ('date_start', '>=', date_from)]
        # O si comienza antes de la fecha_desde y termina después de la fecha_fin (o nunca termina)
        clause_3 = ['&', ('date_start', '<=', date_from), '|',
                    ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id),
                        ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    def compute_sheet(self):
        for payslip in self:
            deduccion = 0
            acreditacion = 0
            sueldo = 0

            number = payslip.number or self.env['ir.sequence'].next_by_code(
                'salary.slip')
            # eliminar líneas antiguas de nómina
            payslip.line_ids.unlink()
            # establecer la lista de contratos a los que se deben aplicar las reglas
            # Si no se encuentra el contrato, entonces las reglas a aplicar deberían ser para todos los contratos actuales del empleado.
            contract_ids = payslip.contract_id.ids or \
                self.get_contract(payslip.employee_id,
                                  payslip.date_from, payslip.date_to)
            lines = [(0, 0, line) for line in
                     self._get_payslip_lines(contract_ids, payslip.id)]

            # Actualizar el sueldo neto
            for line in lines:
                for input in self.input_line_ids:
                    if line[2]['code'] == input.code:
                        line[2]['amount'] = input.amount
                        if self.env['hr.salary.rule.category'].search([('id', '=', line[2]['category_id'])]).code == 'DED':
                            deduccion -= input.amount
                        elif self.env['hr.salary.rule.category'].search([('id', '=', line[2]['category_id'])]).code == 'ALW':
                            acreditacion += input.amount

            payslip.write({'line_ids': lines, 'number': number,
                          'deduction': deduccion, 'accreditation': acreditacion})
        return True

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Explorar registro de contratos
        @return: devuelve una lista de dictados que contiene la entrada que se debe aplicar para el contrato dado entre date_from y date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(
                lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from),
                                        time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to),
                                      time.max)

            day_leave_intervals = []

            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            """day_leave_intervals = contract.employee_id.list_leaves(day_from,
                                                                   day_to,
                                                                   calendar=contract.resource_calendar_id)"""
            permisos = self.env['hr.leave'].search(['&', '&', '&',
                                                    ('employee_id', '=',
                                                     self.employee_id.id),
                                                    ('state', '=', 'validate'),
                                                    ('request_date_from',
                                                     '>=', self.date_from),
                                                    ('request_date_to',
                                                     '<=', self.date_to),
                                                    ])
            day_leave_intervals = contract.employee_id.list_leaves(day_from,
                                                                   day_to,
                                                                   calendar=contract.resource_calendar_id)

            multi_leaves = []
            for day, hours, leave in day_leave_intervals:
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if len(leave) > 1:
                    for each in leave:
                        if each.id:
                            multi_leaves.append(each.holiday_id)
                else:

                    holiday = leave[0].holiday_id
                    current_leave_struct = leaves.setdefault(
                        holiday.holiday_status_id, {
                            'name': holiday.holiday_status_id.name or _(
                                'Permisos con deducción de sueldo'),
                            'sequence': 5,
                            'code': 'PRM',
                            'number_of_days': 0.0,
                            'number_of_hours': 0.0,
                            'contract_id': contract.id,
                        })
                    current_leave_struct['number_of_hours'] += hours
                    if work_hours:
                        current_leave_struct[
                            'number_of_days'] += hours / work_hours

            # compute worked days
            work_data = contract.employee_id.get_work_days_data(day_from,
                                                                day_to,
                                                                calendar=contract.resource_calendar_id)
            attendances = {
                'name': _("Días de trabajo normales pagados al 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }
            res.append(attendances)

            uniq_leaves = [*set(multi_leaves)]
            c_leaves = {}
            for rec in uniq_leaves:
                c_leaves.setdefault(rec.holiday_status_id,
                                    {'hours': float(
                                        rec.duration_display.replace(
                                            "hours",
                                            "")), })
            flag = 1
            for item in c_leaves:
                if not leaves:
                    data = {
                        'name': item.name,
                        'sequence': 20,
                        'code': 'LEAVES',
                        'number_of_hours': c_leaves[item]['hours'],
                        'number_of_days': c_leaves[item][
                            'hours'] / work_hours,
                        'contract_id': contract.id,
                    }
                    res.append(data)

                for time_off in leaves:
                    if item == time_off:
                        leaves[item]['number_of_hours'] += c_leaves[item][
                            'hours']
                        leaves[item]['number_of_days'] += c_leaves[item][
                            'hours'] / work_hours
                    if item not in leaves and flag == 1:
                        data = {
                            'name': item.name,
                            'sequence': 20,
                            'code': holiday.holiday_status_id.code or 'GLOBAL',
                            'number_of_hours': c_leaves[item]['hours'],
                            'number_of_days': c_leaves[item][
                                'hours'] / work_hours,
                            'contract_id': contract.id,
                        }
                        res.append(data)
                        flag = 0

            res.extend(leaves.values())
        return res

    @api.model
    def get_inputs(self, contracts, date_from, date_to):

        res = []

        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in
                           sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped(
            'input_ids')

        for contract in contracts:
            for input in inputs:
                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'amount': 0.0,
                    'contract_id': contract.id,
                }
                res += [input_data]
        return res

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):

        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict,
                                                      category.parent_id,
                                                      amount)
            localdict['categories'].dict[category.code] = category.code in \
                localdict[
                'categories'].dict and \
                localdict[
                'categories'].dict[
                category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict, env):
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(amount) as sum
                    FROM hr_payslip as hp, hr_payslip_input as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (
                                        self.employee_id, from_date, to_date,
                                        code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (
                                        self.employee_id, from_date, to_date,
                                        code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                            FROM hr_payslip as hp, hr_payslip_line as pl
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                                    (
                                        self.employee_id, from_date, to_date,
                                        code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        # we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict,
                                 self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)

        baselocaldict = {'categories': categories, 'rules': rules,
                         'payslip': payslips, 'worked_days': worked_days,
                         'inputs': inputs}
        # get the ids of the structures on the contracts and their parent id as well
        contracts = self.env['hr.contract'].browse(contract_ids)
        if len(contracts) == 1 and payslip.struct_id:
            structure_ids = list(
                set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in
                           sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee,
                             contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                # check if the rule can be applied
                if rule._satisfy_condition(
                        localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[
                        rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict,
                                                          rule.category_id,
                                                          tot_rule - previous_amount)
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'active': rule.active,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in
                                  rule._recursive_search_of_rules()]

        return list(result_dict.values())

    # YTI TODO To rename. This method is not really an onchange, as it is not in any view
    # employee_id and contract_id could be browse records
    def onchange_employee_id(self, date_from, date_to, employee_id=False,
                             contract_id=False):
        # defaults
        res = {
            'value': {
                'line_ids': [],
                # delete old input lines
                'input_line_ids': [(2, x,) for x in self.input_line_ids.ids],
                # delete old worked days lines
                'worked_days_line_ids': [(2, x,) for x in
                                         self.worked_days_line_ids.ids],
                # 'details_by_salary_head':[], TODO put me back
                'name': '',
                'contract_id': False,
                'struct_id': False,
            }
        }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        employee = self.env['hr.employee'].browse(employee_id)
        locale = self.env.context.get('lang') or 'en_US'
        res['value'].update({
            'name': _('Salary Slip of %s for %s') % (
                employee.name, tools.ustr(
                    babel.dates.format_date(date=ttyme, format='MMMM-y',
                                            locale=locale))),
            'company_id': employee.company_id.id,
        })

        if not self.env.context.get('contract'):
            # fill with the first contract of the employee
            contract_ids = self.get_contract(employee, date_from, date_to)
        else:
            if contract_id:
                # set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
            else:
                # if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(employee, date_from, date_to)

        if not contract_ids:
            return res
        contract = self.env['hr.contract'].browse(contract_ids[0])
        res['value'].update({
            'contract_id': contract.id
        })
        struct = contract.struct_id
        if not struct:
            return res
        res['value'].update({
            'struct_id': struct.id,
        })
        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from,
                                                         date_to)
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        res['value'].update({
            'worked_days_line_ids': worked_days_line_ids,
            'input_line_ids': input_line_ids,
        })
        return res

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):

        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []

        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        locale = self.env.context.get('lang') or 'en_US'
        self.name = _('Salary Slip of %s for %s') % (
            employee.name, tools.ustr(
                babel.dates.format_date(date=ttyme, format='MMMM-y',
                                        locale=locale)))
        self.company_id = employee.company_id

        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = self.get_contract(employee, date_from, date_to)
            if not contract_ids:
                self.worked_days_line_ids = False
                self.contract_id = False
                return
            self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

        if not self.contract_id.struct_id:
            self.worked_days_line_ids = False
            return
        self.struct_id = self.contract_id.struct_id
        if self.contract_id:
            contract_ids = self.contract_id.ids
        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from,
                                                         date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines

        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        return

    @api.onchange('contract_id')
    def onchange_contract(self):

        if not self.contract_id:
            self.struct_id = False
        self.with_context(contract=True).onchange_employee()
        return

    def get_salary_line_total(self, code):

        self.ensure_one()
        line = self.line_ids.filtered(lambda line: line.code == code)
        if line:
            return line[0].total
        else:
            return 0.0


class HrPayslipLine(models.Model):
    _name = 'hr.payslip.line'
    _inherit = 'hr.salary.rule'
    _description = 'Payslip Line'
    _order = 'contract_id, sequence'

    slip_id = fields.Many2one('hr.payslip', string='Nomina', required=True,
                              ondelete='cascade', help="Payslip")
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Regla',
                                     required=True, help="Regla de salarial")
    employee_id = fields.Many2one('hr.employee', string='Empleado',
                                  required=True, help="Empleado")
    # category_id = fields.Many2one(related='salary_rule_id.category_id', string='Category', required=True)
    contract_id = fields.Many2one('hr.contract', string='Contrato',
                                  required=True, index=True, help="Contrato")
    rate = fields.Float(string='Taza (%)',
                        digits=dp.get_precision('Payroll Rate'), default=100.0)
    amount = fields.Float(digits=dp.get_precision('Payroll'))
    quantity = fields.Float(digits=dp.get_precision('Payroll'), default=1.0)
    total = fields.Float(compute='_compute_total', string='Total', help="Total",
                         digits=dp.get_precision('Payroll'), store=True)

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):

        for line in self:
            line.total = float(line.quantity) * line.amount * line.rate / 100

    @api.model_create_multi
    def create(self, vals_list):
        deducciones = 0
        acreditaciones = 0
        sueldo = 0

        for values in vals_list:
            categoria = self.env['hr.salary.rule.category'].search(
                [('id', '=', values['category_id'])])
            payslip = self.env['hr.payslip'].browse(values.get('slip_id'))
            pay = payslip.total_payment
            if 'employee_id' not in values or 'contract_id' not in values:
                values['employee_id'] = values.get(
                    'employee_id') or payslip.employee_id.id
                values['contract_id'] = values.get(
                    'contract_id') or payslip.contract_id and payslip.contract_id.id
                if not values['contract_id']:
                    raise UserError(
                        _('Debe establecer un contrato para crear una línea de recibo de planilla.'))
            # Aqui se hacen los calculos de el calculo de la nomina
            if values['active'] == True:
                if values['amount_select'] == 'percentage':
                    if categoria.code == 'DED':
                        pay -= (values['amount_percentage']
                                * payslip.total_payment / 100)
                        sueldo = pay
                    if categoria.code == 'ALW':
                        pay += (values['amount_percentage']
                                * payslip.total_payment / 100)
                        sueldo = pay
                    if values['code'] == 'SLDBT':
                        if payslip.contract_id.salary_type == 'quincenal':
                            values['amount_fix'] = payslip.contract_id.wage / 2
                        else:
                            values['amount_fix'] = payslip.contract_id.wage
                        values['amount'] = values['amount_fix']
                else:
                    if categoria.code == 'DED':
                        pay -= values['amount_fix']
                        sueldo = pay
                    if categoria.code == 'ALW':
                        pay += values['amount_fix']
                        sueldo = pay
                    if values['code'] == 'SLDBT':
                        if payslip.contract_id.salary_type == 'quincenal':
                            values['amount_fix'] = payslip.contract_id.wage / 2
                        else:
                            values['amount_fix'] = payslip.contract_id.wage
                        values['amount'] = values['amount_fix']

        for value in vals_list:
            deduccione = 0
            payslip = self.env['hr.payslip'].browse(value.get('slip_id'))
            if value['active'] == True:
                if value['code'] == 'SLDNT':
                    if payslip.deduction < 0:
                        deduccione = -1 * payslip.deduction
                    value['amount_fix'] = sueldo - \
                        deduccione + payslip.accreditation
                    value['amount'] = value['amount_fix']
                    self.slip_id.write(
                        {'total_payment': sueldo - payslip.deduction + payslip.accreditation})
                    break

        return super(HrPayslipLine, self).create(vals_list)

    def write(self, values):
        # Lógica para actualizar el sueldo neto en la nómina cuando se edita amount o sueldo
        for line in self:
            payslip = line.slip_id
            categoria = line.category_id
            # Si se edita el campo amount
            for rule in payslip.line_ids:
                if rule.code == 'SLDNT':
                    if 'amount' in values:
                        if categoria.code == 'DED':
                            rule.amount -= (values['amount'])
                            payslip.write({'total_payment': rule.amount})
                        elif categoria.code == 'ALW':
                            rule.amount += (values['amount'])
                            payslip.write({'total_payment': rule.amount})
        # Llamar al método write original para guardar los cambios
        result = super(HrPayslipLine, self).write(values)
        return result


class HrPayslipWorkedDays(models.Model):
    _name = 'hr.payslip.worked_days'
    _description = 'Payslip Worked Days'
    _order = 'payslip_id, sequence'

    name = fields.Char(string='Descripción', required=True)
    payslip_id = fields.Many2one('hr.payslip', string='Nomina', required=True,
                                 ondelete='cascade', index=True, help="Nomina")
    sequence = fields.Integer(required=True, index=True, default=10,
                              help="Sequence")
    code = fields.Char(required=True, string="Codigo",
                       help="The code that can be used in the salary rules")
    number_of_days = fields.Float(string='Numero de dias',
                                  help="Number of days worked")
    number_of_hours = fields.Float(string='Numero de horas',
                                   help="Number of hours worked")
    contract_id = fields.Many2one('hr.contract', string='Contrato',
                                  required=True,)


class HrPayslipInput(models.Model):
    _name = 'hr.payslip.input'
    _description = 'Payslip Input'
    _order = 'payslip_id, sequence'

    name = fields.Char(string='Descripción', required=True)
    payslip_id = fields.Many2one('hr.payslip', string='Nomina', required=True,
                                 ondelete='cascade', help="Nomina", index=True)
    sequence = fields.Integer(required=True, index=True, default=10,
                              help="Sequence")
    code = fields.Char(required=True, string="Codigo",
                       help="El código que se puede utilizar en las reglas salariales")
    amount = fields.Float(string="Monto")
    contract_id = fields.Many2one('hr.contract', string='Contrato',
                                  required=True,
                                  help="El contrato para el cual se aplicó esta entrada")


class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _description = 'Payslip Batches'

    name = fields.Char(required=True, readonly=True, string="Nombre",
                       states={'draft': [('readonly', False)]})
    slip_ids = fields.One2many('hr.payslip', 'payslip_run_id',
                               string='Nominas', readonly=True,
                               states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Close'),
    ], string='Estado', index=True, readonly=True, copy=False, default='draft')
    date_start = fields.Date(string='Fecha desde', required=True, readonly=True,
                             help="Fecha desde",
                             states={'draft': [('readonly', False)]},
                             default=lambda self: fields.Date.to_string(
                                 date.today().replace(day=1)))
    date_end = fields.Date(string='Fecha hasta', required=True, readonly=True,
                           help="Fecha hasta",
                           states={'draft': [('readonly', False)]},
                           default=lambda self: fields.Date.to_string(
                               (datetime.now() + relativedelta(months=+1, day=1,
                                                               days=-1)).date()))
    credit_note = fields.Boolean(string='Nota de credito', readonly=True,
                                 states={'draft': [('readonly', False)]},)
    is_validate = fields.Boolean(compute='_compute_is_validate')

    hours_lv = [
        ('6', '6:00 AM'), ('6.25', '6:15 AM'), ('6.5',
                                                '6:30 AM'), ('6.75', '6:45 AM'),
        ('7', '7:00 AM'), ('7.25', '7:15 AM'), ('7.5',
                                                '7:30 AM'), ('7.75', '7:45 AM'),
        ('8', '8:00 AM'), ('8.25', '8:15 AM'), ('8.5',
                                                '8:30 AM'), ('8.75', '8:45 AM'),
        ('9', '9:00 AM'), ('9.25', '9:15 AM'), ('9.5',
                                                '9:30 AM'), ('9.75', '9:45 AM'),
        ('10', '10:00 AM'), ('10.25', '10:15 AM'), ('10.5',
                                                    '10:30 AM'), ('10.75', '10:45 AM'),
        ('11', '11:00 AM'), ('11.25', '11:15 AM'), ('11.5',
                                                    '11:30 AM'), ('11.75', '11:45 AM'),
        ('12', '12:00 PM'), ('12.25', '12:15 PM'), ('12.5',
                                                    '12:30 PM'), ('12.75', '12:45 PM'),
        ('13', '1:00 PM'), ('13.25', '1:15 PM'), ('13.5',
                                                  '1:30 PM'), ('13.75', '1:45 PM'),
        ('14', '2:00 PM'), ('14.25', '2:15 PM'), ('14.5',
                                                  '2:30 PM'), ('14.75', '2:45 PM'),
        ('15', '3:00 PM'), ('15.25', '3:15 PM'), ('15.5',
                                                  '3:30 PM'), ('15.75', '3:45 PM'),
        ('16', '4:00 PM'), ('16.25', '4:15 PM'), ('16.5',
                                                  '4:30 PM'), ('16.75', '4:45 PM'),
        ('17', '5:00 PM'), ('17.25', '5:15 PM'), ('17.5',
                                                  '5:30 PM'), ('17.75', '5:45 PM'),
        ('18', '6:00 PM')
    ]

    def draft_payslip_run(self):
        return self.write({'state': 'draft'})

    def close_payslip_run(self):
        return self.write({'state': 'close'})

    def action_validate_payslips(self):
        if self.slip_ids:
            for slip in self.slip_ids.filtered(
                    lambda slip: slip.state == 'draft'):
                slip.action_payslip_done()

    def _compute_is_validate(self):
        for record in self:
            if record.slip_ids and record.slip_ids.filtered(
                    lambda slip: slip.state == 'draft'):
                record.is_validate = True
            else:
                record.is_validate = False

    def calcular_llegadat(self, in_time, dia_permiso, calendario_id, salario):
        costo_dia = salario / 30
        costo_hora = costo_dia / 8
        deduccion = 0

        working_hours = self.env['resource.calendar.attendance'].search([
            ('calendar_id', '=', calendario_id),
            ('dayofweek', '=', str(dia_permiso)),
            ('day_period', '=', 'morning')
        ])

        for hours in working_hours:
            start_time = datetime.strptime(
                f"{int(hours.hour_from)}:00:00", '%H:%M:%S').time()
            start_datetime = datetime.combine(datetime.today(), start_time)

            # Rango de deducción según minutos de retraso
            diff_minutes = (datetime.combine(datetime.today(),
                            in_time) - start_datetime).total_seconds() / 60

            if 7 < diff_minutes <= 15:
                deduccion = costo_hora / 2
            elif 15 < diff_minutes <= 30:
                deduccion = costo_hora
            elif 30 < diff_minutes <= 60:
                deduccion = costo_hora * 2
            elif 60 < diff_minutes <= 90:
                deduccion = costo_hora * 4

        return deduccion

    def exportar_excel_deducciones(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        data_ded_prm = []
        data_ded_ast = []

        # Crear hojas de Excel
        worksheet_asistencias = workbook.add_worksheet(
            'Deducciones de asistencias')
        worksheet_permisos = workbook.add_worksheet('Deducciones de permisos')

        # Definir formatos
        currency_format = workbook.add_format(
            {'num_format': 'L#,##0.00', 'align': 'center'})
        number_format = workbook.add_format(
            {'num_format': '#,##0', 'align': 'center'})
        header_format = workbook.add_format({'bold': True, 'align': 'center'})
        date_format = workbook.add_format(
            {'num_format': 'dd-mm-yyyy', 'align': 'center'})
        datetime_format = workbook.add_format(
            {'num_format': 'hh:mm:ss', 'align': 'center'})

        # Función para escribir encabezados y datos en una hoja y ajustar el tamaño de las columnas
        def escribir_hoja(worksheet, encabezados, datos, col_widths, formatos):
            # Ajustar el tamaño de las columnas
            for col, width in enumerate(col_widths):
                worksheet.set_column(col, col, width)

            # Escribir los encabezados
            for col, encabezado in enumerate(encabezados):
                worksheet.write(0, col, encabezado, header_format)

            # Escribir los datos
            row = 1
            for record in datos:
                for col, value in enumerate(record):
                    worksheet.write(row, col, value, formatos[col])
                row += 1

        # Encabezados y anchos de columnas
        encabezados_asistencias_reports = [
            'Empleado', 'Fecha de asistencia', 'Hora de asistencia', 'Dia de asistencia', 'Deducción']
        # Ajusta estos valores según sea necesario
        col_widths_asistencias_reports = [50, 25, 25, 25, 20]
        formatos_asistencias_reports = [
            None, date_format, datetime_format, None, currency_format]  # Formatos para cada columna

        encabezados_reports_permisos = ['Empleado', 'fecha inicio', 'fecha final',
                                        'jornada', 'Hora inicio', 'Hora final', 'deduccion', 'Monto']
        # Ajusta estos valores según sea necesario
        col_widths_reports_permisos = [50, 25, 25, 20, 25, 25, 25, 25]
        formatos_reports_permisos = [None, date_format, date_format, None, datetime_format,
                                     datetime_format, None, number_format]  # Formatos para cada columna

        # Preparar los datos
        for slip_id in self.slip_ids:
            employee = slip_id.employee_id
            contract_id = slip_id.contract_id
            date_from = slip_id.date_from
            date_to = slip_id.date_to
            costo_dia = contract_id.wage / 30
            costo_hora = costo_dia / 8
            costo_minuto = costo_hora / 60
            

            # Obtener permisos (leaves)
            leaves = employee.list_leaves(
                datetime.combine(fields.Date.from_string(date_from), time.min),
                datetime.combine(fields.Date.from_string(date_to), time.max),
                calendar=contract_id.resource_calendar_id
            )

            # Agregar deducciones por permisos con marca 'deducciones'
            for day, hours, leave_list in leaves:
                for leave in leave_list:
                    hora_permiso_init = ''
                    hora_permiso_fin = ''
                    if leave.holiday_id.holiday_status_id.deducciones:
                        total = leave.holiday_id.dias * costo_dia + leave.holiday_id.horas * \
                            costo_hora + leave.holiday_id.minutos * costo_minuto
                        
                        for hora in self.hours_lv:
                            if leave.holiday_id.request_hour_from_1 == hora[0]:
                                hora_permiso_init = hora[1]
                                break
                        for hora in self.hours_lv:
                            if leave.holiday_id.request_hour_to_1 == hora[0]:
                                hora_permiso_fin = hora[1]
                                break
                        permiso = {
                            'Empleado': leave.holiday_id.employee_id.name,
                            'fecha inicio': leave.holiday_id.request_date_from,
                            'fecha final': leave.holiday_id.request_date_to,
                            'jornada': leave.holiday_id.request_date_from_period if leave.holiday_id.request_unit_half else 'N/A',
                            'Hora inicio': hora_permiso_init if leave.holiday_id.request_unit_hours else 'N/A',
                            'Hora final': hora_permiso_fin if leave.holiday_id.request_unit_hours else 'N/A',
                            'deduccion': leave.holiday_id.holiday_status_id.name,
                            'Monto': total,
                        }
                        data_ded_prm.append(permiso)

            # Obtener asistencias
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', date_from),
                ('check_out', '<=', date_to)
            ])

            for attendance in attendances:
                check_in_local = attendance.check_in.astimezone(honduras_tz)
                in_date = check_in_local.date()
                in_time = check_in_local.time()
                dia_semana = in_date.weekday()
                dias_de_semana = [('0', 'Lunes'), ('1', 'Martes'), ('2', 'Miercoles'), ('3', 'Jueves'), ('4', 'Viernes'), ('5', 'Sabado')]

                # Verificamos si ese día tiene permisos
                permiso_encontrado = False
                for day, hours, leave_list in leaves:
                    if day == in_date:
                        for leave in leave_list:
                            permiso_encontrado = True
                            # Día completo: no calcular deducción
                            if leave.holiday_id.request_unit_half and leave.holiday_id.request_date_from_period == 'am':
                                # Permiso por la mañana: no calcular deducción
                                _logger.info(
                                    "Permiso por la mañana, no se aplica deducción")
                                continue
                            elif leave.holiday_id.request_unit_half and leave.holiday_id.request_date_from_period == 'pm':
                                # Permiso por la tarde: sí aplica si llegó tarde en la mañana
                                amount = self.calcular_llegadat(
                                    in_time, dia_semana, contract_id.resource_calendar_id.id, contract_id.wage)
                                if amount > 0:
                                    asistencia = {
                                        'Empleado': attendance.employee_id.name,
                                        'fecha': in_date,
                                        'Hora': in_time,
                                        'dia': dias_de_semana[int(dia_semana)][1],
                                        'deducción': amount
                                    }
                                    data_ded_ast.append(asistencia)
                            elif leave.holiday_id.request_unit_hours:
                                # Permiso por horas
                                permiso_inicio = datetime.combine(
                                    day, time(hour=int(float(leave.holiday_id.request_hour_from_1))))
                                permiso_fin = datetime.combine(
                                    day, time(hour=int(float(leave.holiday_id.request_hour_to_1))))

                                entrada_datetime = datetime.combine(
                                    day, in_time)
                                # Si entró antes del permiso, no se deduce
                                if entrada_datetime < permiso_inicio:
                                    amount = self.calcular_llegadat(
                                        in_time, dia_semana, contract_id.resource_calendar_id.id, contract_id.wage)
                                    if amount > 0:
                                        asistencia = {
                                            'Empleado': attendance.employee_id.name,
                                            'fecha': in_date,
                                            'Hora': in_time,
                                            'dia': dias_de_semana[int(dia_semana)][1],
                                            'deducción': amount
                                        }
                                        data_ded_ast.append(asistencia)
                                else:
                                    _logger.info(
                                        "Entró durante el permiso por horas, no se aplica deducción")
                                    continue
                            else:
                                # Día completo
                                _logger.info(
                                    "Permiso por el día completo, no se aplica deducción")
                                continue

                if not permiso_encontrado:
                    # No hay permiso → aplicar lógica de llegada tarde
                    amount = self.calcular_llegadat(
                        in_time, dia_semana, contract_id.resource_calendar_id.id, contract_id.wage)
                    if amount > 0:
                        asistencia = {
                            'Empleado': attendance.employee_id.name,
                            'fecha': in_date,
                            'Hora': in_time,
                            'dia': dias_de_semana[int(dia_semana)][1],
                            'deducción': amount
                        }
                        data_ded_ast.append(asistencia)

        datos_lines_asistencias = [
            (
                record['Empleado'],
                record['fecha'],
                record['Hora'],
                record['dia'],
                record['deducción'],
            )
            for record in data_ded_ast
        ]

        datos_lines_permisos = [
            (
                record['Empleado'],
                record['fecha inicio'],
                record['fecha final'],
                record['jornada'],
                record['Hora inicio'],
                record['Hora final'],
                record['deduccion'],
                record['Monto']

            )
            for record in data_ded_prm
        ]

        # Escribir datos en las hojas correspondientes y ajustar el tamaño de las columnas
        escribir_hoja(worksheet_asistencias, encabezados_asistencias_reports,
                      datos_lines_asistencias, col_widths_asistencias_reports, formatos_asistencias_reports)
        escribir_hoja(worksheet_permisos, encabezados_reports_permisos,
                      datos_lines_permisos, col_widths_reports_permisos, formatos_reports_permisos)

        workbook.close()
        output.seek(0)

        # Crear el adjunto
        attachment = self.env['ir.attachment'].create({
            'name': f'reporte_de_deducciones_de_planilla_del_{self.date_start}_{self.date_end}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'store_fname': f'reporte_de_deducciones_de_planilla_del_{self.date_start}_{self.date_end}.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Devolver la acción para descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def exportar_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        encabezados_rules_code = []
        encabezados_rules_names = []
        datos_row = []
        col_widths_lines_rule = []

        # Crear hojas de Excel
        worksheet_lines_from_customer = workbook.add_worksheet(
            'Resumen de planilla')

        formato_total = workbook.add_format({
            'bold': True,
            # Gris claro (puedes usar '#FFFF00' para amarillo)
            'bg_color': '#D9D9D9',
            'border': 1
        })

        formato_encabezado = workbook.add_format({
            'bold': True,
            'bg_color': '#00A6CB',
        })

        # Función para escribir encabezados y datos en una hoja y ajustar el tamaño de las columnas
        def escribir_hoja(worksheet, encabezados, datos, col_widths):
            # Ajustar el tamaño de las columnas
            for col, width in enumerate(col_widths):
                worksheet.set_column(col, col, width)

            # Escribir los encabezados
            for col, encabezado in enumerate(encabezados):
                worksheet.write(0, col, encabezado, formato_encabezado)

            # Escribir los datos
            row = 1
            for record in datos:
                if str(record[0]).strip().upper() == "TOTAL":
                    for col, value in enumerate(record):
                        worksheet.write(row, col, value, formato_total)
                else:
                    for col, value in enumerate(record):
                        worksheet.write(row, col, value)
                row += 1

        for slip_id in self.slip_ids:
            reglas = []
            # Obtener encabezados y anchos de columnas, siempre y cuando no se repitan
            # Se obtienen igual el monto de las reglas y el nombre
            for rule in slip_id.line_ids:
                if rule.code not in encabezados_rules_code:
                    encabezados_rules_code.append(rule.code)
                    encabezados_rules_names.append(rule.name)
                    col_widths_lines_rule.append(20)
                reglas.append((rule.name, rule.amount))
            # Obtener nombre del empleado y departamento donde trabaja
            reglas = sorted(reglas, key=lambda x: x[0])
            datos_row.append({"Empleado": slip_id.employee_id.name,
                             "Departamento": slip_id.employee_id.department_id.name, "Reglas": reglas})
        # Encabezados y anchos de columnas
        encabezados_rules_names = sorted(encabezados_rules_names)
        encabezados_lines_customer = ["Empleado",
                                      "Departamento"] + encabezados_rules_names
        # Ajusta estos valores según sea necesari
        col_widths_lines_customer = [40, 30, ] + col_widths_lines_rule
        # Preparar los datos
        data_rules = encabezados_rules_names
        data = []
        for datos in datos_row:
            data_line = []
            data_line.append(datos['Empleado'])
            data_line.append(datos['Departamento'])
            valores_dict = dict(datos['Reglas'])
            resultados = [valores_dict.get(c, 0)
                          for c in encabezados_rules_names]
            for rest in resultados:
                data_line.append(rest)
            data.append(data_line)

        # Agrupar por departamento y calcular totales
        departamento_data = defaultdict(list)
        for line in data:
            departamento = line[1]
            _logger.warning("departamento: %s", departamento)
            if departamento != 'Desarrollo':
                if departamento != 'Mercadeo':
                    departamento_data[departamento].append(line)

        datos_lines_from_customer = []

        for departamento in sorted(departamento_data.keys()):
            grupo = departamento_data[departamento]
            datos_lines_from_customer.extend(grupo)

            # Calcular suma por columna
            totales = ["TOTAL", departamento]
            num_cols = len(grupo[0])
            for i in range(2, num_cols - 1):  # Dejar columnas intermedias en blanco
                totales.append('')

            # Sumar solo la última columna
            suma_final = sum(row[-1] for row in grupo)
            totales.append(suma_final)

            datos_lines_from_customer.append(
                tuple(totales))  # Insertar fila de total

        # Escribir datos en las hojas correspondientes y ajustar el tamaño de las columnas
        escribir_hoja(worksheet_lines_from_customer, encabezados_lines_customer,
                      datos_lines_from_customer, col_widths_lines_customer)

        workbook.close()
        output.seek(0)

        # Crear el adjunto
        attachment = self.env['ir.attachment'].create({
            'name': 'resumen_planilla.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'store_fname': 'resumen_planilla.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Devolver la acción para descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def exportar_excel_kreativa(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        encabezados_rules_code = []
        encabezados_rules_names = []
        datos_row = []
        col_widths_lines_rule = []

        # Crear hojas de Excel
        worksheet_lines_from_customer = workbook.add_worksheet(
            'Resumen de planilla')

        formato_total = workbook.add_format({
            'bold': True,
            # Gris claro (puedes usar '#FFFF00' para amarillo)
            'bg_color': '#D9D9D9',
            'border': 1
        })

        formato_encabezado = workbook.add_format({
            'bold': True,
            'bg_color': '#00A6CB',
        })

        # Función para escribir encabezados y datos en una hoja y ajustar el tamaño de las columnas
        def escribir_hoja(worksheet, encabezados, datos, col_widths):
            # Ajustar el tamaño de las columnas
            for col, width in enumerate(col_widths):
                worksheet.set_column(col, col, width)

            # Escribir los encabezados
            for col, encabezado in enumerate(encabezados):
                worksheet.write(0, col, encabezado, formato_encabezado)

            # Escribir los datos
            row = 1
            for record in datos:
                if str(record[0]).strip().upper() == "TOTAL":
                    for col, value in enumerate(record):
                        worksheet.write(row, col, value, formato_total)
                else:
                    for col, value in enumerate(record):
                        worksheet.write(row, col, value)
                row += 1

        for slip_id in self.slip_ids:
            reglas = []
            # Obtener encabezados y anchos de columnas, siempre y cuando no se repitan
            # Se obtienen igual el monto de las reglas y el nombre
            for rule in slip_id.line_ids:
                if rule.code not in encabezados_rules_code:
                    encabezados_rules_code.append(rule.code)
                    encabezados_rules_names.append(rule.name)
                    col_widths_lines_rule.append(20)
                reglas.append((rule.name, rule.amount))
            # Obtener nombre del empleado y departamento donde trabaja
            reglas = sorted(reglas, key=lambda x: x[0])
            datos_row.append({"Empleado": slip_id.employee_id.name,
                             "Departamento": slip_id.employee_id.department_id.name, "Reglas": reglas})
        # Encabezados y anchos de columnas
        encabezados_rules_names = sorted(encabezados_rules_names)
        encabezados_lines_customer = ["Empleado",
                                      "Departamento"] + encabezados_rules_names
        # Ajusta estos valores según sea necesari
        col_widths_lines_customer = [40, 30, ] + col_widths_lines_rule
        # Preparar los datos
        data_rules = encabezados_rules_names
        data = []
        for datos in datos_row:
            data_line = []
            data_line.append(datos['Empleado'])
            data_line.append(datos['Departamento'])
            valores_dict = dict(datos['Reglas'])
            resultados = [valores_dict.get(c, 0)
                          for c in encabezados_rules_names]
            for rest in resultados:
                data_line.append(rest)
            data.append(data_line)

        # Agrupar por departamento y calcular totales
        departamento_data = defaultdict(list)
        for line in data:
            departamento = line[1]
            _logger.warning("departamento: %s", departamento)
            if not departamento != 'Desarrollo' or not departamento != 'Mercadeo':
                departamento_data[departamento].append(line)

        datos_lines_from_customer = []

        for departamento in sorted(departamento_data.keys()):
            grupo = departamento_data[departamento]
            datos_lines_from_customer.extend(grupo)

            # Calcular suma por columna
            totales = ["TOTAL", departamento]
            num_cols = len(grupo[0])
            for i in range(2, num_cols - 1):  # Dejar columnas intermedias en blanco
                totales.append('')

            # Sumar solo la última columna
            suma_final = sum(row[-1] for row in grupo)
            totales.append(suma_final)

            datos_lines_from_customer.append(
                tuple(totales))  # Insertar fila de total

        # Escribir datos en las hojas correspondientes y ajustar el tamaño de las columnas
        escribir_hoja(worksheet_lines_from_customer, encabezados_lines_customer,
                      datos_lines_from_customer, col_widths_lines_customer)

        workbook.close()
        output.seek(0)

        # Crear el adjunto
        attachment = self.env['ir.attachment'].create({
            'name': 'resumen_planilla.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'store_fname': 'resumen_planilla.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Devolver la acción para descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


class ResourceMixin(models.AbstractModel):
    _inherit = "resource.mixin"

    def get_work_days_data(self, from_datetime, to_datetime,
                           compute_leaves=True, calendar=None, domain=None):
        """
           Por defecto se utiliza el calendario de recursos, pero puede ser
            cambiado usando el argumento `calendario`.

            `dominio` se utiliza para reconocer las hojas a tomar,
            Ninguno significa valor predeterminado ('time_type', '=', 'leave')

            Devuelve un dict {'días': n, 'horas': h} que contiene el
            cantidad de tiempo de trabajo expresado en días y en horas.
        """
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        # total hours per day: retrieve attendances with one extra day margin,
        # in order to compute the total hours on the first and last days
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = calendar._attendance_intervals_batch(from_full, to_full,
                                                         resource)
        day_total = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_total[start.date()] += (stop - start).total_seconds() / 3600

        # actual hours per day
        if compute_leaves:
            intervals = calendar._work_intervals_batch(from_datetime,
                                                       to_datetime, resource,
                                                       domain)
        else:
            intervals = calendar._attendance_intervals_batch(from_datetime,
                                                             to_datetime,
                                                             resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600

        # compute number of days as quarters
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[
                day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return {
            'days': days,
            'hours': sum(day_hours.values()),
        }
