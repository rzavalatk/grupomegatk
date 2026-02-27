# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import exceptions
from odoo.exceptions import UserError
from odoo import api, fields, models, _


class SalaryAdvance(models.Model):
    """Modelo para gestionar adelantos de salario de empleados.
    
    Permite a los empleados solicitar adelantos de salario antes de la
    fecha de pago regular. Incluye validaciones de límites, períodos
    mínimos entre solicitudes y creación automática de asientos contables.
    
    Attributes:
        name: Secuencia automática del adelanto
        employee_id: Empleado que solicita el adelanto
        date: Fecha de la solicitud
        reason: Justificación del adelanto
        advance: Monto solicitado
        state: Estado del adelanto (borrador, enviado, aprobado, etc.)
        exceed_condition: Indica si excede el límite máximo permitido
    """
    _name = "salary.advance"
    _description = "Adelanto de Salario"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', readonly=True,
                       default=lambda self: 'Adv/',
                       help='Nombre del adelanto de salario.')
    employee_id = fields.Many2one('hr.employee', string='Empleado',
                                  required=True, help="Nombre del empleado")
    date = fields.Date(string='Fecha', required=True,
                       default=lambda self: fields.Date.today(),
                       help="Fecha de envío del adelanto de salario.")
    reason = fields.Text(string='Motivo', help="Motivo de la solicitud de "
                                               "adelanto de salario.")
    currency_id = fields.Many2one('res.currency', string='Moneda',
                                  required=True,
                                  help='Moneda de la compañía.',
                                  default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one('res.company', string='Compañía',
                                 required=True,
                                 help='Compañía del empleado',
                                 default=lambda self: self.env.user.company_id)
    advance = fields.Float(string='Adelanto', required=True,
                           help='El monto solicitado.')
    payment_method_id = fields.Many2one('account.journal',
                                        string='Método de Pago',
                                        help='Método de pago del adelanto'
                                             ' de salario.')
    exceed_condition = fields.Boolean(string='Excede el Máximo',
                                      help="El adelanto es mayor que el "
                                           "porcentaje máximo en la estructura "
                                           "salarial")
    department_id = fields.Many2one('hr.department', string='Departamento',
                                    related='employee_id.department_id',
                                    help='Departamento del empleado.')
    state = fields.Selection([('draft', 'Borrador'),
                              ('submit', 'Enviado'),
                              ('waiting_approval', 'Esperando Aprobación'),
                              ('approve', 'Aprobado'),
                              ('cancel', 'Cancelado'),
                              ('reject', 'Rechazado')], string='Estado',
                             default='draft', track_visibility='onchange',
                             help='Estado del adelanto de salario.')
    debit_id = fields.Many2one('account.account', string='Cuenta de Débito',
                               help='Cuenta de débito del adelanto de salario.')
    credit_id = fields.Many2one('account.account', string='Cuenta de Crédito',
                                help='Cuenta de crédito del adelanto de salario.')
    journal_id = fields.Many2one('account.journal', string='Diario',
                                 help='Diario del adelanto de salario.')
    employee_contract_id = fields.Many2one('hr.contract', string='Contrato',
                                           related='employee_id.contract_id',
                                           help='Contrato activo del '
                                                'empleado.')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Filtra diarios según la compañía seleccionada.
        
        Cuando cambia la compañía, actualiza el dominio del campo journal_id
        para mostrar solo los diarios de la compañía seleccionada.
        
        Returns:
            dict: Diccionario con el dominio para filtrar journal_id
        """
        company = self.company_id
        domain = [('company_id.id', '=', company.id)]
        result = {
            'domain': {
                'journal_id': domain,
            },
        }
        return result

    def action_submit_to_manager(self):
        """Envía el adelanto de salario al gerente para aprobación.
        
        Cambia el estado del adelanto de 'draft' (borrador) a 'submit' (enviado),
        indicando que está listo para revisión por parte del gerente.
        """
        self.state = 'submit'

    def action_cancel(self):
        """Cancela la solicitud de adelanto de salario.
        
        Cambia el estado a 'cancel', indicando que el empleado o
        administrador decidió cancelar la solicitud.
        """
        self.state = 'cancel'

    def action_reject(self):
        """Rechaza la solicitud de adelanto de salario.
        
        Cambia el estado a 'reject', indicando que el gerente o
        departamento de contabilidad rechazó la solicitud.
        """
        self.state = 'reject'

    @api.model
    def create(self, vals):
        """Crea un nuevo adelanto con secuencia automática.
        
        Genera automáticamente el nombre/secuencia del adelanto usando
        ir.sequence antes de crear el registro.
        
        Args:
            vals (dict): Valores del nuevo adelanto
            
        Returns:
            salary.advance: Registro del adelanto creado
        """
        vals['name'] = self.env['ir.sequence'].get('salary.advance.seq') or ' '
        res_id = super(SalaryAdvance, self).create(vals)
        return res_id

    def approve_request(self):
        """Aprueba la solicitud de adelanto con validaciones completas.
        
        Valida múltiples condiciones antes de aprobar:
        1. El empleado debe tener dirección particular configurada
        2. Solo un adelanto por mes por empleado
        3. Debe existir un contrato activo
        4. El monto no debe exceder el salario (salvo autorización)
        5. No debe existir nómina ya calculada para este mes
        6. Debe respetar el período mínimo de días desde la última nómina
        
        Raises:
            UserError: Si alguna validación falla
        """
        # Validar que el empleado tenga dirección particular
        if not self.employee_id.address_id.id:
            raise UserError('Defina dirección particular para el empleado, es decir, '
                            'dirección en información privada del empleado.')
        
        # Buscar adelantos aprobados del mismo empleado
        salary_advance_search = self.search(
            [('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
             ('state', '=', 'approve')])
        current_month = datetime.strptime(str(self.date),
                                          '%Y-%m-%d').date().month
        
        # Validar que no exista otro adelanto en el mismo mes
        for each_advance in salary_advance_search:
            existing_month = datetime.strptime(str(each_advance.date),
                                               '%Y-%m-%d').date().month
            if current_month == existing_month:
                raise UserError('Solo se puede solicitar un adelanto por mes')
        
        # Validar que exista contrato activo
        if not self.employee_contract_id:
            raise UserError('Defina un contrato para el empleado')
        
        # Validar que el monto no exceda el salario
        if (self.advance > self.employee_contract_id.wage
                and not self.exceed_condition):
            raise UserError('El monto del adelanto es mayor al asignado')

        if not self.advance:
            raise UserError('Debe ingresar el monto del adelanto de salario')
        
        # Validar que no exista nómina ya calculada para este mes
        payslip_ids = self.env['hr.payslip'].search(
            [('employee_id', '=', self.employee_id.id),
             ('state', '=', 'done'), ('date_from', '<=', self.date),
             ('date_to', '>=', self.date)])
        if payslip_ids:
            raise UserError("El salario de este mes ya fue calculado")
        
        # Validar período mínimo desde la última nómina
        for slip in self.env['hr.payslip'].search(
                [('employee_id', '=', self.employee_id.id)]):
            slip_moth = datetime.strptime(str(slip.date_from),
                                          '%Y-%m-%d').date().month
            if current_month == slip_moth + 1:
                slip_day = datetime.strptime(str(slip.date_from),
                                             '%Y-%m-%d').date().day
                current_day = datetime.strptime(str(self.date),
                                                '%Y-%m-%d').date().day
                if (current_day - slip_day < self.
                        employee_contract_id.struct_id.advance_date):
                    raise exceptions.UserError(
                        _('La solicitud puede hacerse después de "%s" días '
                          'desde el salario del mes anterior') % self.
                        employee_contract_id.struct_id.advance_date)
        self.state = 'waiting_approval'

    def approve_request_acc_dept(self):
        """Aprueba el adelanto desde contabilidad y crea asiento contable.
        
        Segundo nivel de aprobación desde el departamento de contabilidad.
        Valida los datos contables y crea automáticamente el asiento con:
        - Débito: Cuenta del empleado (adelanto por cobrar)
        - Crédito: Cuenta de tesorería (salida de dinero)
        
        Raises:
            UserError: Si falta configuración contable o hay adelanto duplicado
            
        Returns:
            bool: True si se aprobó correctamente
        """
        # Validar que no exista otro adelanto aprobado en el mismo mes
        salary_advance_search = self.search(
            [('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
             ('state', '=', 'approve')])
        current_month = datetime.strptime(str(self.date),
                                          '%Y-%m-%d').date().month
        for each_advance in salary_advance_search:
            existing_month = datetime.strptime(str(each_advance.date),
                                               '%Y-%m-%d').date().month
            if current_month == existing_month:
                raise UserError('Solo se puede solicitar un adelanto por mes')
        
        # Validar cuentas contables configuradas
        if not self.debit_id or not self.credit_id or not self.journal_id:
            raise UserError("Debe ingresar las cuentas de débito y crédito "
                            "y el diario para aprobar")
        if not self.advance:
            raise UserError('Debe ingresar el monto del adelanto de salario')
        
        # Crear asiento contable para el adelanto
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        for request in self:
            # Cabecera del asiento
            move = {
                'narration': 'Adelanto de Salario de ' + request.employee_id.name,
                'ref': request.name,
                'journal_id': request.journal_id.id,
                'date': time.strftime('%Y-%m-%d'),
            }
            # Línea de débito (adelanto por cobrar al empleado)
            if request.debit_id.id:
                debit_line = (0, 0, {
                    'name': request.employee_id.name,
                    'account_id': request.debit_id.id,
                    'journal_id': request.journal_id.id,
                    'date': time.strftime('%Y-%m-%d'),
                    'debit': request.advance > 0.0 and request.advance or 0.0,
                    'credit': request.advance < 0.0 and -request.advance or 0.0,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
            # Línea de crédito (salida de caja/banco)
            if request.credit_id.id:
                credit_line = (0, 0, {
                    'name': request.employee_id.name,
                    'account_id': request.credit_id.id,
                    'journal_id': request.journal_id.id,
                    'date': time.strftime('%Y-%m-%d'),
                    'debit': request.advance < 0.0 and -request.advance or 0.0,
                    'credit': request.advance > 0.0 and request.advance or 0.0,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2][
                    'debit']
            # Crear y publicar asiento
            move.update({'line_ids': line_ids})
            draft = self.env['account.move'].create(move)
            draft.action_post()
            self.state = 'approve'
            return True
