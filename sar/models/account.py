# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    allow_multi_sequence = fields.Boolean('Multisecuencias Fiscales', default=False, help='Create multi sequences for this journal')
    sequence_ids = fields.Many2many('ir.sequence', string='Secuencias')
