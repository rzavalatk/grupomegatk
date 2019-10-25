# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Sequence(models.Model):
    _inherit = "ir.sequence"

    journal_id = fields.Many2one("account.journal", "Journal")
    move_type = fields.Selection([('debit', 'Débitos'), ('credit', 'Créditos'), ('deposit', 'Depósitos'), ('check', 'Cheques'), 
    	('transference', 'Transferencias'), ('transference_banks', 'Transferencias entre Bancos'),
    	('otro', 'Otro')], string="Tipo de Transacción")