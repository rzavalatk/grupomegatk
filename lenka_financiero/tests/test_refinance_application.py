from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestRefinanceApplication(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.write({'groups_id': [Command.link(cls.env.ref('lenka_financiero.group_lenka_manager').id)]})
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({'name': 'David nuevo - prueba refinanciamiento'})
        cls.old_partner = cls.env['res.partner'].create({'name': 'Empleado David - prueba'})
        cls.portfolio, cls.clearing, cls.bank = cls.env['account.account'].create([
            {'name': name, 'code': code, 'account_type': account_type,
             'reconcile': True, 'company_ids': [Command.set(cls.company.ids)]}
            for name, code, account_type in [
                ('Cartera prueba refinanciamiento', 'RFIN01', 'asset_receivable'),
                ('Intercambio prueba refinanciamiento', 'RFIN02', 'asset_current'),
                ('Banco prueba refinanciamiento', 'RFIN03', 'asset_cash'),
            ]
        ])
        cls.journal = cls.env['account.journal'].create({
            'name': 'Refinanciamiento prueba', 'code': 'RFIN', 'type': 'general',
            'company_id': cls.company.id, 'default_account_id': cls.bank.id,
        })
        cls.company.write({'lenka_portfolio_account_id': cls.portfolio.id,
                           'lenka_disbursement_journal_id': cls.journal.id})

    def _operation(self):
        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.partner.id, 'company_id': self.company.id,
            'operation_type': 'loan', 'principal_amount': 75000,
            'interest_rate': 4.5, 'term_months': 60, 'calculation_method': 'level',
            'is_quote': False, 'state': 'contracted', 'contract_signed': True,
        })
        self.env['lenka.funding.line'].create({
            'operation_id': operation.id, 'source_type': 'own', 'amount': 75000,
        })
        return operation

    def _entry(self, partner=None, posted=True, credit_account=None):
        move = self.env['account.move'].create({
            'journal_id': self.journal.id, 'date': '2026-10-22',
            'ref': 'Traslado de refinanciamiento - prueba',
            'line_ids': [Command.create({
                'account_id': self.portfolio.id, 'partner_id': (partner or self.partner).id,
                'debit': 19269.20, 'credit': 0, 'date_maturity': '2026-10-22',
            }), Command.create({
                'account_id': (credit_account or self.clearing).id, 'partner_id': self.old_partner.id,
                'debit': 0, 'credit': 19269.20,
            })],
        })
        if posted:
            move.action_post()
        return move.line_ids.filtered(lambda line: line.debit > 0)

    def _application(self, operation, line):
        return self.env['lenka.disbursement'].create({
            'operation_id': operation.id, 'payment_method': 'refinance_entry',
            'refinance_line_id': line.id, 'date': line.move_id.date,
            'destination_partner_id': self.partner.id, 'amount': 19269.20,
            'reference': line.move_id.name,
        })

    def _cash(self, operation, amount=55730.80):
        return self.env['lenka.disbursement'].create({
            'operation_id': operation.id, 'payment_method': 'check', 'amount': amount,
            'destination_partner_id': self.partner.id, 'reference': 'Cheque prueba 668',
        })

    def test_75000_activates_without_new_cxc_or_bank_entry(self):
        operation = self._operation()
        operation.action_generate_schedule()
        line = self._entry()
        cash = self._cash(operation)
        cash.action_post()
        cash.action_create_account_move()
        cash.move_id.action_post()
        with self.assertRaises(ValidationError):
            operation.action_activate()
        before = self.env['account.move'].search_count([])
        application = self._application(operation, line)
        application.action_post()
        application.action_post()  # idempotent
        self.assertFalse(application.move_id)
        self.assertEqual(application.refinance_move_id, line.move_id)
        self.assertEqual(self.env['account.move'].search_count([]), before)
        self.assertAlmostEqual(operation.disbursed_amount, 75000, places=2)
        self.assertAlmostEqual(operation.refinance_applied_amount, 19269.20, places=2)
        self.assertAlmostEqual(operation.cash_disbursed_amount, 55730.80, places=2)
        self.assertAlmostEqual(operation.pending_disbursement, 0, places=2)
        self.assertAlmostEqual(sum((line | cash.move_id.line_ids).filtered(
            lambda l: l.account_id == self.portfolio).mapped('balance')), 75000, places=2)
        with self.assertRaises(ValidationError):
            application.action_create_account_move()
        with self.assertRaises(ValidationError):
            application._prepare_disbursement_move()
        operation.action_activate()
        self.assertEqual(operation.state, 'active')
        with self.assertRaises(ValidationError):
            application.action_cancel()

    def test_other_client_and_old_employee_record_rejected(self):
        for partner in [self.old_partner, self.env['res.partner'].create({'name': 'Otro cliente prueba'})]:
            application = self._application(self._operation(), self._entry(partner=partner))
            with self.assertRaises(ValidationError):
                application.action_post()
            self.assertEqual(application.state, 'draft')

    def test_draft_entry_and_cash_counterpart_rejected(self):
        for line in [self._entry(posted=False), self._entry(credit_account=self.bank)]:
            application = self._application(self._operation(), line)
            with self.assertRaises(ValidationError):
                application.action_post()

    def test_amount_date_currency_and_portfolio_validation(self):
        application = self._application(self._operation(), self._entry())
        for values in [{'amount': 19000}, {'date': '2026-10-23'},
                       {'destination_partner_id': self.old_partner.id}]:
            original = {k: application[k].id if k.endswith('_id') else application[k] for k in values}
            application.write(values)
            with self.assertRaises(ValidationError):
                application.action_post()
            application.write(original)
        self.company.lenka_portfolio_account_id = self.clearing
        with self.assertRaises(ValidationError):
            application.action_post()

    def test_duplicate_line_and_excess_total_rejected(self):
        line = self._entry()
        application = self._application(self._operation(), line)
        application.action_post()
        duplicate = self._application(self._operation(), line)
        with self.assertRaises(ValidationError):
            duplicate.action_post()
        cash = self._cash(application.operation_id, 75000)
        with self.assertRaises(ValidationError):
            cash.action_post()
        self.assertEqual(cash.state, 'draft')

    def test_cancellation_preserves_accounting_and_releases_link(self):
        operation = self._operation()
        line = self._entry()
        application = self._application(operation, line)
        application.action_post()
        application.action_cancel()
        self.assertEqual(line.move_id.state, 'posted')
        self.assertAlmostEqual(line.balance, 19269.20, places=2)
        self.assertAlmostEqual(operation.pending_disbursement, 75000, places=2)
        replacement = self._application(operation, line)
        replacement.action_post()
        self.assertEqual(application.state, 'cancelled')
        self.assertEqual(replacement.state, 'posted')

    def test_protect_linked_accounting_and_applied_details(self):
        line = self._entry()
        application = self._application(self._operation(), line)
        application.action_post()
        with self.assertRaises(ValidationError):
            line.move_id.button_draft()
        with self.assertRaises(ValidationError):
            line.move_id._reverse_moves([{'date': '2026-10-29'}])
        with self.assertRaises(ValidationError):
            line.write({'partner_id': self.old_partner.id})
        with self.assertRaises(ValidationError):
            application.write({'refinance_line_id': False})
        with self.assertRaises(ValidationError):
            application.operation_id.write({'partner_id': self.old_partner.id})
        application.action_cancel()
        line.move_id.button_draft()
        self.assertEqual(line.move_id.state, 'draft')

    def test_lenka_user_cannot_create_or_apply_internal_link(self):
        user = new_test_user(self.env, login='lenka_refinance_user',
                             groups='lenka_financiero.group_lenka_user')
        operation, line = self._operation(), self._entry()
        with self.assertRaises(AccessError):
            self.env['lenka.disbursement'].with_user(user).create({
                'operation_id': operation.id, 'payment_method': 'refinance_entry',
                'refinance_line_id': line.id, 'date': line.move_id.date,
                'destination_partner_id': self.partner.id, 'amount': 19269.20,
            })
        application = self._application(operation, line)
        with self.assertRaises(AccessError):
            application.with_user(user).action_post()

    def test_reference_is_preserved_for_checks_and_transfers(self):
        operation = self._operation()
        for method, reference in [('check', 'Cheque 668'), ('transfer', 'Transaccion BP-12345')]:
            cash = self._cash(operation, 100)
            cash.write({'payment_method': method, 'reference': reference})
            cash.action_post()
            self.assertEqual(cash.reference, reference)

    def test_wrong_company_and_currency_are_rejected(self):
        operation = self._operation()
        line = self._entry()
        application = self._application(operation, line)
        other_company = self.env['res.company'].create({'name': 'Otra empresa prueba refinanciamiento'})
        operation.company_id = other_company
        with self.assertRaises(ValidationError):
            application.action_post()
        operation.company_id = self.company
        other_currency = self.env['res.currency'].with_context(active_test=False).search([('id', '!=', operation.currency_id.id)], limit=1)
        other_currency.active = True
        operation.currency_id = other_currency
        with self.assertRaises(ValidationError):
            application.action_post()

    def test_link_on_cash_and_internal_funding_source_are_rejected(self):
        operation = self._operation()
        line = self._entry()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['lenka.disbursement'].create({
                'operation_id': operation.id, 'amount': 19269.20,
                'payment_method': 'transfer', 'refinance_line_id': line.id,
            })
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['lenka.disbursement'].create({
                'operation_id': operation.id, 'amount': 19269.20,
                'payment_method': 'refinance_entry', 'refinance_line_id': line.id,
                'funding_line_id': operation.funding_line_ids.id,
            })

    def test_reversed_entry_is_rejected(self):
        line = self._entry()
        line.move_id._reverse_moves([{'date': '2026-10-29'}], cancel=True)
        application = self._application(self._operation(), line)
        with self.assertRaises(ValidationError):
            application.action_post()
