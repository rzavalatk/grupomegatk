# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class EmployeeTransfer(models.Model):
    """Modelo para gestionar las Transferencias de Empleados entre sucursales.
    
    Este modelo permite registrar y controlar el proceso de transferencia de
    empleados de una empresa/sucursal a otra, gestionando los estados del
    proceso y creando automáticamente los registros necesarios.
    """
    _name = 'employee.transfer'
    _description = 'Transferencia de Empleados'
    _order = "id desc"

    def _default_responsible_employee_id(self):
        """Obtiene el empleado por defecto para el campo responsible_employee_id.
        
        Busca el empleado asociado al usuario actual que está creando la
        transferencia para asignarlo como responsable por defecto.
        
        Returns:
            hr.employee: Registro del empleado responsable o False si no existe
        """
        emp_ids = self.env['hr.employee'].search([
            ('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    # ===== CAMPOS DEL MODELO =====
    
    name = fields.Char(
        string='Nombre', help='Nombre de la Transferencia',
        copy=False, default=lambda self: _('Nuevo'), readonly=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Empleado', required=True,
        help='Seleccione el empleado que desea transferir')
    old_employee_id = fields.Many2one(
        'hr.employee', string='Empleado Anterior', 
        help='Registro del empleado antes de la transferencia')
    transfer_date = fields.Date(
        string='Fecha', default=fields.Date.today(),
        help="Fecha en que se realizará la transferencia")
    transfer_company_id = fields.Many2one(
        'res.company', string='Transferir A',
        help="Seleccione la empresa/sucursal a la que se transferirá el empleado",
        copy=False, required=True)
    state = fields.Selection(
        [('draft', 'Nuevo'), 
         ('transfer', 'Transferido'), 
         ('cancel', 'Cancelado'),
         ('done', 'Finalizado')],
        string='Estado', readonly=True, copy=False, default='draft',
        help="""Nuevo: La transferencia ha sido creada pero no confirmada.
        Transferido: La transferencia está confirmada. Permanece en este estado
         hasta que la sucursal receptora reciba al empleado.
        Finalizado: El empleado ha sido recibido en la sucursal destino.
        Cancelado: La transferencia ha sido cancelada.""")
    company_id = fields.Many2one(
        'res.company', string='Empresa',
        related='employee_id.company_id',
        help="Empresa actual del empleado")
    note = fields.Text(
        string='Notas Internas',
        help="Especifique notas o comentarios sobre la transferencia")
    transferred = fields.Boolean(
        string='Transferido', copy=False, 
        help="Indica si el empleado ya fue transferido",
        default=False, compute='_compute_transferred')
    responsible_employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Responsable',
        default=_default_responsible_employee_id, readonly=True,
        help="Persona responsable de gestionar esta transferencia.")

    def _compute_transferred(self):
        """Calcula el estado 'transferido' para el registro.
        
        Determina si el usuario actual tiene acceso a la empresa destino
        para poder recibir al empleado transferido.
        """
        for transfer in self:
            # Verifica si la empresa destino está en las empresas del usuario
            transfer.transferred = True if \
                transfer.transfer_company_id in transfer.env.user.company_ids \
                else False

    def action_transfer(self):
        """Acción del botón 'Transferir'.
        
        Valida que se haya seleccionado una empresa destino válida y
        confirma la transferencia cambiando el estado a 'transfer'.
        
        Returns:
            dict: Diccionario con mensaje de advertencia para el usuario
            
        Raises:
            UserError: Si no se selecciona empresa o es la misma empresa actual
        """
        if not self.transfer_company_id:
            raise UserError(_(
                'Debe seleccionar una Empresa destino.'))
        if self.transfer_company_id == self.company_id:
            raise UserError(_(
                'No puede transferir un Empleado a la misma Empresa.'))
        self.state = 'transfer'
        return {
            'warning': {
                'title': _("Advertencia"),
                'message': _(
                    "Este empleado permanecerá en la misma empresa hasta que "
                    "la sucursal destino acepte esta solicitud de transferencia"),
            },
        }

    def action_receive_employee(self):
        """Acción del botón 'Recibir'.
        
        Realiza las siguientes acciones:
        1. Guarda el registro del empleado anterior
        2. Crea un nuevo registro de empleado en la empresa destino
        3. Finaliza los contratos activos en la empresa origen
        4. Desactiva el empleado original
        5. Abre formulario para crear nuevo contrato
        
        Returns:
            dict: Acción de ventana para crear el nuevo contrato del empleado
        """
        # Guarda referencia al empleado original
        self.old_employee_id = self.employee_id
        
        # Lee los datos básicos del empleado actual
        employee = self.employee_id.sudo().read(
            ['name', 'private_email', 'gender',
             'identification_id', 'passport_id'])[0]
        del employee['id']  # Elimina el ID para crear un nuevo registro
        
        # Actualiza la empresa destino
        employee.update({
            'company_id': self.transfer_company_id.id
        })
        
        # Crea el nuevo empleado en la empresa destino
        new_emp = self.env['hr.employee'].sudo().create(employee)
        
        # Finaliza todos los contratos activos del empleado original
        for contract in self.env['hr.contract'].search(
                [('employee_id', '=', self.employee_id.id)]):
            if contract.date_end:
                continue  # Si ya tiene fecha fin, lo omite
            else:
                # Establece la fecha de fin del contrato a hoy
                contract.write({'date_end': fields.date.today().strftime(
                    DEFAULT_SERVER_DATE_FORMAT)})
        
        # Actualiza el registro con el nuevo empleado
        self.employee_id = new_emp
        
        # Desactiva el empleado original
        self.old_employee_id.sudo().write({'active': False})
        
        # Retorna la acción para crear el nuevo contrato
        return {
            'name': _('Contrato'),
            'view_mode': 'form',
            'res_model': 'hr.contract',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_employee_id': self.employee_id.id,
                'default_date_start': self.transfer_date,
                'default_emp_transfer': self.id,
            }, 
        }

    def cancel_transfer(self):
        """Cancela la transferencia.
        
        Cambia el estado de la transferencia a 'cancel', permitiendo
        que el empleado permanezca en su empresa original.
        """
        self.state = 'cancel'

    @api.model
    def create(self, vals):
        """Crea un nuevo registro de transferencia de empleado.
        
        Personaliza el campo 'name' agregando el prefijo "Transferencia: "
        seguido del nombre del empleado que será transferido.
        
        Args:
            vals (dict): Diccionario con los valores del nuevo registro
            
        Returns:
            employee.transfer: Registro creado de la transferencia
        """
        vals['name'] = "Transferencia: " + self.env['hr.employee'].browse(
            vals['employee_id']).name
        return super(EmployeeTransfer, self).create(vals)
