# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# Formato de fecha estándar
date_format = "%Y-%m-%d"

# Tipos de renuncia disponibles
RESIGNATION_TYPE = [('resigned', 'Renuncia Normal'),
                    ('fired', 'Despedido por la empresa')]


class HrResignation(models.Model):
    """Modelo para Renuncias de Recursos Humanos.
    
    Este modelo se utiliza para rastrear las renuncias de empleados,
    gestionando el proceso completo desde la solicitud inicial hasta
    la aprobación y finalización de contratos.
    """
    _name = 'hr.resignation'
    _description = 'Renuncia de RRHH'
    _inherit = 'mail.thread'
    _rec_name = 'employee_id'

    # ===== CAMPOS DEL MODELO =====
    
    name = fields.Char(
        string='Referencia', copy=False,
        readonly=True, index=True,
        default=lambda self: _('Nuevo'))
    employee_id = fields.Many2one(
        'hr.employee', string="Empleado",
        default=lambda self: self.env.user.employee_id.id,
        help='Nombre del empleado para quien se crea la solicitud')
    department_id = fields.Many2one(
        'hr.department', string="Departamento",
        related='employee_id.department_id',
        help='Departamento del empleado')
    resign_confirm_date = fields.Date(
        string="Fecha de Confirmación",
        help='Fecha en que la solicitud es confirmada por el empleado.',
        track_visibility="always")
    approved_revealing_date = fields.Date(
        string="Último Día Aprobado del Empleado",
        help='Fecha en que la solicitud es confirmada por el gerente.',
        track_visibility="always")
    joined_date = fields.Date(
        string="Fecha de Ingreso",
        help='Fecha de ingreso del empleado, es decir, fecha de inicio del primer contrato')
    expected_revealing_date = fields.Date(
        string="Último Día del Empleado",
        required=True,
        help='Fecha solicitada por el empleado en la que dejará la empresa.')
    reason = fields.Text(
        string="Motivo", required=True,
        help='Especifique el motivo de dejar la empresa')
    notice_period = fields.Char(
        string="Período de Preaviso",
        help="Período de preaviso del empleado en días.")
    state = fields.Selection(
        [('draft', 'Borrador'), 
         ('confirm', 'Confirmado'), 
         ('approved', 'Aprobado'),
         ('cancel', 'Rechazado')],
        string='Estado', default='draft', track_visibility="always")
    resignation_type = fields.Selection(
        selection=RESIGNATION_TYPE,
        help="Seleccione el tipo de renuncia: "
             "renuncia normal o despido por la empresa")
    change_employee = fields.Boolean(
        string="Cambiar Empleado",
        compute="_compute_change_employee",
        help="Verifica si el usuario tiene permiso para cambiar el empleado")
    employee_contract = fields.Char(String="Contrato")

    @api.depends('employee_id')
    def _compute_change_employee(self):
        """Verifica si el usuario tiene permiso para cambiar el empleado"""
        res_user = self.env['res.users'].browse(self._uid)
        self.change_employee = res_user.has_group('hr.group_hr_user')

    @api.constrains('employee_id')
    def _check_employee_id(self):
        """Valida que el usuario tenga permiso para crear renuncia del empleado.
        
        Raises:
            ValidationError: Si intenta crear solicitud para otro empleado
        """
        for resignation in self:
            if not self.env.user.has_group('hr.group_hr_user'):
                if (resignation.employee_id.user_id.id and
                        resignation.employee_id.user_id.id != self.env.uid):
                    raise ValidationError(
                        _('No puede crear una solicitud para otros empleados'))

    @api.constrains('joined_date')
    def _check_joined_date(self):
        """Verifica si existe una solicitud de renuncia activa para el empleado.
        
        Raises:
            ValidationError: Si ya existe una renuncia confirmada/aprobada
        """
        for resignation in self:
            resignation_request = self.env['hr.resignation'].search(
                [('employee_id', '=', resignation.employee_id.id),
                 ('state', 'in', ['confirm', 'approved'])])
            if resignation_request:
                raise ValidationError(
                    _('Existe una solicitud de renuncia en estado confirmado o'
                      ' aprobado para este empleado'))

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Método ejecutado cuando cambia el empleado seleccionado."""
        self.joined_date = self.employee_id.joining_date
        if self.employee_id:
            resignation_request = self.env['hr.resignation'].search(
                [('employee_id', '=', self.employee_id.id),
                 ('state', 'in', ['confirm', 'approved'])])
            if resignation_request:
                raise ValidationError(
                    _('Existe una solicitud de renuncia en estado confirmado o'
                      ' aprobado para este empleado'))
            employee_contract = self.env['hr.contract'].search(
                [('employee_id', '=', self.employee_id.id)])
            for contracts in employee_contract:
                if contracts.state == 'open':
                    self.employee_contract = contracts.name
                    self.notice_period = contracts.notice_days

    @api.model
    def create(self, vals):
        """Crea un nuevo registro asignando una secuencia única."""
        if vals.get('name', _('Nuevo')) == _('Nuevo'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'hr.resignation') or _('Nuevo')
        return super(HrResignation, self).create(vals)

    def action_confirm_resignation(self):
        """Confirma la solicitud de renuncia.
        
        Valida que las fechas sean correctas y cambia el estado a 'confirm'.
        Ejecutado por el botón 'Confirmar'.
        
        Raises:
            ValidationError: Si las fechas son inválidas
        """
        for resignation in self:
            if resignation.joined_date:
                if (resignation.joined_date >=
                        resignation.expected_revealing_date):
                    raise ValidationError(
                        _('La fecha de salida del Empleado debe '
                          'ser posterior a la fecha de ingreso'))
            else:
                raise ValidationError(
                    _('Por favor establezca una Fecha de Ingreso para el empleado'))
            resignation.state = 'confirm'
            resignation.resign_confirm_date = str(fields.Datetime.now())

    def action_cancel_resignation(self):
        """Cancela la solicitud de renuncia.
        
        Ejecutado por el botón 'Cancelar'.
        """
        for resignation in self:
            resignation.state = 'cancel'

    def action_reject_resignation(self):
        """Rechaza la solicitud de renuncia.
        
        Ejecutado por el botón 'Rechazar' (solo para gerentes de RRHH).
        """
        for resignation in self:
            resignation.state = 'cancel'

    def action_reset_to_draft(self):
        """Restablece la renuncia a estado borrador.
        
        Reactiva al empleado y limpia los flags de renuncia/despido.
        Ejecutado por el botón 'Establecer como Borrador'.
        """
        for resignation in self:
            resignation.state = 'draft'
            resignation.employee_id.active = True
            resignation.employee_id.resigned = False
            resignation.employee_id.fired = False

    def action_approve_resignation(self):
        """Aprueba la solicitud de renuncia.
        
        Realiza las siguientes acciones:
        1. Valida que existan contratos para el empleado
        2. Calcula la fecha de salida según el período de preaviso
        3. Cancela los contratos activos
        4. Desactiva al empleado si la fecha de salida es hoy o anterior
        5. Actualiza el motivo de salida (renunciado/despedido)
        6. Cierra contratos en ejecución
        7. Desactiva el usuario vinculado
        
        Ejecutado por el botón 'Aprobar' (solo para gerentes de RRHH).
        
        Raises:
            ValidationError: Si no hay contratos o las fechas son inválidas
        """
        for resignation in self:
            if (resignation.expected_revealing_date and
                    resignation.resign_confirm_date):
                # Busca contratos del empleado
                employee_contract = self.env['hr.contract'].search(
                    [('employee_id', '=', self.employee_id.id)])
                if not employee_contract:
                    raise ValidationError(
                        _("No se encontraron Contratos para este empleado"))
                
                for contract in employee_contract:
                    if contract.state == 'open':
                        resignation.employee_contract = contract.name
                        resignation.state = 'approved'
                        # Calcula fecha de salida sumando días de preaviso
                        resignation.approved_revealing_date = (
                                resignation.resign_confirm_date + timedelta(
                            days=contract.notice_days))
                    else:
                        resignation.approved_revealing_date = (
                            resignation.expected_revealing_date)
                    # Cancela el contrato si está abierto
                    contract.state = 'cancel' if contract.state == "open" else \
                        contract.state
                
                # Cambia el estado del empleado si la fecha de salida es hoy o pasada
                if (resignation.expected_revealing_date <= fields.Date.today()
                        and resignation.employee_id.active):
                    resignation.employee_id.active = False
                    
                    # Actualiza campos en la tabla de empleados relacionados con la renuncia
                    resignation.employee_id.resign_date = (
                        resignation.expected_revealing_date)
                    
                    # Establece el motivo de salida según el tipo de renuncia
                    if resignation.resignation_type == 'resigned':
                        resignation.employee_id.resigned = True
                        departure_reason_id = self.env[
                            'hr.departure.reason'].search(
                            [('name', '=', 'Resigned')])
                    else:
                        resignation.employee_id.fired = True
                        departure_reason_id = self.env[
                            'hr.departure.reason'].search(
                            [('name', '=', 'Fired')])
                    
                    # Cierra los contratos en ejecución
                    running_contract_ids = self.env['hr.contract'].search([
                        ('employee_id', '=', resignation.employee_id.id),
                        ('company_id', '=', resignation.employee_id.company_id.id),
                        ('state', '=', 'open'),
                    ]).filtered(lambda c: c.date_start <= fields.Date.today() and (
                                not c.date_end or c.date_end >= fields.Date.today()))
                    running_contract_ids.state = 'close'
                    resignation.employee_id.departure_reason_id = departure_reason_id
                    resignation.employee_id.departure_date = resignation.approved_revealing_date
                    
                    # Elimina y desactiva el usuario del empleado
                    if resignation.employee_id.user_id:
                        resignation.employee_id.user_id.active = False
                        resignation.employee_id.user_id = None
            else:
                raise ValidationError(_('Por favor ingrese Fechas Válidas.'))
