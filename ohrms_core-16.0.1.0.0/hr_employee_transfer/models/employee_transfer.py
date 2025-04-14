# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class EmployeeTransfer(models.Model):
    _name = 'employee.transfer'
    _description = 'Transferencias de empleados entre compañias o sucursales'
    _order = "id desc"

    def _default_employee(self):
        """
        Devuelve el empleado predeterminado según el ID de usuario actual.

        Busca registros de empleados con un ID de usuario coincidente y devuelve el primer empleado coincidente, 
        o Falso si no se encuentra ninguna coincidencia.

        Devuelve:
        registro hr.employee o Falso
        """
        emp_ids = self.env['hr.employee'].search([
            ('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    name = fields.Char(string='Nombre', help='Dale un nombre a la Transferencia', copy=False, default=lambda self: _('New'), readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, help='Seleccione el empleado que va a transferir')
    old_employee_id = fields.Many2one('hr.employee', string='Antiguo empleado', Help='Detalles del antiguo empleado')
    date = fields.Date(string='Fecha', default=fields.Date.today(), help="Fecha")
    transfer_company_id = fields.Many2one('res.company', string='Transferir a', help="Empresa transferida",copy=False, required=True)
    state = fields.Selection(
        [('draft', 'Nuevo'), ('cancel', 'Cancelado'),
         ('transfer', 'Transferido'), ('done', 'Hecho')],
        string='Estado', readonly=True, copy=False, default='draft',
        help=" * El estado 'Borrador' se utiliza cuando se crea una transferencia y no está confirmada.\n"
             " * El estado de transferido se utiliza cuando el empleado es transferido. Esra en estado abierto hasta que la otra empresa reciba al empleado.\n"
             " * Se cambia a estado hecho cuando el empleado es recibido.\n"
             " * El estado cancelado se utiliza cuando se cancela la transferencia.")
    company_id = fields.Many2one('res.company', string='Compañia', related='employee_id.company_id', help="Compañia")
    note = fields.Text( string='Notas',help="Especificar notas de la transferencia")
    transferred = fields.Boolean(string='Transferido', copy=False, help="Transferido", default=False, compute='_compute_transferred',)
    responsible = fields.Many2one('hr.employee', string='Responsable', default=_default_employee, readonly=True, help="Persona responsable de la transferencia")

    def _compute_transferred(self):
        for rec in self:
            rec.transferred = True if \
                rec.transfer_company_id in rec.env.user.company_ids else False

    def transfer(self):
        if not self.transfer_company_id:
            raise UserError(_(
                'Debes seleccionar la empresa.'))
        if self.transfer_company_id == self.company_id:
            raise UserError(_(
                'No se puede transferir a la misma empresa.'))
        self.state = 'transfer'
        return {
            'warning': {
                'title': _("Warning"),
                'message': _(
                    "Este empleado permanecerá en la misma empresa hasta que"
                    "la empresa transferida que acepta esta solicitud de transferencia"),
            },
        }
    
    """
    Recibir una solicitud de transferencia de empleado y actualizar la información del empleado en consecuencia.

    Este método actualiza la empresa del empleado, crea un nuevo socio y actualiza la dirección del empleado.
    También desactiva el registro del empleado antiguo y crea un nuevo contrato para el empleado transferido.

    Retorna:
        Un diccionario que contiene la acción para mostrar el formulario de contrato para el empleado transferido.
    """
    def receive_employee(self):
        self.old_employee_id = self.employee_id
        emp = self.employee_id.sudo().read(
            ['name', 'private_email', 'gender',
             'identification_id', 'passport_id'])[0]
        del emp['id']
        emp.update({
            'company_id': self.transfer_company_id.id
        })
        new_emp = self.env['hr.employee'].sudo().create(emp)
        if self.employee_id.address_home_id:
            self.employee_id.address_home_id.active = False
        for contract in self.env['hr.contract'].search(
                [('employee_id', '=', self.employee_id.id)]):
            if contract.date_end:
                continue
            else:
                contract.write({'date_end': date.today().strftime(
                    DEFAULT_SERVER_DATE_FORMAT)})
        self.employee_id = new_emp
        self.old_employee_id.sudo().write({'active': False})
        partner = {
            'name': self.employee_id.name,
            'company_id': self.transfer_company_id.id,
        }
        partner_created = self.env['res.partner'].create(partner)
        self.employee_id.sudo().write({'address_home_id': partner_created.id})
        return {
            'name': _('Contract'),
            'view_mode': 'form',
            'res_model': 'hr.contract',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_employee_id': self.employee_id.id,
                        'default_date_start': self.date,
                        'default_emp_transfer': self.id,
                        },
        }

    def cancel_transfer(self):
        self.state = 'cancel'

    @api.model
    def create(self, vals):
        vals['name'] = "Transfer: " + self.env['hr.employee'].browse(
            vals['employee_id']).name
        res = super(EmployeeTransfer, self).create(vals)
        return res
