# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


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
        ('nomina', 'Nomina'),
        ('quincenal', 'Quincenal')
    ], string='Tipo de salario', help="Tipo de salario")
    pay_type = fields.Selection([
        ('efectivo', 'Efectivo'),
        ('cheque', 'Cheque'),
        ('transferencia', 'Transferencia bancaria')
    ], string='Tipo de pago', help="Tipo de pago")
    
    #beneficios adicionales
    health = fields.Boolean(string="Seguro de salud", help="Seguro de salud")
    pension = fields.Boolean(string="Seguro de pension", help="Seguro de pension")
    vacation = fields.Boolean(string="Vacaciones", help="Vacaciones")
    Bonuses = fields.Boolean(string="Bonificaciones", help="Bonificaciones")
    Commissions = fields.Boolean(string="Comisiones", help="Comisiones")
    viaticos = fields.Boolean(string="Viáticos", help="Viaticos")
    
    
    #DEDUCCIONES
    
    
    
    
    
    