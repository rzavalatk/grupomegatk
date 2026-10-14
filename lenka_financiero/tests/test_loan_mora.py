from datetime import date
from unittest import TestCase

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from ..late_fee import balance_late_fees


class TestBalanceLateFees(TestCase):
    def calc(self, end=date(2026, 2, 1), payments=(), lines=None, grace=0, rate=2):
        return balance_late_fees(10000, rate, grace,
            lines or [(1, date(2026, 1, 2), 0, 300)], payments, end)

    def test_thirty_days_interest_only(self):
        self.assertAlmostEqual(float(self.calc()[1]), 200)

    def test_no_arrears_on_due_date_or_grace(self):
        self.assertEqual(self.calc(end=date(2026, 1, 2))[1], 0)
        self.assertEqual(self.calc(end=date(2026, 1, 7), grace=5)[1], 0)
        self.assertAlmostEqual(float(self.calc(end=date(2026, 1, 8), grace=5)[1]), 200/30)

    def test_multiple_overdue_installments_do_not_multiply_charge(self):
        totals=self.calc(lines=[(1, date(2026, 1, 2), 0, 300), (2, date(2026, 1, 10), 0, 300)])
        self.assertAlmostEqual(float(sum(totals.values())), 200)
        self.assertEqual(totals[2], 0)

    def test_payment_cures_interest_arrears(self):
        totals=self.calc(payments=[(date(2026, 1, 17), 0, [(1, 0, 300)])])
        self.assertAlmostEqual(float(totals[1]), 100)

    def test_partial_payment_and_principal_reduction_preserve_prior_days(self):
        totals=self.calc(payments=[(date(2026, 1, 17), 5000, [(1, 0, 100)])])
        self.assertAlmostEqual(float(totals[1]), 150)

    def test_pre_due_payment_reduces_base(self):
        totals=self.calc(payments=[(date(2026, 1, 1), 5000, [])])
        self.assertAlmostEqual(float(totals[1]), 100)

    def test_zero_rate_and_paid_capital_stop_accrual(self):
        self.assertEqual(self.calc(rate=0)[1], 0)
        self.assertEqual(self.calc(payments=[(date(2026, 1, 1), 10000, [])])[1], 0)

    def test_refresh_is_deterministic(self):
        self.assertEqual(self.calc(), self.calc())


class TestLoanMoraIntegration(TransactionCase):
    def operation(self, **values):
        partner=self.env['res.partner'].create({'name':'Cliente ficticio mora', 'is_company':True})
        op=self.env['lenka.financial.operation'].create({
            'partner_id':partner.id, 'operation_type':'loan', 'principal_amount':10000,
            'interest_rate':3, 'term_months':18, 'calculation_method':'interest_then_level',
            'interest_only_months':6, 'first_payment_date':date(2026,1,2),
            'late_fee_rate':2, 'late_fee_method':'balance_monthly', **values})
        op.action_generate_schedule()
        return op

    def test_refresh_prorates_interest_only_and_does_not_duplicate(self):
        op=self.operation()
        op._update_balance_late_fees(date(2026,2,1))
        self.assertAlmostEqual(sum(op.schedule_line_ids.mapped('late_fee_due')),200)
        op._update_balance_late_fees(date(2026,2,1))
        self.assertAlmostEqual(sum(op.schedule_line_ids.mapped('late_fee_due')),200)

    def test_payment_automatically_updates_mora_and_cures_arrears(self):
        op=self.operation();op.state='active'
        payment=self.env['lenka.payment'].create({'operation_id':op.id,'amount':400,'payment_date':date(2026,1,17)})
        payment.action_post()
        self.assertAlmostEqual(payment.late_fee_amount,100)
        self.assertAlmostEqual(payment.interest_amount,300)
        op._update_balance_late_fees(date(2026,2,1))
        self.assertAlmostEqual(sum(op.schedule_line_ids.mapped('late_fee_due')),100)
        payment.action_cancel()
        op._update_balance_late_fees(date(2026,2,1))
        self.assertAlmostEqual(sum(op.schedule_line_ids.mapped('late_fee_due')),200)

    def test_legacy_method_is_preserved(self):
        op=self.operation(late_fee_method='legacy')
        self.assertEqual(op.late_fee_method,'legacy')
        self.assertEqual(self.env['lenka.financial.operation']._fields['late_fee_method'].default(op),'legacy')

    def test_terms_reject_invalid_values_and_lock_after_approval(self):
        op=self.operation()
        for values in ({'late_fee_rate':-1},{'late_fee_rate':101},{'grace_days':-1}):
            with self.assertRaises(ValidationError),self.cr.savepoint():op.write(values)
        op.state='approved'
        for values in ({'late_fee_rate':3},{'late_fee_method':'legacy'},{'grace_days':5}):
            with self.assertRaises(ValidationError):op.write(values)

    def test_company_contract_has_dynamic_mora_firmants_and_full_annex(self):
        op=self.operation(security_mode='sole_signature',late_fee_rate=1.25,grace_days=3)
        op.contract_buyer_representative='Representante ficticio'
        op.contract_buyer_authority='Poder ficticio para pruebas'
        template=self.env['lenka.contract.template']._approved_unsecured_loan_template(op.company_id)
        body=op._render_lenka_template(template)
        self.assertIn('1.25 % mensual',body)
        self.assertIn('3 días de gracia',body)
        self.assertIn('Representante ficticio',body)
        self.assertIn('Poder ficticio para pruebas',body)
        self.assertIn('Anexo 1: plan de pagos',body)
        self.assertIn('6 meses de solo intereses y 12 meses de cuota nivelada',body)
        self.assertNotIn('{{',body)
        self.assertIn('no lo convierte en aval',body)

    def test_loan_template_rejects_legacy_basis_and_backed_operation(self):
        op=self.operation(security_mode='sole_signature',late_fee_method='legacy')
        template=self.env['lenka.contract.template']._approved_unsecured_loan_template(op.company_id)
        with self.assertRaises(ValidationError):op._render_lenka_template(template)
        op.write({'late_fee_method':'balance_monthly','security_mode':'backed'})
        with self.assertRaises(ValidationError):op._render_lenka_template(template)

    def test_new_loan_form_defaults_and_zero_rate_contract(self):
        defaults=self.env['lenka.financial.operation'].with_context(default_operation_type='loan').default_get(['operation_type','late_fee_method','late_fee_rate'])
        self.assertEqual(defaults['late_fee_method'],'balance_monthly')
        self.assertEqual(defaults['late_fee_rate'],2)
        op=self.operation(security_mode='sole_signature',late_fee_rate=0)
        template=self.env['lenka.contract.template']._approved_unsecured_loan_template(op.company_id)
        self.assertIn('0 % mensual',op._render_lenka_template(template))

    def test_same_day_collection_and_historical_cancellation_guard(self):
        op=self.operation();op.state='active'
        Payment=self.env['lenka.payment']
        first=Payment.create({'operation_id':op.id,'amount':100,'payment_date':date(2026,1,17)})
        first.action_post()
        second=Payment.create({'operation_id':op.id,'amount':300,'payment_date':date(2026,1,17)})
        second.action_post()
        self.assertAlmostEqual(second.late_fee_amount,0)
        self.assertAlmostEqual(second.interest_amount,300)
        with self.assertRaises(ValidationError):first.action_cancel()
        second.action_cancel();first.action_cancel()
        self.assertEqual(first.state,'cancelled')

    def test_backdated_and_future_collections_are_rejected(self):
        op=self.operation();op.state='active'
        Payment=self.env['lenka.payment']
        first=Payment.create({'operation_id':op.id,'amount':400,'payment_date':date(2026,1,17)})
        first.action_post()
        for date_value in (date(2026,1,16), fields.Date.add(fields.Date.context_today(op),days=1)):
            payment=Payment.create({'operation_id':op.id,'amount':100,'payment_date':date_value})
            with self.assertRaises(ValidationError):payment.action_post()
            self.assertEqual(payment.state,'draft')
