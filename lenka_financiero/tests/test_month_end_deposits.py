"""Fictitious accounts only: calendar closing, cashflows and deposit accounting."""
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestLenkaMonthEndDeposits(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({'name': 'FICTITIOUS monthly depositor'})
        cls.bank, cls.liability, cls.expense = cls.env['account.account'].create([
            {'name': 'FICTITIOUS ' + name, 'code': code, 'account_type': kind,
             'company_ids': [(6, 0, cls.company.ids)]}
            for name, code, kind in [('Cash', 'LDEP01', 'asset_cash'),
                                     ('Investor obligation', 'LDEP02', 'liability_current'),
                                     ('Passive interest', 'LDEP03', 'expense')]
        ])
        cls.journal = cls.env['account.journal'].create({
            'name': 'FICTITIOUS deposit bank', 'code': 'LDEP', 'type': 'bank',
            'company_id': cls.company.id, 'default_account_id': cls.bank.id,
        })
        cls.company.write({'lenka_investor_liability_account_id': cls.liability.id,
                           'lenka_passive_interest_expense_account_id': cls.expense.id,
                           'lenka_investment_journal_id': cls.journal.id})

    def _investment(self, **extra):
        vals = {'partner_id': self.partner.id, 'company_id': self.company.id,
                'principal_amount': 100000, 'passive_rate': 1.5, 'early_withdrawal_rate': 1,
                'rate_period': 'monthly', 'investment_type': 'fixed',
                'start_date': '2025-09-01', 'maturity_date': '2026-09-01',
                'capitalization': 'monthly'}
        vals.update(extra)
        rec = self.env['lenka.investment'].create(vals)
        rec.action_activate()
        return rec

    def _deposit(self, investment, date='2025-09-20', amount=30000, reference='FICTITIOUS-001', confirm=True, **extra):
        vals = {'investment_id': investment.id, 'date': date, 'amount': amount,
                'journal_id': self.journal.id, 'reference': reference}
        vals.update(extra)
        rec = self.env['lenka.investment.deposit'].create(vals)
        if confirm:
            rec.action_post()
        return rec

    def _generate(self, investment, date):
        investment._generate_interest_until(fields.Date.to_date(date), investment.passive_rate)
        return investment.interest_line_ids.sorted('period_date')

    def _statement(self, investment, date_from, date_to):
        rec = self.env['lenka.statement'].create({
            'statement_type': 'investment', 'investment_id': investment.id,
            'partner_id': investment.partner_id.id, 'company_id': investment.company_id.id,
            'currency_id': investment.currency_id.id, 'date_from': date_from, 'date_to': date_to,
        })
        rec.action_generate()
        return rec

    def test_first_partial_month_capitalizes_at_its_own_month_end(self):
        rec = self._investment(start_date='2025-09-20')
        lines = self._generate(rec, '2025-10-31')
        self.assertEqual(rec.interest_schedule, 'month_end')
        self.assertEqual([str(l.period_date) for l in lines], ['2025-09-30', '2025-10-31'])
        self.assertEqual([str(l.period_start_date) for l in lines], ['2025-09-20', '2025-10-01'])
        self.assertEqual(lines.mapped('calculation_days'), [11, 31])
        self.assertEqual(lines.mapped('day_count_basis'), [30, 31])
        self.assertAlmostEqual(lines[0].amount, 550)
        self.assertAlmostEqual(lines[1].base_amount, 100550)
        self.assertAlmostEqual(lines[1].amount, 1508.25)

    def test_full_february_is_one_month_in_leap_and_non_leap_years(self):
        for year, end, days in ((2024, '2024-02-29', 29), (2025, '2025-02-28', 28)):
            rec = self._investment(start_date='%s-02-01' % year, maturity_date='%s-06-01' % year)
            line = self._generate(rec, end)
            self.assertEqual(line.calculation_days, days)
            self.assertEqual(line.day_count_basis, days)
            self.assertAlmostEqual(line.amount, 1500)
            self.assertFalse(line.is_prorated)

    def test_opening_on_last_day_earns_one_day(self):
        rec = self._investment(start_date='2025-09-30')
        line = self._generate(rec, '2025-09-30')
        self.assertEqual(line.calculation_days, 1)
        self.assertAlmostEqual(line.amount, 50)

    def test_regular_generation_waits_for_calendar_close_and_is_idempotent(self):
        rec = self._investment(start_date='2025-09-20')
        self.assertFalse(self._generate(rec, '2025-09-29'))
        lines = self._generate(rec, '2025-10-31')
        before = lines.read(['period_date', 'amount', 'base_amount', 'write_date'])
        self._generate(rec, '2025-11-04')
        self._generate(rec, '2025-10-31')
        self.assertEqual(rec.interest_line_ids, lines)
        self.assertEqual(lines.read(['period_date', 'amount', 'base_amount', 'write_date']), before)

    def test_deposit_earns_only_from_arrival_without_changing_contract(self):
        rec = self._investment()
        maturity, rate, initial = rec.maturity_date, rec.passive_rate, rec.principal_amount
        deposit = self._deposit(rec)
        lines = self._generate(rec, '2025-10-31')
        self.assertEqual((rec.maturity_date, rec.passive_rate, rec.principal_amount), (maturity, rate, initial))
        self.assertAlmostEqual(rec.additional_deposits, 30000)
        self.assertAlmostEqual(rec.outstanding_principal, 130000)
        self.assertAlmostEqual(lines[0].amount, 1665)  # 1500 + 30000 * 1.5% * 11/30
        self.assertAlmostEqual(lines[1].base_amount, 131665)
        self.assertAlmostEqual(lines[1].amount, 1974.98)
        self.assertAlmostEqual(rec.account_balance, 133639.98)
        self.assertEqual(deposit.move_id.state, 'draft')

    def test_two_deposits_in_same_month_use_their_own_dates(self):
        rec = self._investment()
        self._deposit(rec, date='2025-09-10', amount=30000)
        self._deposit(rec, date='2025-09-20', amount=60000, reference='FICTITIOUS-002')
        line = self._generate(rec, '2025-09-30')
        self.assertAlmostEqual(line.amount, 1500 + 315 + 330)

    def test_draft_and_cancelled_deposits_do_not_change_balances(self):
        rec = self._investment()
        draft = self._deposit(rec, confirm=False)
        self.assertAlmostEqual(rec.outstanding_principal, 100000)
        draft.action_cancel()
        self.assertAlmostEqual(self._generate(rec, '2025-09-30').amount, 1500)

    def test_confirming_twice_creates_only_one_draft_receipt(self):
        rec = self._investment()
        deposit = self._deposit(rec)
        move = deposit.move_id
        deposit.action_post()
        self.assertEqual(deposit.move_id, move)
        self.assertEqual(len(move.line_ids), 2)
        self.assertAlmostEqual(sum(move.line_ids.mapped('balance')), 0)
        self.assertAlmostEqual(move.line_ids.filtered(lambda l: l.account_id == self.bank).debit, 30000)
        self.assertAlmostEqual(move.line_ids.filtered(lambda l: l.account_id == self.liability).credit, 30000)
        self.assertAlmostEqual(rec.outstanding_principal, 130000)

    def test_same_reference_cannot_be_confirmed_twice(self):
        rec = self._investment()
        self._deposit(rec)
        duplicate = self._deposit(rec, confirm=False)
        with self.assertRaises(ValidationError):
            duplicate.action_post()
        self.assertEqual(duplicate.state, 'draft')
        self.assertFalse(duplicate.move_id)

    def test_accounting_can_publish_matching_receipt_and_protect_it(self):
        deposit = self._deposit(self._investment())
        move = deposit.move_id
        move.action_post()
        self.assertEqual(move.state, 'posted')
        with self.assertRaises(ValidationError):
            deposit.action_cancel()
        with self.assertRaises(ValidationError):
            move.button_draft()
        with self.assertRaises(ValidationError):
            move.line_ids[0].write({'partner_id': False})

    def test_changed_draft_cannot_publish_different_recipient(self):
        deposit = self._deposit(self._investment())
        deposit.move_id.line_ids.write({'partner_id': False})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            deposit.move_id.action_post()
        self.assertEqual(deposit.move_id.state, 'draft')

    def test_cancel_unaccounted_deposit_cancels_receipt_and_removes_capital(self):
        rec = self._investment()
        deposit = self._deposit(rec)
        deposit.action_cancel()
        deposit.action_cancel()
        self.assertEqual(deposit.move_id.state, 'cancel')
        self.assertAlmostEqual(rec.outstanding_principal, 100000)
        deposit.move_id.button_draft()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            deposit.move_id.action_post()

    def test_cannot_cancel_deposit_already_included_in_interest(self):
        rec = self._investment()
        deposit = self._deposit(rec)
        self._generate(rec, '2025-09-30')
        with self.assertRaises(ValidationError):
            deposit.action_cancel()
        self.assertEqual(deposit.state, 'posted')

    def test_confirmed_deposit_and_contract_cannot_be_rewritten(self):
        rec = self._investment()
        deposit = self._deposit(rec)
        for vals in ({'amount': 10}, {'date': '2025-09-21'}, {'reference': 'changed'}, {'state': 'draft'}, {'move_id': False}):
            with self.assertRaises(ValidationError):
                deposit.write(vals)
        with self.assertRaises(ValidationError):
            deposit.unlink()
        with self.assertRaises(ValidationError):
            rec.principal_amount = 130000
        with self.assertRaises(ValidationError):
            rec.maturity_date = '2026-12-01'

    def test_cannot_inject_state_or_accounting_link(self):
        rec = self._investment()
        for extra in ({'state': 'posted'}, {'move_id': 1}):
            with self.assertRaises(ValidationError):
                self._deposit(rec, confirm=False, **extra)

    def test_retroactive_future_and_out_of_term_deposits_are_blocked(self):
        rec = self._investment()
        self._generate(rec, '2025-09-30')
        for date in ('2025-09-20', '2025-09-30', '2025-08-31', '2026-09-01',
                     fields.Date.to_string(fields.Date.today() + timedelta(days=1))):
            draft = self._deposit(rec, date=date, confirm=False)
            with self.assertRaises(ValidationError):
                draft.action_post()
            self.assertFalse(draft.move_id)

    def test_missing_liability_does_not_partially_confirm(self):
        rec = self._investment()
        self.company.lenka_investor_liability_account_id = False
        deposit = self._deposit(rec, confirm=False)
        with self.assertRaises(ValidationError):
            deposit.action_post()
        self.assertEqual(deposit.state, 'draft')
        self.assertFalse(deposit.move_id)
        self.assertAlmostEqual(rec.outstanding_principal, 100000)

    def test_other_company_bank_is_rejected(self):
        rec = self._investment()
        other = self.env['res.company'].create({'name': 'FICTITIOUS second deposit company'})
        journal = self.env['account.journal'].with_company(other).create({
            'name': 'FICTITIOUS foreign bank', 'code': 'FDEP', 'type': 'bank', 'company_id': other.id,
        })
        with self.assertRaises(UserError), self.cr.savepoint():
            self._deposit(rec, journal_id=journal.id)

    def test_net_interest_is_capitalized_after_withholding(self):
        self.env['ir.config_parameter'].sudo().set_param('lenka_financiero.passive_interest_tax_rate', '10')
        rec = self._investment()
        lines = self._generate(rec, '2025-10-31')
        self.assertAlmostEqual(lines[0].amount, 1500)
        self.assertAlmostEqual(lines[0].net_amount, 1350)
        self.assertAlmostEqual(lines[1].base_amount, 101350)
        self.assertAlmostEqual(lines[1].amount, 1520.25)

    def test_annual_rate_and_non_compounding_contract(self):
        rec = self._investment(passive_rate=18, early_withdrawal_rate=12, rate_period='annual', capitalization='maturity')
        lines = self._generate(rec, '2025-10-31')
        self.assertAlmostEqual(lines[0].amount, 1500)
        self.assertAlmostEqual(lines[1].base_amount, 100000)
        self.assertAlmostEqual(lines[1].amount, 1500)

    def test_existing_anniversary_history_is_preserved_and_gap_closes_once(self):
        rec = self._investment(start_date='2025-08-20')
        old = self.env['lenka.investment.interest'].create({
            'investment_id': rec.id, 'period_start_date': '2025-08-20', 'period_date': '2025-09-20',
            'base_amount': 100000, 'rate': 1.5, 'amount': 1500, 'state': 'accrued', 'calculation_days': 30,
        })
        before = old.read()
        lines = self._generate(rec, '2025-10-31')
        self.assertEqual(old.read(), before)
        self.assertEqual([str(l.period_date) for l in lines], ['2025-09-20', '2025-09-30', '2025-10-31'])
        self.assertEqual(str(lines[1].period_start_date), '2025-09-21')
        self.assertAlmostEqual(lines[1].amount, 507.5)
        self.assertAlmostEqual(lines[2].amount, 1530.11)
        self._generate(rec, '2025-10-31')
        self.assertEqual(rec.interest_line_ids, lines)

    def test_deposits_appear_in_statement_and_next_opening_balance(self):
        rec = self._investment()
        deposit = self._deposit(rec)
        statement = self._statement(rec, '2025-09-01', '2025-09-30')
        self.assertAlmostEqual(statement.closing_balance, 130000)
        self.assertEqual(len(statement.line_ids), 2)
        self.assertTrue(statement.line_ids.filtered(lambda l: l.reference == deposit.reference))
        following = self._statement(rec, '2025-10-01', '2025-10-31')
        self.assertAlmostEqual(following.opening_balance, 130000)
        self.assertFalse(following.line_ids)

    def test_withdrawal_settles_through_previous_day_and_remaining_balance_continues(self):
        rec = self._investment(start_date='2025-09-20')
        self._deposit(rec, date='2025-09-25', amount=30000)
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': rec.id, 'date': '2025-09-28', 'principal_amount': 20000,
        })
        withdrawal.action_post()
        # Early rate 1%: 5 days at 100000, 3 at 130000, divided by 30.
        self.assertAlmostEqual(withdrawal.gross_interest_amount, 296.67)
        paid = rec.interest_line_ids
        self.assertEqual(str(paid.period_date), '2025-09-27')
        self.assertEqual(paid.state, 'paid')
        line = self._generate(rec, '2025-09-30')[-1]
        self.assertAlmostEqual(line.base_amount, 110000)
        self.assertEqual(line.calculation_days, 3)
        self.assertAlmostEqual(line.amount, 110)
        before = paid.read()
        self._generate(rec, '2025-10-31')
        self.assertEqual(paid.read(), before)
        self.assertAlmostEqual(rec.interest_line_ids[-1].base_amount, 110110)

    def test_start_day_withdrawal_does_not_create_interest(self):
        rec = self._investment(start_date='2025-09-20')
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': rec.id, 'date': '2025-09-20', 'principal_amount': 100000,
        })
        withdrawal.action_post()
        self.assertFalse(rec.interest_line_ids)
        self.assertEqual(rec.state, 'closed')

    def test_maturity_closes_last_fraction_without_extending_term(self):
        rec = self._investment(start_date='2025-09-20', maturity_date='2025-10-20')
        lines = self._generate(rec, '2025-10-31')
        self.assertEqual([str(l.period_date) for l in lines], ['2025-09-30', '2025-10-19'])
        self.assertEqual(lines.mapped('calculation_days'), [11, 19])
        self.assertAlmostEqual(lines[1].amount, rec.currency_id.round(100550 * .015 * 19 / 31))

    def test_deposit_copy_is_clean_and_does_not_copy_accounting(self):
        deposit = self._deposit(self._investment())
        duplicate = deposit.copy({'reference': 'FICTITIOUS-COPY'})
        self.assertEqual(duplicate.state, 'draft')
        self.assertFalse(duplicate.move_id)
        self.assertNotEqual(duplicate.name, deposit.name)

    def test_wrong_currency_bank_is_rejected(self):
        rec = self._investment()
        currency = self.env['res.currency'].with_context(active_test=False).search([('id', '!=', rec.currency_id.id)], limit=1)
        currency.active = True
        self.journal.currency_id = currency
        deposit = self._deposit(rec, confirm=False)
        with self.assertRaises(ValidationError):
            deposit.action_post()

    def test_hnl_and_usd_deposits_keep_currency_and_balance(self):
        for code in ('HNL', 'USD'):
            currency = self.env['res.currency'].with_context(active_test=False).search([('name', '=', code)], limit=1)
            self.assertTrue(currency)
            currency.active = True
            rec = self._investment(currency_id=currency.id)
            deposit = self._deposit(rec, reference='FICTITIOUS-' + code)
            self.assertEqual(deposit.move_id.line_ids.currency_id, currency)
            self.assertAlmostEqual(sum(deposit.move_id.line_ids.mapped('amount_currency')), 0)
            self.assertAlmostEqual(sum(deposit.move_id.line_ids.mapped('balance')), 0)
            self.assertAlmostEqual(deposit.move_id.line_ids.filtered(lambda l: l.account_id == self.bank).amount_currency, 30000)

    def test_operator_without_accounting_cannot_confirm_or_gain_permissions(self):
        operator = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'FICTITIOUS deposit operator', 'login': 'lenka_deposit_operator',
            'company_id': self.company.id, 'company_ids': [(6, 0, self.company.ids)],
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('lenka_financiero.group_lenka_user').id])],
        })
        deposit = self._deposit(self._investment(), confirm=False)
        with self.assertRaises(AccessError), self.cr.savepoint():
            deposit.with_user(operator).action_post()
        self.assertEqual(deposit.state, 'draft')
        self.assertFalse(deposit.move_id)
        self.assertFalse(operator.has_group('account.group_account_user'))

    def test_company_rule_hides_other_company_deposits(self):
        deposit = self._deposit(self._investment())
        other = self.env['res.company'].create({'name': 'FICTITIOUS isolated reading company'})
        operator = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'FICTITIOUS other-company operator', 'login': 'lenka_deposit_other_company',
            'company_id': other.id, 'company_ids': [(6, 0, other.ids)],
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('lenka_financiero.group_lenka_user').id])],
        })
        model = self.env['lenka.investment.deposit'].with_user(operator).with_context(allowed_company_ids=other.ids)
        self.assertFalse(model.search([('id', '=', deposit.id)]))
        with self.assertRaises(AccessError):
            model.browse(deposit.id).read(['amount'])

    def test_zero_and_negative_deposits_are_rejected(self):
        for amount in (0, -1):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self._deposit(self._investment(), amount=amount)

    def test_new_views_offer_deposit_and_calendar_information(self):
        from lxml import etree
        form = self.env.ref('lenka_financiero.view_lenka_investment_form')
        arch = etree.fromstring(form.arch_db)
        self.assertTrue(arch.xpath("//button[@name='action_register_deposit']"))
        self.assertTrue(arch.xpath("//field[@name='deposit_ids']"))
        self.assertTrue(arch.xpath("//field[@name='interest_schedule']"))
        self.env.ref('lenka_financiero.view_lenka_investment_deposit_form')._check_xml()
