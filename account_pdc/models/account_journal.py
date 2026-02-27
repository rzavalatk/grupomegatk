# -*- coding: utf-8 -*-
from odoo import models, api, _

class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.depends('outbound_payment_method_ids')
    def _compute_check_printing_payment_method_selected(self):
        self.check_printing_payment_method_selected = any(
            pm.code in ['check_printing', 'pdc'] for pm in self.outbound_payment_method_ids)

    def _enable_pdc_on_bank_journals(self):
        """ Enables check printing payment method and add a check sequence on bank journals.
            Called upon module installation via data file.
        """
        pdcin = self.env.ref('account_pdc.account_payment_method_pdc_in')
        pdcout = self.env.ref('account_pdc.account_payment_method_pdc_out')
        bank_journals = self.search([('type', '=', 'bank')])
        for bank_journal in bank_journals:
            # bank_journal._create_check_sequence()
            bank_journal.write({
                'inbound_payment_method_ids': [(4, pdcin.id, None)],
                'outbound_payment_method_ids': [(4, pdcout.id, None)],
            })
