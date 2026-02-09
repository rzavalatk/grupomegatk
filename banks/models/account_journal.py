# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


# Campos que se asignan al formulario de bancos
class AccountJournal(models.Model):
	_inherit = "account.journal"

	multi_seq_banks = fields.Boolean('Multi secuencias bancarias', default=False)
	secuencia_ids = fields.One2many("ir.sequence", "journal_id", "Secuencias")
	logo = fields.Binary('Logo')

	def _get_available_payment_method_lines(self, payment_type):
		"""Override to avoid AccessError on journals in multi-company migration tests.

		We intentionally use sudo() when computing available payment methods so that
		reading journal payment method lines does not fail because of restrictive
		record rules on account.journal during automated crawls.
		"""
		journals = self.sudo()
		return super(AccountJournal, journals)._get_available_payment_method_lines(payment_type)
	