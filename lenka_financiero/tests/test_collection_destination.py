"""Fictitious payments only; no production records or bank transactions."""
from lxml import etree
from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCollectionDestination(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({'name': 'FICTITIOUS collection client'})
        accounts = cls.env['account.account'].create([
            {'name': 'FICTITIOUS ' + name, 'code': 'LCD%02d' % index,
             'account_type': kind, 'company_ids': [(6, 0, cls.company.ids)]}
            for index, (name, kind) in enumerate([
                ('bank A', 'asset_cash'), ('bank B', 'asset_cash'), ('cash', 'asset_cash'),
                ('clearing', 'asset_current'), ('portfolio', 'asset_current'),
                ('interest', 'income'), ('late fees', 'income'), ('advances', 'liability_current'),
                ('card fees', 'expense')], 1)
        ])
        cls.bank_a, cls.bank_b, cls.cash, cls.clearing, cls.portfolio, cls.interest, cls.late, cls.advances, cls.fees = accounts
        cls.journals = cls.env['account.journal'].create([
            {'name': 'FICTITIOUS ' + name, 'code': code, 'type': kind,
             'company_id': cls.company.id, 'default_account_id': account.id}
            for name, code, kind, account in [
                ('bank A', 'LCDA', 'bank', cls.bank_a), ('bank B', 'LCDB', 'bank', cls.bank_b),
                ('cash', 'LCDC', 'cash', cls.cash), ('clearing', 'LCDI', 'general', cls.clearing)]
        ])
        cls.company.write({
            'lenka_collection_journal_id': cls.journals[0].id,
            'lenka_portfolio_account_id': cls.portfolio.id,
            'lenka_interest_income_account_id': cls.interest.id,
            'lenka_late_fee_income_account_id': cls.late.id,
            'lenka_unapplied_account_id': cls.advances.id,
            'lenka_card_fee_expense_account_id': cls.fees.id,
        })

    def _operation(self):
        rec = self.env['lenka.financial.operation'].create({
            'partner_id': self.partner.id, 'company_id': self.company.id,
            'operation_type': 'loan', 'principal_amount': 300000,
            'interest_rate': 3.5, 'rate_period': 'monthly', 'term_months': 18,
            'calculation_method': 'interest_then_level', 'interest_only_months': 6,
            'first_payment_date': '2025-01-14', 'is_quote': False,
            'late_fee_method': 'legacy',
        })
        rec.action_generate_schedule()
        rec.state = 'active'
        return rec

    def _payment(self, **extra):
        vals = {'operation_id': self._operation().id, 'amount': 10500,
                'payment_date': '2025-01-14', 'payment_method': 'transfer',
                'collection_destination': 'bank', 'collection_journal_id': self.journals[0].id}
        vals.update(extra)
        return self.env['lenka.payment'].create(vals)

    def test_interest_only_bank_collection_creates_one_draft_and_no_capital_credit(self):
        rec = self._payment()
        rec.action_apply_and_prepare_collection()
        move = rec.move_id
        self.assertEqual(rec.state, 'posted')
        self.assertEqual(move.state, 'draft')
        self.assertEqual(move.journal_id, self.journals[0])
        self.assertEqual(move.line_ids.filtered(lambda l: l.debit).account_id, self.bank_a)
        self.assertEqual(move.line_ids.filtered(lambda l: l.credit).account_id, self.interest)
        self.assertEqual(rec.interest_amount, 10500)
        self.assertEqual(rec.capital_amount, 0)
        self.assertEqual(rec.operation_id.outstanding_capital, 300000)
        self.assertTrue(move.name.startswith('LENKA-COB-'))
        allocation_ids = rec.allocation_line_ids.ids
        counter = self.env.ref('lenka_financiero.seq_lenka_collection_move').number_next_actual
        rec.action_apply_and_prepare_collection()
        self.assertEqual(rec.move_id, move)
        self.assertEqual(rec.allocation_line_ids.ids, allocation_ids)
        self.assertEqual(self.env.ref('lenka_financiero.seq_lenka_collection_move').number_next_actual, counter)
        name = move.name
        move.action_post()
        self.assertEqual(move.name, name)
        self.assertEqual(rec.collection_accounting_state, 'posted')

    def test_selected_bank_overrides_company_default_for_this_payment_only(self):
        rec = self._payment(collection_journal_id=self.journals[1].id)
        rec.action_apply_and_prepare_collection()
        self.assertEqual(rec.move_id.journal_id, self.journals[1])
        self.assertEqual(rec.move_id.line_ids.filtered(lambda l: l.debit).account_id, self.bank_b)
        self.assertEqual(self.company.lenka_collection_journal_id, self.journals[0])

    def test_clearing_collection_does_not_post_bank_cashflow(self):
        rec = self._payment(collection_destination='clearing', collection_journal_id=self.journals[3].id)
        rec.action_apply_and_prepare_collection()
        self.assertEqual(rec.move_id.line_ids.filtered(lambda l: l.debit).account_id, self.clearing)
        self.assertFalse(rec.move_id.line_ids.filtered(lambda l: l.account_id in (self.bank_a | self.bank_b | self.cash)))
        rec.move_id.action_post()

    def test_cash_collection_uses_selected_cash_journal(self):
        rec = self._payment(payment_method='cash', collection_destination='cash', collection_journal_id=self.journals[2].id)
        rec.action_apply_and_prepare_collection()
        self.assertEqual(rec.move_id.line_ids.filtered(lambda l: l.debit).account_id, self.cash)

    def test_designated_historical_internal_bridge_keeps_its_classification(self):
        self.company.lenka_refinance_clearing_journal_id = self.journals[1]
        rec = self._payment(collection_destination='clearing', collection_journal_id=self.journals[1].id)
        rec.action_apply_and_prepare_collection()
        self.assertEqual(self.journals[1].type, 'bank')
        self.assertEqual(self.bank_b.account_type, 'asset_cash')
        self.assertEqual(rec.move_id.line_ids.filtered(lambda l: l.debit).account_id, self.bank_b)

    def test_missing_destination_rolls_back_without_applying_interest(self):
        rec = self._payment(collection_journal_id=False)
        with self.assertRaises(ValidationError):
            rec.action_apply_and_prepare_collection()
        self.assertEqual(rec.state, 'draft')
        self.assertFalse(rec.move_id)
        self.assertEqual(rec.operation_id.paid_interest, 0)

    def test_accounting_failure_rolls_back_the_allocation_too(self):
        rec = self._payment()
        self.company.lenka_interest_income_account_id = False
        with self.assertRaises(ValidationError):
            rec.action_apply_and_prepare_collection()
        self.assertEqual(rec.state, 'draft')
        self.assertFalse(rec.allocation_line_ids)
        self.assertFalse(rec.move_id)
        self.assertEqual(rec.operation_id.paid_interest, 0)

    def test_bank_cannot_be_used_as_undesigned_clearing(self):
        rec = self._payment(collection_destination='clearing')
        with self.assertRaises(ValidationError):
            rec.action_apply_and_prepare_collection()
        self.assertEqual(rec.state, 'draft')

    def test_destination_type_and_deprecated_account_are_validated(self):
        rec = self._payment(collection_destination='cash')
        with self.assertRaises(ValidationError):
            rec.action_apply_and_prepare_collection()
        rec.collection_destination = 'bank'
        self.bank_a.deprecated = True
        with self.assertRaises(ValidationError):
            rec.action_apply_and_prepare_collection()

    def test_already_applied_payment_can_prepare_without_reapplying(self):
        rec = self._payment(collection_destination=False, collection_journal_id=False)
        rec.action_post()  # Original workflow retained for pre-upgrade payments.
        allocations = rec.allocation_line_ids.ids
        interest_paid = rec.operation_id.paid_interest
        rec.write({'collection_destination': 'bank', 'collection_journal_id': self.journals[1].id})
        rec.action_create_account_move()
        rec.action_create_account_move()
        self.assertEqual(rec.allocation_line_ids.ids, allocations)
        self.assertEqual(rec.operation_id.paid_interest, interest_paid)
        self.assertEqual(rec.move_id.journal_id, self.journals[1])

    def test_changing_destination_after_draft_creation_is_rejected(self):
        rec = self._payment()
        rec.action_apply_and_prepare_collection()
        for vals in ({'collection_journal_id': self.journals[1].id}, {'collection_destination': 'clearing'}):
            with self.assertRaises(ValidationError):
                rec.write(vals)

    def test_edited_bank_draft_cannot_be_posted(self):
        rec = self._payment()
        rec.action_apply_and_prepare_collection()
        rec.move_id.line_ids.filtered(lambda l: l.debit).account_id = self.bank_b
        with self.assertRaises(ValidationError), self.cr.savepoint():
            rec.move_id.action_post()
        self.assertEqual(rec.move_id.state, 'draft')

    def test_published_collection_and_lines_require_regularization(self):
        rec = self._payment()
        rec.action_apply_and_prepare_collection()
        rec.move_id.action_post()
        for operation in (lambda: rec.move_id.button_draft(),
                          lambda: rec.move_id.line_ids.write({'partner_id': False}),
                          lambda: rec.move_id._reverse_moves(),
                          lambda: rec.action_cancel()):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                operation()
        self.assertEqual(rec.move_id.state, 'posted')

    def test_cancellation_cancels_draft_and_unapplies_only_once(self):
        rec = self._payment()
        rec.action_apply_and_prepare_collection()
        rec.action_cancel()
        rec.action_cancel()
        self.assertEqual(rec.move_id.state, 'cancel')
        self.assertEqual(rec.operation_id.paid_interest, 0)
        rec.move_id.button_draft()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            rec.move_id.action_post()

    def test_other_company_destination_is_rejected_before_allocation(self):
        company = self.env['res.company'].create({'name': 'FICTITIOUS OTHER collection company'})
        journal = self.env['account.journal'].create({'name': 'FICTITIOUS OTHER bank', 'code': 'LCDO', 'type': 'bank', 'company_id': company.id})
        rec = self._payment(collection_journal_id=journal.id)
        with self.assertRaises(ValidationError):
            rec.action_apply_and_prepare_collection()
        self.assertEqual(rec.operation_id.paid_interest, 0)

    def test_no_accounting_permissions_are_elevated(self):
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'FICTITIOUS Lenka operator', 'login': 'fictitious_collection_operator',
            'company_id': self.company.id, 'company_ids': [(6, 0, self.company.ids)],
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('lenka_financiero.group_lenka_user').id])],
        })
        rec = self._payment()
        with self.assertRaises(AccessError):
            rec.with_user(user).action_apply_and_prepare_collection()
        self.assertEqual(rec.state, 'draft')
        self.assertEqual(rec.operation_id.paid_interest, 0)

    def test_currency_mismatch_rejected(self):
        other = self.env['res.currency'].search([('id', '!=', self.company.currency_id.id)], limit=1)
        other.active = True
        self.journals[0].currency_id = other
        rec = self._payment()
        with self.assertRaises(ValidationError):
            rec.action_apply_and_prepare_collection()

    def test_view_offers_combined_action_and_explicit_accounting_status(self):
        result = self.env['lenka.payment'].get_view(self.env.ref('lenka_financiero.view_lenka_payment_form').id, 'form')
        arch = etree.fromstring(result['arch'])
        self.assertTrue(arch.xpath("//button[@name='action_apply_and_prepare_collection']"))
        self.assertFalse(arch.xpath("//button[@name='action_post']"))
        for field in ('collection_destination', 'collection_journal_id', 'collection_account_id', 'collection_accounting_state'):
            self.assertTrue(arch.xpath("//field[@name='%s']" % field))
