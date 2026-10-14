from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestLenkaStatement(TransactionCase):

    def _statement(self):
        return self.env['lenka.statement'].create({
            'statement_type': 'operation', 'partner_id': self.partner.id,
            'operation_id': self.operation.id, 'company_id': self.operation.company_id.id,
            'currency_id': self.operation.currency_id.id,
            'date_from': fields.Date.today(), 'date_to': fields.Date.add(fields.Date.today(), months=2),
        })

    def test_draft_identity_edits_are_revalidated(self):
        statement = self._statement()
        other_currency = self.env['res.currency'].with_context(active_test=False).search([('id', '!=', statement.currency_id.id)], limit=1)
        other_company = self.env['res.company'].create({'name': 'Empresa estado incorrecto'})
        for vals in [{'partner_id': self.other_partner.id}, {'currency_id': other_currency.id}, {'company_id': other_company.id}]:
            with self.subTest(vals=vals), self.assertRaises(ValidationError), self.cr.savepoint():
                statement.write(vals)

    def test_sent_statement_cannot_be_regenerated_or_rewritten(self):
        statement = self._statement()
        statement.action_generate()
        statement.write({'state': 'sent', 'sent_date': fields.Datetime.now()})
        for vals in [{'date_to': fields.Date.today()}, {'closing_balance': 1.0}, {'state': 'draft'}]:
            with self.subTest(vals=vals), self.assertRaises(ValidationError):
                statement.write(vals)
        with self.assertRaises(ValidationError):
            statement.action_generate()
        with self.assertRaisesRegex(ValidationError, 'Solo pueden enviarse'):
            statement.action_send_email()

    def test_generated_statement_period_cannot_change(self):
        statement = self._statement()
        statement.action_generate()
        with self.assertRaises(ValidationError):
            statement.date_from = fields.Date.add(statement.date_from, days=1)

    def test_duplicate_statement_is_clean_draft(self):
        statement = self._statement()
        statement.action_generate()
        statement.write({'state': 'sent', 'sent_date': fields.Datetime.now()})
        copy = statement.copy()
        self.assertEqual(copy.state, 'draft')
        self.assertFalse(copy.sent_date)
        self.assertFalse(copy.line_ids)
        self.assertAlmostEqual(copy.opening_balance, 0.0, places=2)
        self.assertAlmostEqual(copy.closing_balance, 0.0, places=2)
        copy.action_generate()
        self.assertEqual(copy.closing_balance, statement.closing_balance)

    def test_cancelled_statement_cannot_be_generated_or_sent(self):
        statement = self._statement()
        statement.state = 'cancelled'
        with self.assertRaises(ValidationError):
            statement.action_generate()
        with self.assertRaisesRegex(ValidationError, 'Solo pueden enviarse'):
            statement.action_send_email()

    def test_onchange_source_fills_identity_and_currency(self):
        statement = self.env['lenka.statement'].new({'statement_type': 'operation', 'operation_id': self.operation.id})
        statement._onchange_source()
        self.assertEqual(statement.partner_id, self.partner)
        self.assertEqual(statement.company_id, self.operation.company_id)
        self.assertEqual(statement.currency_id, self.operation.currency_id)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente Estado Lenka'})
        cls.other_partner = cls.env['res.partner'].create({'name': 'Cliente Incorrecto Lenka'})
        cls.operation = cls.env['lenka.financial.operation'].create({
            'partner_id': cls.partner.id,
            'operation_type': 'loan',
            'principal_amount': 10000.0,
            'interest_rate': 3.0,
            'rate_period': 'monthly',
            'term_months': 12,
            'calculation_method': 'level',
            'state': 'review',
        })
        cls.operation.action_generate_schedule()
        cls.operation.state = 'active'

    def test_operation_statement_balance_uses_capital_only(self):
        first = self.operation.schedule_line_ids.sorted('sequence')[0]
        payment = self.env['lenka.payment'].create({
            'operation_id': self.operation.id,
            'payment_date': first.date,
            'amount': first.amount_due,
            'payment_method': 'cash',
        })
        payment.action_post()
        statement = self.env['lenka.statement'].create({
            'statement_type': 'operation',
            'partner_id': self.partner.id,
            'operation_id': self.operation.id,
            'company_id': self.operation.company_id.id,
            'currency_id': self.operation.currency_id.id,
            'date_from': first.date,
            'date_to': first.date,
        })
        statement.action_generate()
        self.assertAlmostEqual(statement.opening_balance, 10000.0, places=2)
        self.assertAlmostEqual(
            statement.closing_balance,
            10000.0 - payment.capital_amount,
            places=2,
        )
        self.assertAlmostEqual(statement.period_interest, payment.interest_amount, places=2)

    def test_statement_rejects_wrong_partner(self):
        today = fields.Date.context_today(self.env.user)
        with self.assertRaises(ValidationError):
            self.env['lenka.statement'].create({
                'statement_type': 'operation',
                'partner_id': self.other_partner.id,
                'operation_id': self.operation.id,
                'company_id': self.operation.company_id.id,
                'currency_id': self.operation.currency_id.id,
                'date_from': today - timedelta(days=30),
                'date_to': today,
            })

    def test_statement_rejects_inverted_dates(self):
        today = fields.Date.context_today(self.env.user)
        with self.assertRaises(ValidationError):
            self.env['lenka.statement'].create({
                'statement_type': 'operation',
                'partner_id': self.partner.id,
                'operation_id': self.operation.id,
                'company_id': self.operation.company_id.id,
                'currency_id': self.operation.currency_id.id,
                'date_from': today,
                'date_to': today - timedelta(days=1),
            })

    def _taxed_investment_statement(self, date_from='2025-01-15', date_to='2025-02-15', withdraw=False):
        investment = self.env['lenka.investment'].create({
            'partner_id': self.partner.id, 'principal_amount': 10000.0,
            'passive_rate': 10.0, 'early_withdrawal_rate': 1.0,
            'rate_period': 'monthly', 'start_date': '2025-01-15',
            'maturity_date': '2025-02-15', 'capitalization': 'maturity',
        })
        investment.action_activate()
        interest = self.env['lenka.investment.interest'].create({
            'investment_id': investment.id, 'period_date': '2025-02-15',
            'base_amount': 10000.0, 'rate': 10.0, 'amount': 1000.0,
            'tax_rate': 10.0, 'state': 'accrued',
        })
        if withdraw:
            self.env['lenka.investment.withdrawal'].create({
                'investment_id': investment.id, 'principal_amount': 10000.0,
                'date': '2025-02-15',
            }).action_post()
        statement = self.env['lenka.statement'].create({
            'statement_type': 'investment', 'partner_id': self.partner.id,
            'investment_id': investment.id, 'company_id': investment.company_id.id,
            'currency_id': investment.currency_id.id, 'date_from': date_from, 'date_to': date_to,
        })
        statement.action_generate()
        return statement, interest

    def test_investment_statement_separates_withholding_from_investor_balance(self):
        statement, interest = self._taxed_investment_statement()
        self.assertAlmostEqual(statement.closing_balance, 10900.0)
        self.assertAlmostEqual(statement.period_interest, 1000.0)
        self.assertEqual(len(statement.line_ids), 3)
        self.assertAlmostEqual(sum(statement.line_ids.mapped('debit')), 100.0)
        self.assertAlmostEqual(sum(statement.line_ids.mapped('credit')), 10000.0 + interest.amount)
        statement.action_generate()
        self.assertEqual(len(statement.line_ids), 3)
        self.assertAlmostEqual(statement.closing_balance, 10900.0)

    def test_fully_withdrawn_investment_has_no_residual_tax_balance(self):
        statement, interest = self._taxed_investment_statement(withdraw=True)
        self.assertEqual(interest.state, 'paid')
        self.assertAlmostEqual(statement.closing_balance, 0.0)
        self.assertAlmostEqual(statement.opening_balance + sum(statement.line_ids.mapped('credit'))
                               - sum(statement.line_ids.mapped('debit')), 0.0)

    def test_investment_opening_balance_uses_net_interest(self):
        statement, _ = self._taxed_investment_statement(date_from='2025-03-01', date_to='2025-03-31')
        self.assertAlmostEqual(statement.opening_balance, 10900.0)
        self.assertAlmostEqual(statement.closing_balance, 10900.0)
        self.assertFalse(statement.line_ids)

    def test_closed_investment_next_statement_opens_at_zero(self):
        statement, _ = self._taxed_investment_statement(date_from='2025-03-01', date_to='2025-03-31', withdraw=True)
        self.assertAlmostEqual(statement.opening_balance, 0.0)
        self.assertAlmostEqual(statement.closing_balance, 0.0)
        self.assertFalse(statement.line_ids)

    def test_investment_statement_before_deposit_has_no_balance(self):
        statement, _ = self._taxed_investment_statement(date_from='2024-12-01', date_to='2024-12-31')
        self.assertAlmostEqual(statement.opening_balance, 0.0)
        self.assertAlmostEqual(statement.closing_balance, 0.0)
        self.assertFalse(statement.line_ids)

    def test_investment_deposit_appears_on_its_actual_date(self):
        for date_from in ('2025-01-01', '2025-01-15'):
            with self.subTest(date_from=date_from):
                statement, _ = self._taxed_investment_statement(date_from=date_from, date_to='2025-01-15')
                self.assertAlmostEqual(statement.opening_balance, 0.0)
                self.assertAlmostEqual(statement.closing_balance, 10000.0)
                self.assertEqual(len(statement.line_ids), 1)
                self.assertEqual(statement.line_ids.date, fields.Date.to_date('2025-01-15'))
                self.assertAlmostEqual(statement.line_ids.credit, 10000.0)
                statement.action_generate()
                self.assertEqual(len(statement.line_ids), 1)

    def test_investment_deposit_is_carried_forward_without_duplication(self):
        statement, _ = self._taxed_investment_statement(date_from='2025-01-16', date_to='2025-02-14')
        self.assertAlmostEqual(statement.opening_balance, 10000.0)
        self.assertAlmostEqual(statement.closing_balance, 10000.0)
        self.assertFalse(statement.line_ids)

    def test_investment_print_displays_deposit_withdrawal_and_tax_amounts(self):
        from lxml import html as html_parser
        statement, _ = self._taxed_investment_statement(withdraw=True)
        report = self.env.ref('lenka_financiero.action_report_lenka_statement')
        rendered, _ = report._render_qweb_html(report.report_name, docids=statement.ids)
        document = html_parser.fromstring(rendered)
        rows = document.xpath('//table[@name="investment_movements"]/tbody/tr')
        self.assertEqual(len(rows), 4)
        amounts = []
        for row in rows:
            cells = row.xpath('./td')
            amounts.append(tuple(''.join(c for c in cell.text_content() if c.isdigit()) for cell in cells[-2:]))
        self.assertCountEqual(amounts, [('1000000', '000'), ('100000', '000'), ('000', '10000'), ('000', '1090000')])
        self.assertAlmostEqual(statement.opening_balance + sum(statement.line_ids.mapped('credit'))
                               - sum(statement.line_ids.mapped('debit')), statement.closing_balance)

    def test_monthly_generation_includes_final_closed_investment_once(self):
        from unittest.mock import patch
        statement, _ = self._taxed_investment_statement(withdraw=True)
        investment = statement.investment_id
        self.assertEqual(investment.state, 'closed')
        self.env['ir.config_parameter'].sudo().set_param('lenka_financiero.auto_send_statements', 'False')
        model = self.env['lenka.statement']
        with patch('odoo.addons.lenka_financiero.models.statement.fields.Date.context_today',
                   return_value=fields.Date.to_date('2025-03-01')):
            model._cron_generate_monthly_statements()
            model._cron_generate_monthly_statements()
        monthly = model.search([('investment_id', '=', investment.id), ('date_from', '=', '2025-02-01')])
        self.assertEqual(len(monthly), 1)
        self.assertEqual(monthly.state, 'generated')
        self.assertFalse(monthly.sent_date)
        self.assertAlmostEqual(monthly.opening_balance, 10000.0)
        self.assertAlmostEqual(monthly.closing_balance, 0.0)
        self.assertEqual(len(monthly.line_ids), 3)
        with patch('odoo.addons.lenka_financiero.models.statement.fields.Date.context_today',
                   return_value=fields.Date.to_date('2025-04-01')):
            model._cron_generate_monthly_statements()
        self.assertFalse(model.search([('investment_id', '=', investment.id), ('date_from', '=', '2025-03-01')]))

    def test_monthly_generation_skips_investments_not_started_in_period(self):
        from unittest.mock import patch
        investment = self.env['lenka.investment'].create({
            'partner_id': self.partner.id, 'principal_amount': 10000.0,
            'passive_rate': 1.0, 'early_withdrawal_rate': 0.5, 'start_date': '2025-03-15',
            'maturity_date': '2026-03-15',
        })
        investment.action_activate()
        self.env['ir.config_parameter'].sudo().set_param('lenka_financiero.auto_send_statements', 'False')
        with patch('odoo.addons.lenka_financiero.models.statement.fields.Date.context_today',
                   return_value=fields.Date.to_date('2025-03-01')):
            self.env['lenka.statement']._cron_generate_monthly_statements()
        self.assertFalse(self.env['lenka.statement'].search([('investment_id', '=', investment.id)]))
