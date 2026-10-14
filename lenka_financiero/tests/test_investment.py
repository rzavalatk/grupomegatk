from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestLenkaInvestment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Inversionista Prueba Lenka'})

    def _investment(self, **extra):
        vals = {
            'partner_id': self.partner.id,
            'investment_type': 'fixed',
            'principal_amount': 100000.0,
            'passive_rate': 12.0,
            'early_withdrawal_rate': 6.0,
            'rate_period': 'annual',
            'start_date': fields.Date.add(fields.Date.context_today(self.env.user), months=-3),
            'term_months': 12,
            'capitalization': 'monthly',
        }
        vals.update(extra)
        investment = self.env['lenka.investment'].create(vals)
        investment.action_activate()
        return investment

    def test_monthly_interest_12_percent_annual(self):
        investment = self._investment()
        investment.action_generate_monthly_interest()
        self.assertTrue(investment.interest_line_ids)
        first = investment.interest_line_ids.sorted('period_date')[0]
        self.assertAlmostEqual(first.amount, 1000.0, places=2)

    def test_monthly_capitalization_increases_interest_base(self):
        investment = self._investment()
        investment.action_generate_monthly_interest()
        lines = investment.interest_line_ids.sorted('period_date')
        if len(lines) >= 2:
            self.assertGreater(lines[1].base_amount, lines[0].base_amount)
            self.assertGreater(lines[1].amount, lines[0].amount)

    def test_withdrawal_cannot_exceed_outstanding_principal(self):
        investment = self._investment()
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id,
            'principal_amount': 120000.0,
            'date': fields.Date.context_today(self.env.user),
        })
        with self.assertRaises(ValidationError):
            withdrawal.action_post()

    def test_early_withdrawal_recalculates_all_interest_at_contractual_early_rate(self):
        investment = self._investment(
            passive_rate=1.5,
            early_withdrawal_rate=1.0,
            rate_period='monthly',
        )
        investment.action_generate_monthly_interest()
        preferential_interest = sum(investment.interest_line_ids.mapped('amount'))

        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id,
            'principal_amount': 20000.0,
            'date': fields.Date.context_today(self.env.user),
        })
        self.assertTrue(withdrawal.early_withdrawal)
        withdrawal.action_post()

        recalculated_interest = withdrawal.accrued_interest_amount
        self.assertAlmostEqual(withdrawal.effective_rate, 1.0, places=4)
        self.assertLess(recalculated_interest, preferential_interest)
        self.assertAlmostEqual(
            withdrawal.total_amount,
            withdrawal.principal_amount + recalculated_interest,
            places=2,
        )

    def test_early_withdrawal_compounds_monthly_at_reduced_rate(self):
        investment = self._investment(
            passive_rate=1.5,
            early_withdrawal_rate=1.0,
            rate_period='monthly',
        )
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id,
            'principal_amount': 20000.0,
            'date': fields.Date.context_today(self.env.user),
        })
        withdrawal.action_post()
        lines = investment.interest_line_ids.sorted('period_date')
        self.assertGreaterEqual(len(lines), 3)
        self.assertAlmostEqual(lines[0].amount, 1000.0, places=2)
        self.assertAlmostEqual(lines[1].base_amount, 101000.0, places=2)
        self.assertAlmostEqual(lines[1].amount, 1010.0, places=2)


    def test_early_rate_cannot_exceed_preferential_rate(self):
        investment = self.env['lenka.investment'].create({
            'partner_id': self.partner.id,
            'investment_type': 'fixed',
            'principal_amount': 100000.0,
            'passive_rate': 1.0,
            'early_withdrawal_rate': 1.5,
            'rate_period': 'monthly',
            'start_date': fields.Date.context_today(self.env.user),
            'term_months': 12,
            'capitalization': 'monthly',
        })
        with self.assertRaises(ValidationError):
            investment.action_activate()

    def test_withdrawal_before_investment_start_is_rejected(self):
        investment = self._investment(
            passive_rate=1.5,
            early_withdrawal_rate=1.0,
            rate_period='monthly',
        )
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id,
            'principal_amount': 10000.0,
            'date': fields.Date.add(investment.start_date, days=-1),
        })
        with self.assertRaises(ValidationError):
            withdrawal.action_post()


    def test_fixed_investment_requires_early_withdrawal_rate(self):
        investment = self.env['lenka.investment'].create({
            'partner_id': self.partner.id,
            'investment_type': 'fixed',
            'principal_amount': 100000.0,
            'passive_rate': 1.5,
            'early_withdrawal_rate': 0.0,
            'rate_period': 'monthly',
            'start_date': fields.Date.context_today(self.env.user),
            'term_months': 12,
            'capitalization': 'monthly',
        })
        with self.assertRaises(ValidationError):
            investment.action_activate()


    def test_interest_tax_is_split_into_gross_tax_and_net(self):
        investment = self._investment()
        interest = self.env['lenka.investment.interest'].create({
            'investment_id': investment.id,
            'period_date': fields.Date.context_today(self.env.user),
            'base_amount': 100000.0,
            'rate': 1.0,
            'amount': 1000.0,
            'tax_rate': 10.0,
            'state': 'accrued',
        })
        self.assertAlmostEqual(interest.tax_amount, 100.0, places=2)
        self.assertAlmostEqual(interest.net_amount, 900.0, places=2)

    def test_interest_tax_rate_must_be_valid_percentage(self):
        investment = self._investment()
        with self.assertRaises(ValidationError):
            self.env['lenka.investment.interest'].create({
                'investment_id': investment.id,
                'period_date': fields.Date.context_today(self.env.user),
                'base_amount': 100000.0,
                'rate': 1.0,
                'amount': 1000.0,
                'tax_rate': 101.0,
                'state': 'accrued',
            })


    def test_maturity_withdrawal_uses_only_unpaid_net_interest(self):
        today = fields.Date.context_today(self.env.user)
        investment = self._investment(
            passive_rate=1.5,
            early_withdrawal_rate=1.0,
            rate_period='monthly',
            start_date=fields.Date.add(today, months=-3),
            maturity_date=today,
            term_months=3,
        )
        self.env['lenka.investment.interest'].create({
            'investment_id': investment.id,
            'period_date': fields.Date.add(today, months=-2),
            'base_amount': 100000.0,
            'rate': 1.5,
            'amount': 1500.0,
            'tax_rate': 10.0,
            'state': 'paid',
        })
        pending = self.env['lenka.investment.interest'].create({
            'investment_id': investment.id,
            'period_date': fields.Date.add(today, months=-1),
            'base_amount': 101500.0,
            'rate': 1.5,
            'amount': 1522.50,
            'tax_rate': 10.0,
            'state': 'accrued',
        })
        investment.action_generate_monthly_interest()
        expected_pending_net = sum(investment.interest_line_ids.filtered(lambda l: l.state == 'accrued').mapped('net_amount'))
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id,
            'principal_amount': 100000.0,
            'date': today,
        })
        withdrawal.action_post()
        self.assertFalse(withdrawal.early_withdrawal)
        self.assertGreaterEqual(expected_pending_net, pending.net_amount)
        self.assertAlmostEqual(withdrawal.accrued_interest_amount, expected_pending_net, places=2)
        self.assertEqual(investment.state, 'closed')

    def test_partial_maturity_withdrawal_keeps_investment_open(self):
        today = fields.Date.context_today(self.env.user)
        investment = self._investment(
            start_date=fields.Date.add(today, months=-12),
            maturity_date=today,
            term_months=12,
        )
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id,
            'principal_amount': 25000.0,
            'date': today,
        })
        withdrawal.action_post()
        self.assertAlmostEqual(investment.outstanding_principal, 75000.0, places=2)
        self.assertNotEqual(investment.state, 'closed')


    def test_mark_matured_moves_active_investment_to_matured(self):
        today = fields.Date.context_today(self.env.user)
        investment = self._investment(
            start_date=fields.Date.add(today, months=-12),
            maturity_date=today,
            term_months=12,
        )
        self.assertEqual(investment.state, 'active')
        investment.action_mark_matured()
        self.assertEqual(investment.state, 'matured')
        self.assertTrue(investment.interest_line_ids)

    def test_not_yet_mature_investment_stays_active(self):
        today = fields.Date.context_today(self.env.user)
        investment = self._investment(
            start_date=today,
            maturity_date=fields.Date.add(today, months=12),
            term_months=12,
        )
        investment.action_mark_matured()
        self.assertEqual(investment.state, 'active')


    def test_full_maturity_withdrawal_marks_pending_interest_paid(self):
        today = fields.Date.context_today(self.env.user)
        investment = self._investment(
            start_date=fields.Date.add(today, months=-2),
            maturity_date=today,
            term_months=2,
        )
        investment.action_generate_monthly_interest()
        self.assertTrue(investment.interest_line_ids.filtered(lambda l: l.state == 'accrued'))
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id,
            'principal_amount': investment.outstanding_principal,
            'date': today,
        })
        withdrawal.action_post()
        self.assertEqual(investment.state, 'closed')
        self.assertFalse(investment.interest_line_ids.filtered(lambda l: l.state == 'accrued'))
        self.assertTrue(investment.interest_line_ids.filtered(lambda l: l.state == 'paid'))


    def test_full_withdrawal_marks_pending_interest_paid(self):
        today = fields.Date.context_today(self.env.user)
        investment = self._investment(
            start_date=fields.Date.add(today, months=-3),
            maturity_date=today,
            term_months=3,
        )
        investment.action_generate_monthly_interest()
        self.assertTrue(investment.interest_line_ids.filtered(lambda l: l.state == 'accrued'))
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id,
            'principal_amount': investment.outstanding_principal,
            'date': today,
        })
        withdrawal.action_post()
        self.assertEqual(investment.state, 'closed')
        self.assertFalse(investment.interest_line_ids.filtered(lambda l: l.state == 'accrued'))
        self.assertTrue(investment.interest_line_ids.filtered(lambda l: l.state == 'paid'))
        self.assertAlmostEqual(investment.outstanding_principal, 0.0, places=2)


    def test_partial_maturity_withdrawal_marks_included_interest_paid(self):
        today = fields.Date.context_today(self.env.user)
        investment = self._investment(
            start_date=fields.Date.add(today, months=-3),
            maturity_date=today,
            term_months=3,
        )
        investment.action_generate_monthly_interest()
        pending_before = investment.interest_line_ids.filtered(lambda l: l.state == 'accrued')
        expected_net = sum(pending_before.mapped('net_amount'))
        self.assertGreater(expected_net, 0.0)
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id,
            'principal_amount': 25000.0,
            'date': today,
        })
        withdrawal.action_post()
        self.assertAlmostEqual(withdrawal.accrued_interest_amount, expected_net, places=2)
        self.assertFalse(investment.interest_line_ids.filtered(lambda l: l.state == 'accrued'))
        self.assertAlmostEqual(investment.outstanding_principal, 75000.0, places=2)
        self.assertNotEqual(investment.state, 'closed')


    def test_withdrawal_tracks_gross_tax_and_net_interest(self):
        today = fields.Date.context_today(self.env.user)
        investment = self._investment(
            start_date=fields.Date.add(today, months=-1),
            maturity_date=today,
            term_months=1,
        )
        interest = self.env['lenka.investment.interest'].create({
            'investment_id': investment.id,
            'period_date': today,
            'base_amount': 100000.0,
            'rate': 1.0,
            'amount': 1000.0,
            'tax_rate': 10.0,
            'state': 'accrued',
        })
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id,
            'principal_amount': 25000.0,
            'date': today,
        })
        withdrawal.action_post()
        self.assertGreaterEqual(withdrawal.gross_interest_amount, interest.amount)
        self.assertGreaterEqual(withdrawal.interest_tax_amount, interest.tax_amount)
        self.assertAlmostEqual(
            withdrawal.accrued_interest_amount,
            withdrawal.gross_interest_amount - withdrawal.interest_tax_amount,
            places=2,
        )
        self.assertAlmostEqual(
            withdrawal.total_amount,
            withdrawal.principal_amount + withdrawal.accrued_interest_amount,
            places=2,
        )

    def test_half_and_majority_withdrawals_keep_remaining_capital_open(self):
        today = fields.Date.context_today(self.env.user)
        for amount in (50000.0, 75000.0):
            investment = self._investment(maturity_date=today)
            withdrawal = self.env['lenka.investment.withdrawal'].create({
                'investment_id': investment.id, 'principal_amount': amount, 'date': today,
            })
            withdrawal.action_post()
            self.assertAlmostEqual(investment.outstanding_principal, 100000.0 - amount)
            self.assertNotEqual(investment.state, 'closed')
            remaining = self.env['lenka.investment.withdrawal'].create({
                'investment_id': investment.id, 'principal_amount': 100000.0 - amount,
                'date': today,
            })
            remaining.action_post()
            self.assertEqual(investment.state, 'closed')
            self.assertAlmostEqual(remaining.accrued_interest_amount, 0.0)

    def test_early_withdrawal_marks_recognized_interest_paid(self):
        investment = self._investment()
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id, 'principal_amount': 100000.0,
        })
        withdrawal.action_post()
        self.assertGreater(withdrawal.accrued_interest_amount, 0.0)
        self.assertFalse(investment.interest_line_ids.filtered(lambda line: line.state == 'accrued'))
        self.assertAlmostEqual(investment.paid_interest, withdrawal.accrued_interest_amount)
        self.assertEqual(investment.state, 'closed')

    def test_interest_calendar_keeps_original_month_end(self):
        investment = self._investment(start_date='2025-01-31', maturity_date='2025-05-31')
        investment._generate_interest_until(fields.Date.to_date('2025-04-30'), 12.0)
        expected = ['2025-02-28', '2025-03-31', '2025-04-30']
        self.assertEqual([str(line.period_date) for line in investment.interest_line_ids], expected)
        original = investment.interest_line_ids
        investment._generate_interest_until(fields.Date.to_date('2025-04-30'), 12.0)
        self.assertEqual(investment.interest_line_ids, original)

    def test_backdated_withdrawal_does_not_pay_later_interest(self):
        investment = self._investment(investment_type='current', term_months=0, maturity_date=False,
                                      start_date='2025-01-15')
        investment._generate_interest_until(fields.Date.to_date('2025-04-15'), 12.0)
        later = investment.interest_line_ids.filtered(lambda line: line.period_date > fields.Date.to_date('2025-02-15'))
        first = investment.interest_line_ids.filtered(lambda line: line.period_date == fields.Date.to_date('2025-02-15'))
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id, 'principal_amount': 1000.0, 'date': '2025-02-15',
        })
        withdrawal.action_post()
        self.assertAlmostEqual(withdrawal.accrued_interest_amount, first.net_amount)
        self.assertEqual(first.state, 'paid')
        self.assertFalse(later.exists())
        later = investment.interest_line_ids.filtered(lambda line: line.period_date > withdrawal.date)
        self.assertTrue(all(line.state == 'accrued' for line in later))
        self.assertAlmostEqual(later.sorted('period_date')[0].base_amount, 99000.0)
        self.assertEqual(len(investment.interest_line_ids), 3)

    def test_future_withdrawal_rejected_without_generating_interest(self):
        investment = self._investment()
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id, 'principal_amount': 1000.0,
            'date': fields.Date.add(fields.Date.context_today(self.env.user), days=1),
        })
        with self.assertRaises(ValidationError):
            withdrawal.action_post()
        self.assertEqual(withdrawal.state, 'draft')
        self.assertFalse(investment.interest_line_ids)

    def test_principal_change_invalidates_cached_outstanding(self):
        investment = self._investment()
        self.assertEqual(investment.outstanding_principal, 100000.0)
        investment.principal_amount = 120000.0
        self.assertEqual(investment.outstanding_principal, 120000.0)

    def _reduced_rate_investment(self):
        return self._investment(start_date='2025-01-15', maturity_date='2026-01-15',
                                passive_rate=1.5, early_withdrawal_rate=1.0,
                                rate_period='monthly', principal_amount=100000.0)

    def _post_withdrawal(self, investment, amount, date):
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id, 'principal_amount': amount, 'date': date,
        })
        withdrawal.action_post()
        return withdrawal

    def test_remaining_principal_continues_at_one_percent(self):
        investment = self._reduced_rate_investment()
        self.assertEqual(investment.current_rate, 1.5)
        first = self._post_withdrawal(investment, 20000.0, '2025-03-15')
        self.assertAlmostEqual(first.gross_interest_amount, 2010.0)
        self.assertAlmostEqual(investment.current_rate, 1.0)
        self.assertAlmostEqual(investment.passive_rate, 1.5)
        investment._generate_interest_until(fields.Date.to_date('2025-05-15'), investment.passive_rate)
        later = investment.interest_line_ids.filtered(lambda line: line.period_date > first.date).sorted('period_date')
        self.assertEqual(later.mapped('rate'), [1.0, 1.0])
        self.assertAlmostEqual(later[0].base_amount, 80000.0)
        self.assertAlmostEqual(later[0].amount, 800.0)
        self.assertAlmostEqual(later[1].amount, 808.0)

    def test_second_early_withdrawal_pays_only_new_interest(self):
        investment = self._reduced_rate_investment()
        first = self._post_withdrawal(investment, 20000.0, '2025-03-15')
        paid_history = investment.interest_line_ids
        second = self._post_withdrawal(investment, 30000.0, '2025-04-15')
        self.assertAlmostEqual(second.gross_interest_amount, 800.0)
        self.assertEqual(second.effective_rate, 1.0)
        self.assertTrue(all(line.state == 'paid' for line in paid_history.exists()))
        self.assertEqual(len(paid_history.exists()), 2)
        self.assertAlmostEqual(first.gross_interest_amount, 2010.0)
        investment._generate_interest_until(fields.Date.to_date('2025-05-15'), 1.5)
        latest = investment.interest_line_ids.sorted('period_date')[-1]
        self.assertAlmostEqual(latest.base_amount, 50000.0)
        self.assertAlmostEqual(latest.amount, 500.0)
        second.action_post()
        self.assertAlmostEqual(investment.outstanding_principal, 50000.0)

    def test_same_day_withdrawals_do_not_duplicate_interest(self):
        investment = self._reduced_rate_investment()
        self._post_withdrawal(investment, 20000.0, '2025-03-15')
        second = self._post_withdrawal(investment, 30000.0, '2025-03-15')
        self.assertAlmostEqual(second.gross_interest_amount, 0.0)
        self.assertEqual(second.effective_rate, 1.0)
        investment._generate_interest_until(fields.Date.to_date('2025-04-15'), 1.5)
        self.assertAlmostEqual(investment.interest_line_ids.sorted('period_date')[-1].amount, 500.0)

    def test_final_early_withdrawal_closes_without_repaying_history(self):
        investment = self._reduced_rate_investment()
        self._post_withdrawal(investment, 20000.0, '2025-03-15')
        final = self._post_withdrawal(investment, 80000.0, '2025-04-15')
        self.assertAlmostEqual(final.total_amount, 80800.0)
        self.assertAlmostEqual(investment.outstanding_principal, 0.0)
        self.assertEqual(investment.state, 'closed')

    def test_precomputed_future_interest_rebuilt_at_reduced_rate(self):
        investment = self._reduced_rate_investment()
        investment._generate_interest_until(fields.Date.to_date('2025-05-15'), 1.5)
        self._post_withdrawal(investment, 20000.0, '2025-03-15')
        last = investment.interest_line_ids.sorted('period_date')[-1]
        self.assertEqual(last.rate, 1.0)
        self.assertAlmostEqual(last.amount, 808.0)
        self.assertEqual(len(investment.interest_line_ids), 4)
        ids = investment.interest_line_ids.ids
        investment._generate_interest_until(fields.Date.to_date('2025-05-15'), 1.5)
        self.assertEqual(investment.interest_line_ids.ids, ids)

    def test_future_paid_interest_blocks_backdated_withdrawal(self):
        investment = self._reduced_rate_investment()
        investment._generate_interest_until(fields.Date.to_date('2025-05-15'), 1.5)
        investment.interest_line_ids[-1].state = 'paid'
        original = investment.interest_line_ids
        with self.assertRaises(ValidationError):
            self._post_withdrawal(investment, 20000.0, '2025-03-15')
        self.assertEqual(investment.interest_line_ids, original)
        self.assertAlmostEqual(investment.outstanding_principal, 100000.0)

    def test_new_withdrawal_cannot_precede_applied_withdrawal(self):
        investment = self._reduced_rate_investment()
        self._post_withdrawal(investment, 20000.0, '2025-03-15')
        with self.assertRaises(ValidationError):
            self._post_withdrawal(investment, 1000.0, '2025-02-15')
        self.assertAlmostEqual(investment.outstanding_principal, 80000.0)

    def test_reduced_annual_rate_retains_period_units(self):
        investment = self._investment(start_date='2025-01-15', maturity_date='2026-01-15',
                                      passive_rate=18.0, early_withdrawal_rate=12.0)
        self._post_withdrawal(investment, 20000.0, '2025-03-15')
        investment._generate_interest_until(fields.Date.to_date('2025-04-15'), 18.0)
        latest = investment.interest_line_ids.sorted('period_date')[-1]
        self.assertEqual(investment.current_rate, 12.0)
        self.assertAlmostEqual(latest.amount, 800.0)

    def test_applied_withdrawal_history_cannot_be_edited_deleted_or_copied_as_paid(self):
        investment = self._reduced_rate_investment()
        withdrawal = self._post_withdrawal(investment, 20000.0, '2025-03-15')
        for vals in ({'principal_amount': 30000.0}, {'date': '2025-04-15'},
                     {'effective_rate': 1.5}, {'state': 'draft'}):
            with self.assertRaises(ValidationError):
                withdrawal.write(vals)
        with self.assertRaises(ValidationError):
            withdrawal.unlink()
        duplicate = withdrawal.copy()
        self.assertEqual(duplicate.state, 'draft')
        self.assertEqual(duplicate.gross_interest_amount, 0.0)
        self.assertEqual(duplicate.effective_rate, 0.0)
        self.assertAlmostEqual(investment.outstanding_principal, 80000.0)

    def test_withdrawal_cannot_inject_state_or_interest(self):
        investment = self._reduced_rate_investment()
        for extra in ({'state': 'posted'}, {'effective_rate': 1.0}, {'accrued_interest_amount': 999.0}):
            with self.assertRaises(ValidationError):
                self.env['lenka.investment.withdrawal'].create({
                    'investment_id': investment.id, 'principal_amount': 20000.0, **extra,
                })

    def test_second_withdrawal_does_not_repeat_historical_accounting_adjustment(self):
        investment = self._reduced_rate_investment()
        self._post_withdrawal(investment, 20000.0, '2025-03-15')
        second = self._post_withdrawal(investment, 30000.0, '2025-04-15')
        # No debe intentar crear un ajuste historico ni requerir cuentas para ello.
        second.action_create_early_withdrawal_adjustment()
        self.assertFalse(second.adjustment_move_id)

    def test_paid_interest_cannot_be_reopened_changed_or_deleted(self):
        investment = self._reduced_rate_investment()
        self._post_withdrawal(investment, 20000.0, '2025-03-15')
        paid = investment.interest_line_ids
        for vals in ({'state': 'accrued'}, {'amount': 1.0}, {'tax_rate': 50.0}):
            with self.assertRaises(ValidationError):
                paid.write(vals)
        with self.assertRaises(ValidationError):
            paid.unlink()
        self.assertAlmostEqual(investment.paid_interest, 2010.0)

    def test_accrued_interest_locks_terms_but_allows_early_recalculation(self):
        investment = self._reduced_rate_investment()
        investment._generate_interest_until(fields.Date.to_date('2025-03-15'), 1.5)
        with self.assertRaises(ValidationError):
            investment.early_withdrawal_rate = .1
        withdrawal = self._post_withdrawal(investment, 20000.0, '2025-03-15')
        self.assertAlmostEqual(withdrawal.gross_interest_amount, 2010.0)
        self.assertAlmostEqual(investment.current_rate, 1.0)

    def test_draft_investment_without_history_can_be_corrected_and_deleted(self):
        investment = self.env['lenka.investment'].create({
            'partner_id': self.partner.id, 'principal_amount': 10000.0,
            'passive_rate': 1.5, 'early_withdrawal_rate': 1.0,
            'rate_period': 'monthly', 'term_months': 12,
        })
        investment.principal_amount = 12000.0
        investment.passive_rate = 1.4
        investment.unlink()
        self.assertFalse(investment.exists())

    def test_mixed_investment_term_edit_rejected_before_draft_changes(self):
        used = self._reduced_rate_investment()
        self._post_withdrawal(used, 20000.0, '2025-03-15')
        draft = used.copy()
        with self.assertRaises(ValidationError):
            (draft | used).write({'passive_rate': 2.0})
        self.assertEqual(draft.passive_rate, 1.5)
