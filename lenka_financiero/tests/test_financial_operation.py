from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestLenkaFinancialOperation(TransactionCase):

    def test_monthly_dates_keep_original_day_after_february(self):
        from odoo import fields
        for start, dates in [
            ('2027-01-31', ['2027-01-31', '2027-02-28', '2027-03-31', '2027-04-30']),
            ('2028-01-30', ['2028-01-30', '2028-02-29', '2028-03-30', '2028-04-30']),
        ]:
            with self.subTest(start=start):
                operation = self._operation('level', term=4)
                operation.first_payment_date = start
                operation.action_generate_schedule()
                self.assertEqual(operation.schedule_line_ids.sorted('sequence').mapped('date'), [fields.Date.to_date(d) for d in dates])

    def test_extra_payments_in_same_installment_are_added(self):
        operation = self._operation('balloon')
        operation.extra_payment_line_ids = [
            (0, 0, {'installment_number': 6, 'amount': 5000.0}),
            (0, 0, {'installment_number': 6, 'amount': 7000.0}),
        ]
        operation.action_generate_schedule()
        sixth = operation.schedule_line_ids.filtered(lambda line: line.sequence == 6)
        self.assertAlmostEqual(sixth.extra_charge, 12000.0, places=2)
        self.assertAlmostEqual(sum(operation.schedule_line_ids.mapped('capital')), 100000.0, places=2)

    def test_invalid_regeneration_preserves_existing_schedule(self):
        operation = self._operation('balloon')
        operation.action_generate_schedule()
        original = operation.schedule_line_ids
        operation.extra_payment_line_ids = [(0, 0, {'installment_number': 13, 'amount': 1000.0})]
        with self.assertRaises(ValidationError):
            operation.action_generate_schedule()
        self.assertEqual(operation.schedule_line_ids, original)
        self.assertTrue(original.exists())

    def test_mixed_valid_and_active_batch_preserves_all_schedules(self):
        draft = self._operation('level')
        active = self._operation('level')
        (draft | active).action_generate_schedule()
        original = draft.schedule_line_ids
        active.state = 'active'
        with self.assertRaises(ValidationError):
            (draft | active).action_generate_schedule()
        self.assertEqual(draft.schedule_line_ids, original)

    def test_funding_edit_cannot_exceed_financed_total(self):
        operation = self._operation('level')
        lines = self.env['lenka.funding.line'].create([
            {'operation_id': operation.id, 'source_type': 'own', 'amount': 60000.0},
            {'operation_id': operation.id, 'source_type': 'cash', 'amount': 40000.0},
        ])
        with self.assertRaises(ValidationError), self.cr.savepoint():
            lines[1].amount = 50000.0
        self.assertAlmostEqual(sum(operation.funding_line_ids.mapped('amount')), 100000.0, places=2)

    def test_funding_source_edit_requires_provider(self):
        operation = self._operation('level')
        funding = self.env['lenka.funding.line'].create({'operation_id': operation.id, 'source_type': 'own', 'amount': 50000.0})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            funding.source_type = 'bank_loan'
        funding.write({'source_type': 'bank_loan', 'partner_id': self.partner.id})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            funding.partner_id = False

    def test_funding_cannot_be_moved_to_smaller_operation(self):
        original = self._operation('level')
        smaller = self._operation('level')
        smaller.principal_amount = 10000.0
        funding = self.env['lenka.funding.line'].create({'operation_id': original.id, 'source_type': 'own', 'amount': 50000.0})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            funding.operation_id = smaller
        self.assertEqual(funding.operation_id, original)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente Prueba Lenka'})

    def _operation(self, method, rate=3.0, term=12):
        return self.env['lenka.financial.operation'].create({
            'partner_id': self.partner.id,
            'operation_type': 'loan',
            'principal_amount': 100000.0,
            'down_payment': 0.0,
            'interest_rate': rate,
            'rate_period': 'monthly',
            'term_months': term,
            'calculation_method': method,
        })

    def test_level_payment_3_percent_12_months(self):
        operation = self._operation('level')
        operation.action_generate_schedule()
        self.assertEqual(len(operation.schedule_line_ids), 12)
        first = operation.schedule_line_ids.sorted('sequence')[0]
        last = operation.schedule_line_ids.sorted('sequence')[-1]
        self.assertAlmostEqual(first.payment, 10046.21, places=2)
        self.assertAlmostEqual(first.interest, 3000.0, places=2)
        self.assertAlmostEqual(last.closing_balance, 0.0, places=2)
        self.assertAlmostEqual(sum(operation.schedule_line_ids.mapped('capital')), 100000.0, places=2)

    def test_balance_method_has_fixed_capital_and_decreasing_payment(self):
        operation = self._operation('balance')
        operation.action_generate_schedule()
        lines = operation.schedule_line_ids.sorted('sequence')
        self.assertAlmostEqual(lines[0].capital, 100000.0 / 12.0, places=2)
        self.assertAlmostEqual(lines[0].interest, 3000.0, places=2)
        self.assertGreater(lines[0].payment, lines[-1].payment)
        self.assertAlmostEqual(lines[-1].closing_balance, 0.0, places=2)

    def test_interest_only_pays_capital_at_end(self):
        operation = self._operation('interest_only')
        operation.action_generate_schedule()
        lines = operation.schedule_line_ids.sorted('sequence')
        self.assertEqual(len(lines), 12)
        self.assertAlmostEqual(lines[0].capital, 0.0, places=2)
        self.assertAlmostEqual(lines[0].interest, 3000.0, places=2)
        self.assertAlmostEqual(lines[-1].capital, 100000.0, places=2)
        self.assertAlmostEqual(lines[-1].payment, 103000.0, places=2)
        self.assertAlmostEqual(lines[-1].closing_balance, 0.0, places=2)

    def test_annual_rate_converts_to_monthly_nominal_rate(self):
        operation = self._operation('interest_only', rate=18.0, term=1)
        operation.rate_period = 'annual'
        operation.action_generate_schedule()
        line = operation.schedule_line_ids[0]
        self.assertAlmostEqual(line.interest, 1500.0, places=2)

    def test_financing_down_payment_reduces_financed_amount(self):
        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.partner.id,
            'operation_type': 'financing',
            'principal_amount': 100000.0,
            'down_payment': 20000.0,
            'interest_rate': 3.0,
            'rate_period': 'monthly',
            'term_months': 12,
            'calculation_method': 'level',
        })
        self.assertAlmostEqual(
            operation.financed_amount,
            80000.0,
            places=2,
            msg=(
                f"principal={operation.principal_amount!r}, "
                f"prima={operation.down_payment!r}, "
                f"financiado={operation.financed_amount!r}, "
                f"moneda={operation.currency_id.name}, "
                f"redondeo={operation.currency_id.rounding!r}"
            ),
        )
        operation.action_generate_schedule()
        self.assertAlmostEqual(sum(operation.schedule_line_ids.mapped('capital')), 80000.0, places=2)

    def test_balloon_extra_payment_reduces_future_interest(self):
        normal = self._operation('level')
        normal.action_generate_schedule()
        normal_lines = normal.schedule_line_ids.sorted('sequence')

        balloon = self._operation('balloon')
        balloon.write({
            'balloon_base_payment': normal_lines[0].payment,
            'extra_payment_line_ids': [(0, 0, {
                'installment_number': 6,
                'amount': 20000.0,
                'note': 'Cuota bomba mes 6',
            })],
        })
        balloon.action_generate_schedule()
        balloon_lines = balloon.schedule_line_ids.sorted('sequence')

        sixth = balloon_lines.filtered(lambda l: l.sequence == 6)
        seventh = balloon_lines.filtered(lambda l: l.sequence == 7)
        self.assertAlmostEqual(sixth.extra_charge, 20000.0, places=2)
        self.assertLess(seventh.interest, normal_lines[6].interest)
        self.assertAlmostEqual(balloon_lines[-1].closing_balance, 0.0, places=2)

    def test_balloon_payment_outside_term_is_rejected(self):
        operation = self._operation('balloon', term=12)
        operation.write({
            'extra_payment_line_ids': [(0, 0, {
                'installment_number': 13,
                'amount': 5000.0,
            })],
        })
        with self.assertRaises(ValidationError):
            operation.action_generate_schedule()


    def test_approved_operation_financial_terms_are_locked(self):
        guarantor = self.env['res.partner'].create({'name': 'Aval bloqueo condiciones'})
        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.partner.id,
            'guarantor_ids': [(6, 0, [guarantor.id])],
            'operation_type': 'loan',
            'principal_amount': 100000.0,
            'interest_rate': 3.0,
            'rate_period': 'monthly',
            'term_months': 12,
            'calculation_method': 'level',
            'is_quote': False,
            'state': 'review',
        })
        operation.action_generate_schedule()
        operation.action_approve()
        with self.assertRaises(ValidationError):
            operation.write({'interest_rate': 4.0})
        with self.assertRaises(ValidationError):
            operation.write({'term_months': 18})
        with self.assertRaises(ValidationError):
            operation.write({'principal_amount': 120000.0})

    def test_review_operation_financial_terms_can_still_change(self):
        operation = self._operation('level')
        operation.write({'state': 'review'})
        operation.write({'interest_rate': 4.0, 'term_months': 18})
        self.assertAlmostEqual(operation.interest_rate, 4.0, places=2)
        self.assertEqual(operation.term_months, 18)
