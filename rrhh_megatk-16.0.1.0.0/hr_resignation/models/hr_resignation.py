# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

date_format = "%Y-%m-%d"
RESIGNATION_TYPE = [('resigned', 'Renuncia normal'),
                    ('fired', 'Despedido por la empresa')]


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _inherit = 'mail.thread'
    _rec_name = 'employee_id'

    name = fields.Char(string='Orden de referencia', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string="Empleado", default=lambda self: self.env.user.employee_id.id, 
                                  help='Nombre del empleado para el cual se crea la solicitud')
    department_id = fields.Many2one('hr.department', string="Departamento", related='employee_id.department_id',
                                    help='Departamento del empleado ')
    resign_confirm_date = fields.Date(string="Fecha de confirmación", help='Fecha en que se confirma la solicitud por parte del trabajador.',
                                      track_visibility="always")
    approved_revealing_date = fields.Date(string="Último día de trabajo del empleado aprobado", track_visibility="always")
    joined_date = fields.Date(string="Fecha de ingreso", store=True,)

    expected_revealing_date = fields.Date(string="Último día de empleado", required=True,)
    reason = fields.Text(string="Razón", required=True, help='Especificar razón para la solicitud')
    notice_period = fields.Char(string="plazo de aviso")
    state = fields.Selection(
        [('draft', 'Borrador'), ('confirm', 'Confirmado'), ('approved', 'Aprobado'), ('cancel', 'Cancelado')],
        string='Estado', default='draft', track_visibility="always")
    resignation_type = fields.Selection(selection=RESIGNATION_TYPE, help="Seleccione el tipo de renuncia: normal "
                                                                         "renuncia o despido por parte de la empresa")
    read_only = fields.Boolean(string="Solo lectura")
    employee_contract = fields.Char(String="Contrato")

    @api.onchange('employee_id')
    @api.depends('employee_id')
    def _compute_read_only(self):
        """ Utilice esta función para verificar si el usuario tiene permiso para cambiar el empleado."""
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('hr.group_hr_user'):
            self.read_only = True
        else:
            self.read_only = False

    @api.onchange('employee_id')
    def set_join_date(self):
        self.joined_date = self.employee_id.joining_date

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.resignation') or _('New')
        res = super(HrResignation, self).create(vals)
        return res

    @api.constrains('employee_id')
    def check_employee(self):
        for rec in self:
            if not self.env.user.has_group('hr.group_hr_user'):
                if rec.employee_id.user_id.id and rec.employee_id.user_id.id != self.env.uid:
                    raise ValidationError(_('No puedes crear solicitudes para otros empleados'))

    @api.onchange('employee_id')
    @api.depends('employee_id')
    def check_request_existence(self):
        # Verificar si ya existe alguna solicitud de renuncia
        for rec in self:
            if rec.employee_id:
                resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
                                                                         ('state', 'in', ['confirm', 'approved'])])
                if resignation_request:
                    raise ValidationError(_('Hay una solicitud de renuncia en confirmado o'
                                            ' estado aprobado para este empleado'))
                if rec.employee_id:
                    no_of_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
                    for contracts in no_of_contract:
                        if contracts.state == 'open':
                            rec.employee_contract = contracts.name
                            rec.notice_period = contracts.notice_days

    @api.constrains('joined_date')
    def _check_dates(self):
        # validando las fechas ingresadas
        for rec in self:
            resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
                                                                     ('state', 'in', ['confirm', 'approved'])])
            if resignation_request:
                raise ValidationError(_('Hay una solicitud de renuncia en confirmado o'
                                        ' estado aprobado para este empleado'))

    def confirm_resignation(self):
        if self.joined_date:
            if self.joined_date >= self.expected_revealing_date:
                raise ValidationError(_('La última fecha del empleado debe ser anterior a la fecha de incorporación.'))
            for rec in self:
                rec.state = 'confirm'
                rec.resign_confirm_date = str(datetime.now())
        else:
            raise ValidationError(_('Por favor, establezca la fecha de incorporación del empleado'))

    def cancel_resignation(self):
        for rec in self:
            rec.state = 'cancel'

    def reject_resignation(self):
        for rec in self:
            rec.state = 'cancel'

    def reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.employee_id.active = True
            rec.employee_id.resigned = False
            rec.employee_id.fired = False

    def approve_resignation(self):
        for rec in self:
            if rec.expected_revealing_date and rec.resign_confirm_date:
                no_of_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
                for contracts in no_of_contract:
                    if contracts.state == 'open':
                        rec.employee_contract = contracts.name
                        rec.state = 'approved'
                        rec.approved_revealing_date = rec.resign_confirm_date + timedelta(days=contracts.notice_days)
                    else:
                        rec.approved_revealing_date = rec.expected_revealing_date
                # Cambio de estado del empleado si renuncia hoy
                if rec.expected_revealing_date <= fields.Date.today() and rec.employee_id.active:
                    rec.employee_id.active = False
                    # Modificar campos en la tabla de empleados con respecto a la renuncia
                    rec.employee_id.resign_date = rec.expected_revealing_date
                    if rec.resignation_type == 'resigned':
                        rec.employee_id.resigned = True
                    else:
                        rec.employee_id.fired = True
                    # Removiendo y desactivando el usuario
                    if rec.employee_id.user_id:
                        rec.employee_id.user_id.active = False
                        rec.employee_id.user_id = None
            else:
                raise ValidationError(_('Por favor, ingrese fechas validas.'))

    def update_employee_status(self):
        resignation = self.env['hr.resignation'].search([('state', '=', 'approved')])
        for rec in resignation:
            if rec.expected_revealing_date <= fields.Date.today() and rec.employee_id.active:
                rec.employee_id.active = False
                # Modificar campos en la tabla de empleados con respecto a la renuncia
                rec.employee_id.resign_date = rec.expected_revealing_date
                if rec.resignation_type == 'resigned':
                    rec.employee_id.resigned = True
                else:
                    rec.employee_id.fired = True
                # Removiendo y desactivando el usuario
                if rec.employee_id.user_id:
                    rec.employee_id.user_id.active = False
                    rec.employee_id.user_id = None


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    resign_date = fields.Date('Fecha de renuncia', readonly=True, help="Fecha de la renuncia")
    resigned = fields.Boolean(string="Resignado", default=False, store=True,
                              help="Si está marcada, el empleado ha renunciado.")
    fired = fields.Boolean(string="Despedido", default=False, store=True, help="Si está marcado, el empleado ha sido despedido.")
