from datetime import timedelta
from lxml import html
from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from .test_cashflow import TestCashflowForecast


class TestCompletedPaymentsAndReports(TestCashflowForecast):
    def payment(self, amount=100):
        return self.env['cashflow.promise'].create({
            'plan_id': self.plan.id, 'partner_id': self.partner.id,
            'direction': 'payable', 'period': 'week_1', 'amount': amount,
            'classification': 'creditor',
        })

    def test_full_payment_leaves_projection_keeps_history_no_accounting(self):
        promise = self.payment()
        moves = self.env['account.move'].search_count([])
        payments = self.env['account.payment'].search_count([])
        self.assertEqual(self.plan.total_expected_payable, 100)
        promise._complete_payment(100, fields.Date.today(), 'Comprobante ficticio')
        self.assertEqual(promise.state, 'paid')
        self.assertEqual(promise.paid_amount, 100)
        self.assertEqual(promise.paid_by, self.env.user)
        self.assertEqual(self.plan.total_expected_payable, 0)
        self.assertFalse(self.plan.creditor_promise_ids)
        self.assertNotIn(self.partner.name, str(self.plan._cashflow_report_sections()))
        self.assertEqual(self.env['account.move'].search_count([]), moves)
        self.assertEqual(self.env['account.payment'].search_count([]), payments)
        self.assertIn(('plan_id', '=', self.plan.id), self.plan.action_view_completed_payments()['domain'])

    def test_partial_payment_projects_only_remainder(self):
        promise = self.payment()
        promise._complete_payment(35, fields.Date.today(), 'Abono ficticio')
        remaining = self.plan.creditor_promise_ids
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining.amount, 65)
        self.assertEqual(self.plan.payable_week_1, 65)
        self.assertEqual(promise.amount, 100)
        self.assertEqual(promise.paid_amount, 35)
        self.assertFalse(remaining.paid_date)
        self.assertTrue(promise.message_ids)

    def test_bad_amount_date_reference_and_repeat_rejected(self):
        promise = self.payment()
        for amount in (0, -1, 101):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                promise._complete_payment(amount, fields.Date.today(), 'Prueba')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            promise._complete_payment(100, fields.Date.today() + timedelta(days=1), 'Prueba')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            promise._complete_payment(100, fields.Date.today(), '  ')
        promise._complete_payment(100, fields.Date.today(), 'Prueba')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            promise._complete_payment(100, fields.Date.today(), 'Prueba')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            promise.action_reactivate()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            promise.unlink()

    def test_forged_completion_audit_is_rejected(self):
        promise = self.payment()
        with self.assertRaises(AccessError), self.cr.savepoint():
            promise.write({'state': 'paid'})
        with self.assertRaises(AccessError), self.cr.savepoint():
            promise.write({'paid_amount': 100})
        with self.assertRaises(AccessError), self.cr.savepoint():
            promise.copy({'state': 'paid'})

    def test_aged_columns_removed_without_changing_native_buckets(self):
        for xmlid in ('aged_payable_report', 'aged_receivable_report'):
            report = self.env.ref('account_reports.' + xmlid)
            labels = report.column_ids.mapped('expression_label')
            self.assertTrue({'period0', 'period1', 'period2', 'period3', 'period4', 'period5', 'total'}.issubset(labels))
            self.assertFalse(set(labels) & {'cashflow_week_1','cashflow_week_2','cashflow_week_3','cashflow_pending'})

    def test_html_borders_and_utf8_are_present_in_rendered_report(self):
        self.partner.name = 'Clínica Castellón'
        self.payment()
        Report = self.env['ir.actions.report']
        body, _ = Report._render_qweb_html('megatk_cash_flow_forecast.action_report_cashflow_preview', self.plan.ids)
        text = body.decode('utf-8')
        self.assertIn('Clínica Castellón', text)
        self.assertNotIn('CastellÃ', text)
        doc = html.fromstring(body)
        self.assertTrue(doc.xpath('//meta[@charset="utf-8"]'))
        self.assertTrue(doc.xpath('//th[contains(@style,"border:1px solid")]'))
        # Odoo parses the raw bytes before converting the PDF. Encoding must
        # survive this step too, not just look correct in a browser.
        bodies, *_ = Report._prepare_html(body)
        self.assertTrue(any('Clínica Castellón' in b.decode('utf-8') for b in bodies))
