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
