# -*- coding: utf-8 -*-
from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['pixel'] = {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
        return res

    @api.model_create_multi
    def create(self, vals_list):
        payment_methods = super().create(vals_list)
        methods_info = self._get_payment_method_information()
        for method in payment_methods:
            information = methods_info.get(method.code)

            if method.code == 'pixel':
                method_domain = method._get_payment_method_domain()

                journals = self.env['account.journal'].search(method_domain)

                self.env['account.payment.method.line'].create([{
                    'name': method.name,
                    'payment_method_id': method.id,
                    'journal_id': journal.id
                } for journal in journals])
        return payment_methods