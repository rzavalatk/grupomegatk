# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo.exceptions import Warning


class PlantillasDocuments(models.Model):
    _name = 'banks.template'


    pagar_a = fields.Char("Pagar a", required=True)
    journal_id = fields.Many2one("account.journal", "Banco", required=True)
    total = fields.Float(string='Total', required=True)
    memo = fields.Text("Descripción")
    currency_id = fields.Many2one('res.currency', string='Moneda')
    name = fields.Char("Nombre de Plantilla", required=True)
    detalle_lines = fields.One2many("banks.template.line", "template_id", "Detalle de Plantilla", required=True)
    currency_rate = fields.Float("Tasa de Cambio", digits=(12, 6))
    doc_type = fields.Selection([('check', 'Cheque'), ('transference', 'Transferencia'), ('debit', 'Débito'), ('credit','Crédito'), ('deposit','Depósito')], 
        string='Tipo de Transacción', required=True)
    company_id = fields.Many2one("res.company", "Empresa", default=lambda self: self.env.user.company_id, required=True)
    es_moneda_base = fields.Boolean("Es moneda base")


class check_line(models.Model):
    _name = 'banks.template.line'

    template_id = fields.Many2one('banks.template', 'Plantilla')
    partner_id = fields.Many2one('res.partner', 'Empresa', domain="[('company_id', '=', parent.company_id)]")
    account_id = fields.Many2one('account.account', 'Cuenta', required=True)
    name = fields.Char('Descripción')
    amount = fields.Float('Monto', required=True)
    currency_id = fields.Many2one('res.currency', string='Moneda')
    analytic_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica", domain="[('company_id', '=', parent.company_id)]")
    move_type = fields.Selection([('debit', 'Débito'), ('credit', 'Crédito')], 'Debit/Credit', default='debit', required=True)
