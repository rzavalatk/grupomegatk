# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)

class ContractType(models.Model):
    _name = 'hr.contract.type'
    _description = 'Contract Type'
    _order = 'sequence, id'

    name = fields.Char(string='Tipo de contrato', required=True, help="Nombre")
    sequence = fields.Integer(help="Indica la secuencia de visualización de una lista de contratos.", default=10)

class ContractInherit(models.Model):
    _inherit = 'hr.contract'

    type_id = fields.Many2one('hr.contract.type', string="Categoria de empleado",
                              required=True, help="Categoria de empleado",
                              default=lambda self: self.env['hr.contract.type'].search([], limit=1))
    #Información bancaria
    bank = fields.Char(string="Banco", help="Banco")
    account_number = fields.Char(string="Cuenta bancaria", help="Cuenta bancaria")
    account_type = fields.Selection([
        ('ahorro', 'Ahorro'),
        ('corriente', 'Corriente')
    ], string='Tipo de cuenta bancaria', help="Tipo de cuenta bancaria")
    #INformación salarial
    salary_type = fields.Selection([
        ('mensual', 'Mensual'),
        ('quincenal', 'Quincenal')
    ], string='Tipo de salario', help="Tipo de salario")
    pay_type = fields.Selection([
        ('efectivo', 'Efectivo'),
        ('cheque', 'Cheque'),
        ('transferencia', 'Transferencia bancaria')
    ], string='Tipo de pago', help="Tipo de pago")
    currency_id = fields.Many2one('res.currency', string='Moneda de pago', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    #beneficios adicionales
    health = fields.Boolean(string="Seguro de salud", help="Seguro de salud")
    pension = fields.Boolean(string="Seguro de pension", help="Seguro de pension")
    vacation = fields.Boolean(string="Vacaciones", help="Vacaciones")
    Bonuses = fields.Boolean(string="Bonificaciones", help="Bonificaciones")
    Commissions = fields.Boolean(string="Comisiones", help="Comisiones")
    viaticos = fields.Boolean(string="Viáticos", help="Viaticos")
    #DEDUCCIONES
    social_security = fields.Boolean('Pago de seguro social')
    social_security_pay = fields.Float('Monto a pagar de seguro social')
    loans = fields.Boolean('Pago de prestamos')
    loans_pay = fields.Float('Monto a pagar de prestamos')
    pensions = fields.Boolean('Pago de pensiones')
    pensions_pay = fields.Float('Monto a pagar de pensiones')
    #PRESTACIONES
    vacation_pay = fields.Boolean('Pago de vacaciones')
    vacation_amount = fields.Float('Monto a pagar de vacaciones')
    aguinaldo = fields.Boolean('Pago de aguinaldo')
    aguinaldo_amount = fields.Float('Total a pagar de aguinaldo')
    catorceavo = fields.Boolean('pago de 14avo')
    catorceavo_amount = fields.Float('Total a pagar de 14avo')
    # Acuerdos Adicionales
    telework_modality = fields.Boolean(string="Modalidad de Teletrabajo")
    telework_days = fields.Many2many(
        'telework.days', 
        string="Jornadas de Teletrabajo", 
        help="Seleccione los días que el empleado teletrabajará.",
    )
    flexible_schedule = fields.Boolean(string="Horario flexible")
    
    @api.constrains('telework_modality', 'telework_days')
    def _check_telework_days(self):
        for record in self:
            if record.telework_modality and not record.telework_days:
                raise ValidationError("Debes seleccionar al menos un día de teletrabajo cuando la Modalidad de Teletrabajo esté habilitada.")

    @api.onchange('health')
    def _onchange_health(self):
        self.social_security = self.health
    
    @api.onchange('pension')
    def _onchange_pension(self):
        self.pensions = self.pension
    
    @api.onchange('vacation')
    def _onchange_vacation(self):
        self.vacation_pay = self.vacation  
    
    def validate_deductions(self):
        deductions = [
            ('social_security', 'El seguro social debe ser mayor a 0', self.social_security_pay),
            ('loans', 'Los prestamos deben ser mayor a 0', self.loans_pay),
            ('pensions', 'Las pensiones deben ser mayor a 0', self.pensions_pay),
            ('vacation_pay', 'El pago de vacaciones debe ser mayor a 0', self.vacation_amount),
            ('aguinaldo', 'El pago de aguinaldo debe ser mayor a 0', self.aguinaldo_amount),
            ('catorceavo', 'El pago de 14avo debe ser mayor a 0', self.catorceavo_amount),
        ]
        for field, message, value in deductions:
            if getattr(self, field) and value <= 0:
                raise UserError(_(message))
            
    @api.model_create_multi               
    def create(self, vals):
        """
        Esta función crea un registro en el modelo hr.contract basado en los valores
        dado en el argumento vals.
        :param vals: un diccionario de valores para crear un registro en el modelo hr.contract
        :return: El registro recién creado
        """
        #VERSION GRATIS DE NOMINA, SOLO PODRA CREAR 10 CONTRATOS
        contratos = self.env['hr.contract'].search([])
        if len(contratos) >= 10:
            raise UserError("NO PUEDE CREAR MAS DE 10 CONTRATOS EN LA VERSION GRATIS, POR FAVOR COMPRUEBE SU PLAN DE NOMINA")
        else:
            return super(ContractInherit, self).create(vals)   

class TeleworkDays(models.Model):
    _name = 'telework.days'
    _description = 'Dias de teletrabajo'

    name = fields.Char(string="Dia", required=True)