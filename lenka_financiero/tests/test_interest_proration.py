from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestLenkaInterestProration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Inversionista base 30 de prueba'})

    def _investment(self, **extra):
        vals = {
            'partner_id': self.partner.id, 'principal_amount': 100000.0,
            'passive_rate': 1.5, 'early_withdrawal_rate': 1.0,
            'rate_period': 'monthly', 'investment_type': 'fixed',
            'start_date': '2025-01-15', 'maturity_date': '2026-01-15',
            'capitalization': 'monthly',
        }
        vals.update(extra)
        investment = self.env['lenka.investment'].create(vals)
        investment.action_activate()
        return investment

    def _withdraw(self, investment, date, capital):
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id, 'date': date, 'principal_amount': capital,
        })
        withdrawal.action_post()
        return withdrawal

    def _generate(self, investment, date):
        investment._generate_interest_until(fields.Date.to_date(date), investment.passive_rate)

    def test_first_ten_days_are_paid_on_thirty_day_basis(self):
        investment = self._investment()
        withdrawal = self._withdraw(investment, '2025-01-25', 100000.0)
        self.assertAlmostEqual(withdrawal.gross_interest_amount, 333.33, places=2)
        self.assertAlmostEqual(withdrawal.total_amount, 100333.33, places=2)
        line = investment.interest_line_ids
        self.assertEqual(line.period_start_date, fields.Date.to_date('2025-01-15'))
        self.assertEqual(line.period_date, withdrawal.date)
        self.assertEqual(line.calculation_days, 10)
        self.assertTrue(line.is_prorated)
        self.assertEqual(line.rate, 1.0)
        self.assertEqual(line.state, 'paid')
        self.assertEqual(investment.state, 'closed')

    def test_partial_withdrawal_splits_month_and_compounds_at_anniversary(self):
        investment = self._investment()
        self._withdraw(investment, '2025-01-25', 20000.0)
        self._generate(investment, '2025-03-15')
        lines = investment.interest_line_ids.sorted('period_date')
        self.assertEqual(lines.mapped('calculation_days'), [10, 21, 30])
        self.assertEqual(lines.mapped('is_prorated'), [True, True, False])
        self.assertAlmostEqual(lines[1].base_amount, 80000.0)
        self.assertAlmostEqual(lines[1].amount, 560.0)
        self.assertAlmostEqual(lines[2].base_amount, 80560.0)
        self.assertAlmostEqual(lines[2].amount, 805.60)
        self.assertEqual(lines[1:].mapped('rate'), [1.0, 1.0])

    def test_two_withdrawals_in_same_month_use_each_remaining_balance(self):
        investment = self._investment()
        first = self._withdraw(investment, '2025-01-25', 20000.0)
        second = self._withdraw(investment, '2025-01-30', 30000.0)
        self.assertAlmostEqual(first.gross_interest_amount, 333.33)
        self.assertAlmostEqual(second.gross_interest_amount, 133.33)
        self._generate(investment, '2025-02-15')
        latest = investment.interest_line_ids.sorted('period_date')[-1]
        self.assertEqual(latest.calculation_days, 16)
        self.assertAlmostEqual(latest.base_amount, 50000.0)
        self.assertAlmostEqual(latest.amount, 266.67)

    def test_repeated_generation_and_same_day_withdrawal_do_not_duplicate_days(self):
        investment = self._investment()
        self._withdraw(investment, '2025-01-25', 20000.0)
        second = self._withdraw(investment, '2025-01-25', 30000.0)
        self.assertEqual(second.gross_interest_amount, 0.0)
        self._generate(investment, '2025-02-15')
        before = investment.interest_line_ids
        amounts = before.mapped('amount')
        self._generate(investment, '2025-02-15')
        self.assertEqual(investment.interest_line_ids, before)
        self.assertEqual(before.mapped('amount'), amounts)
        self.assertAlmostEqual(before.sorted('period_date')[-1].amount, 350.0)

    def test_complete_february_month_is_one_month_in_both_years(self):
        for year, end in ((2024, '2024-02-29'), (2025, '2025-02-28')):
            investment = self._investment(start_date='%s-01-31' % year, maturity_date='%s-05-31' % year)
            self._generate(investment, end)
            line = investment.interest_line_ids
            self.assertEqual(line.calculation_days, 30)
            self.assertFalse(line.is_prorated)
            self.assertAlmostEqual(line.amount, 1500.0)

    def test_partial_february_uses_elapsed_days_divided_by_thirty(self):
        for year in (2024, 2025):
            investment = self._investment(start_date='%s-01-31' % year, maturity_date='%s-05-31' % year)
            withdrawal = self._withdraw(investment, '%s-02-10' % year, 100000.0)
            self.assertEqual(investment.interest_line_ids.calculation_days, 10)
            self.assertAlmostEqual(withdrawal.gross_interest_amount, 333.33)

    def test_full_month_plus_five_days_recalculates_at_reduced_rate(self):
        investment = self._investment()
        self._generate(investment, '2025-03-15')
        withdrawal = self._withdraw(investment, '2025-02-20', 100000.0)
        # Un mes: 100000 * 1%; cinco dias: 101000 * 1% * 5/30.
        self.assertAlmostEqual(withdrawal.gross_interest_amount, 1168.33)
        self.assertEqual(len(investment.interest_line_ids), 2)
        self.assertFalse(investment.interest_line_ids.filtered(lambda line: line.period_date > withdrawal.date))

    def test_off_anniversary_maturity_includes_final_fraction(self):
        investment = self._investment(maturity_date='2025-02-20')
        self._generate(investment, '2025-02-20')
        lines = investment.interest_line_ids.sorted('period_date')
        self.assertEqual(lines.mapped('calculation_days'), [30, 5])
        self.assertAlmostEqual(lines[0].amount, 1500.0)
        self.assertAlmostEqual(lines[1].amount, 253.75)
        withdrawal = self._withdraw(investment, '2025-02-20', 100000.0)
        self.assertFalse(withdrawal.early_withdrawal)
        self.assertAlmostEqual(withdrawal.gross_interest_amount, 1753.75)

    def test_regular_generation_does_not_create_daily_capitalization(self):
        investment = self._investment()
        self._generate(investment, '2025-01-25')
        self.assertFalse(investment.interest_line_ids)
        self._generate(investment, '2025-02-15')
        self.assertEqual(len(investment.interest_line_ids), 1)
        self.assertAlmostEqual(investment.interest_line_ids.amount, 1500.0)

    def test_withdrawal_on_start_date_has_no_interest(self):
        investment = self._investment()
        withdrawal = self._withdraw(investment, '2025-01-15', 20000.0)
        self.assertEqual(withdrawal.gross_interest_amount, 0.0)
        self.assertFalse(investment.interest_line_ids)
        self._generate(investment, '2025-02-15')
        self.assertAlmostEqual(investment.interest_line_ids.amount, 800.0)

    def test_annual_rate_and_noncapitalizing_deposit_prorate_correctly(self):
        investment = self._investment(passive_rate=18.0, early_withdrawal_rate=12.0,
                                      rate_period='annual', capitalization='maturity')
        withdrawal = self._withdraw(investment, '2025-02-20', 100000.0)
        self.assertAlmostEqual(withdrawal.gross_interest_amount, 1166.67)

    def test_fractional_interest_tax_and_statement_end_at_zero(self):
        self.env['ir.config_parameter'].sudo().set_param('lenka_financiero.passive_interest_tax_rate', '10')
        investment = self._investment()
        withdrawal = self._withdraw(investment, '2025-01-25', 100000.0)
        self.assertAlmostEqual(withdrawal.interest_tax_amount, 33.33, places=2)
        self.assertAlmostEqual(withdrawal.accrued_interest_amount, 300.0, places=2)
        self.assertAlmostEqual(withdrawal.total_amount, 100300.0, places=2)
        statement = self.env['lenka.statement'].create({
            'statement_type': 'investment', 'investment_id': investment.id,
            'partner_id': self.partner.id, 'company_id': investment.company_id.id,
            'currency_id': investment.currency_id.id,
            'date_from': '2025-01-15', 'date_to': '2025-01-25',
        })
        statement.action_generate()
        self.assertAlmostEqual(statement.closing_balance, 0.0, places=2)
        self.assertEqual(len(statement.line_ids), 4)

    def test_paid_fraction_is_preserved_when_later_periods_are_generated(self):
        investment = self._investment()
        self._withdraw(investment, '2025-01-25', 20000.0)
        paid = investment.interest_line_ids
        self._generate(investment, '2025-03-15')
        self.assertEqual(paid.state, 'paid')
        self.assertEqual(paid.calculation_days, 10)
        self.assertAlmostEqual(paid.amount, 333.33)
        with self.assertRaises(ValidationError):
            self._withdraw(investment, '2025-01-20', 1000.0)
        self.assertEqual(paid.state, 'paid')
