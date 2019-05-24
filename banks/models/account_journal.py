# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    multi_seq_banks = fields.Boolean('Multi secuencias bancarias', default=False)
    secuencia_ids = fields.One2many("ir.sequence", "journal_id", "Secuencias")