from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestLenkaPayment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente Cobros Lenka'})

    def _operation(self, first_payment_date=None):
        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.partner.id,
            'operation_type': 'loan',
            'principal_amount': 100000.0,
            'interest_rate': 3.0,
            'rate_period': 'monthly',
            'term_months': 12,
            'calculation_method': 'level',
            'first_payment_date': first_payment_date or fields.Date.context_today(self.env.user),
        })
        operation.action_generate_schedule()
        operation.state = 'active'
        return operation

    def _draft_payment(self, operation=None):
        operation = operation or self._operation()
        return self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': operation.schedule_line_ids.sorted('sequence')[0].date,
            'amount': 15000.0,
            'payment_method': 'cash',
        })

    def test_applied_payment_financial_data_is_immutable(self):
        payment = self._draft_payment()
        payment.action_post()
        balance = payment.operation_id.outstanding_capital
        changes = [
            {'amount': 20000.0},
            {'payment_date': fields.Date.add(payment.payment_date, days=1)},
            {'payment_method': 'card'},
            {'card_fee_rate': 5.0},
            {'operation_id': self._operation().id},
        ]
        for vals in changes:
            with self.subTest(vals=vals), self.assertRaises(ValidationError):
                payment.write(vals)
        self.assertAlmostEqual(payment.amount, 15000.0, places=2)
        self.assertAlmostEqual(payment.operation_id.outstanding_capital, balance, places=2)
        payment.write({'notes': 'Referencia verificada', 'reference': 'REC-123'})
        self.assertEqual(payment.reference, 'REC-123')

    def test_draft_payment_can_be_edited_before_posting(self):
        payment = self._draft_payment()
        payment.write({'amount': 10000.0, 'payment_method': 'card', 'card_fee_rate': 4.0})
        self.assertAlmostEqual(payment.net_bank_amount, 9600.0, places=2)
        payment.action_post()
        self.assertAlmostEqual(
            payment.capital_amount + payment.interest_amount + payment.late_fee_amount
            + payment.unapplied_amount, 9600.0, places=2,
        )

    def test_closed_operation_blocks_collection_cancellation(self):
        payment = self._draft_payment()
        operation = payment.operation_id
        first = operation.schedule_line_ids.sorted('sequence')[0]
        payment.amount = operation.financed_amount + first.interest
        payment.action_post()
        operation.action_close_paid_operation()
        with self.assertRaises(ValidationError):
            payment.action_cancel()
        self.assertEqual(operation.state, 'done')
        self.assertEqual(payment.state, 'posted')
        self.assertAlmostEqual(operation.outstanding_capital, 0.0, places=2)

    def test_cancel_batch_validates_before_changing_any_payment(self):
        first = self._draft_payment()
        first.action_post()
        second = self._draft_payment()
        second.action_post()
        second.operation_id.state = 'done'
        balance = first.operation_id.outstanding_capital
        with self.assertRaises(ValidationError):
            (first | second).action_cancel()
        self.assertEqual(first.state, 'posted')
        self.assertEqual(second.state, 'posted')
        self.assertAlmostEqual(first.operation_id.outstanding_capital, balance, places=2)

    def test_payment_cannot_skip_actions_via_create_or_write(self):
        payment = self._draft_payment()
        for vals in [{'state': 'posted'}, {'capital_amount': 5000.0}, {'extra_capital_amount': 5000.0}]:
            with self.subTest(vals=vals), self.assertRaises(ValidationError):
                payment.write(vals)
            with self.subTest(create_vals=vals), self.assertRaises(ValidationError):
                self.env['lenka.payment'].create({
                    'operation_id': payment.operation_id.id,
                    'amount': 5000.0,
                    **vals,
                })
        payment.action_post()
        for state in ['draft', 'cancelled']:
            with self.subTest(state=state), self.assertRaises(ValidationError):
                payment.write({'state': state})
        payment.action_cancel()
        self.assertEqual(payment.state, 'cancelled')
        with self.assertRaises(ValidationError):
            payment.write({'amount': 1000.0})

    def test_duplicate_applied_payment_is_clean_draft(self):
        payment = self._draft_payment()
        payment.action_post()
        balance = payment.operation_id.outstanding_capital
        duplicate = payment.copy()
        self.assertEqual(duplicate.state, 'draft')
        self.assertNotEqual(duplicate.name, payment.name)
        self.assertFalse(duplicate.allocation_line_ids)
        self.assertFalse(duplicate.move_id)
        for field in ['late_fee_amount', 'interest_amount', 'capital_amount', 'extra_capital_amount', 'unapplied_amount']:
            self.assertAlmostEqual(duplicate[field], 0.0, places=2)
        self.assertAlmostEqual(payment.operation_id.outstanding_capital, balance, places=2)

    def test_applied_and_cancelled_payments_cannot_be_deleted(self):
        payment = self._draft_payment()
        payment.action_post()
        with self.assertRaises(ValidationError):
            payment.unlink()
        payment.action_cancel()
        with self.assertRaises(ValidationError):
            payment.unlink()
        draft = self._draft_payment()
        draft.unlink()
        self.assertFalse(draft.exists())

    def test_mixed_batch_cannot_edit_applied_payment(self):
        draft = self._draft_payment()
        posted = self._draft_payment(draft.operation_id)
        posted.action_post()
        with self.assertRaises(ValidationError):
            (draft | posted).write({'amount': 20000.0})
        self.assertAlmostEqual(draft.amount, 15000.0, places=2)
        self.assertAlmostEqual(posted.amount, 15000.0, places=2)

    def test_repeated_post_and_cancel_do_not_duplicate_allocations(self):
        payment = self._draft_payment()
        operation = payment.operation_id
        payment.action_post()
        allocations = payment.allocation_line_ids
        balance = operation.outstanding_capital
        payment.action_post()
        self.assertEqual(payment.allocation_line_ids, allocations)
        self.assertAlmostEqual(operation.outstanding_capital, balance, places=2)
        payment.action_cancel()
        payment.action_cancel()
        self.assertAlmostEqual(operation.outstanding_capital, operation.financed_amount, places=2)

    def test_payment_priority_late_fee_interest_capital(self):
        operation = self._operation()
        first = operation.schedule_line_ids.sorted('sequence')[0]
        first.late_fee_due = 500.0

        payment = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': first.date,
            'amount': 4000.0,
            'payment_method': 'cash',
        })
        payment.action_post()

        self.assertAlmostEqual(payment.late_fee_amount, 500.0, places=2)
        self.assertAlmostEqual(payment.interest_amount, 3000.0, places=2)
        self.assertAlmostEqual(payment.capital_amount, 500.0, places=2)
        self.assertAlmostEqual(payment.extra_capital_amount, 0.0, places=2)

    def test_card_fee_reduces_amount_applied_to_debt(self):
        operation = self._operation()
        first = operation.schedule_line_ids.sorted('sequence')[0]

        payment = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': first.date,
            'amount': 100.0,
            'payment_method': 'card',
            'card_fee_rate': 3.5,
        })

        self.assertAlmostEqual(payment.card_fee_amount, 3.50, places=2)
        self.assertAlmostEqual(payment.net_bank_amount, 96.50, places=2)

        payment.action_post()
        self.assertAlmostEqual(
            payment.late_fee_amount + payment.interest_amount + payment.capital_amount + payment.unapplied_amount,
            96.50,
            places=2,
        )

    def test_overpayment_after_due_amount_goes_to_extra_capital(self):
        operation = self._operation()
        first = operation.schedule_line_ids.sorted('sequence')[0]
        due = first.capital + first.interest

        payment = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': first.date,
            'amount': due + 5000.0,
            'payment_method': 'transfer',
        })
        payment.action_post()

        self.assertAlmostEqual(payment.interest_amount, first.interest, places=2)
        self.assertAlmostEqual(first.capital_paid, first.capital, places=2)
        self.assertAlmostEqual(payment.extra_capital_amount, 5000.0, places=2)
        self.assertAlmostEqual(payment.unapplied_amount, 0.0, places=2)

    def test_future_interest_is_not_paid_in_advance(self):
        today = fields.Date.context_today(self.env.user)
        operation = self._operation(first_payment_date=fields.Date.add(today, months=1))

        payment = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': today,
            'amount': 10000.0,
            'payment_method': 'transfer',
        })
        payment.action_post()

        self.assertAlmostEqual(payment.interest_amount, 0.0, places=2)
        self.assertAlmostEqual(payment.capital_amount, 10000.0, places=2)
        self.assertAlmostEqual(payment.extra_capital_amount, 10000.0, places=2)

    def test_partial_payment_only_applies_available_amount(self):
        operation = self._operation()
        first = operation.schedule_line_ids.sorted('sequence')[0]

        payment = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': first.date,
            'amount': 1000.0,
            'payment_method': 'cash',
        })
        payment.action_post()

        self.assertAlmostEqual(payment.interest_amount, 1000.0, places=2)
        self.assertAlmostEqual(payment.capital_amount, 0.0, places=2)
        self.assertEqual(first.payment_state, 'partial')


    def test_cancel_posted_payment_restores_schedule_balances(self):
        operation = self._operation()
        first = operation.schedule_line_ids.sorted('sequence')[0]
        original_due = first.amount_due

        payment = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': first.date,
            'amount': 2500.0,
            'payment_method': 'cash',
        })
        payment.action_post()
        self.assertGreater(first.amount_paid, 0.0)

        payment.action_cancel()
        self.assertEqual(payment.state, 'cancelled')
        self.assertAlmostEqual(first.capital_paid, 0.0, places=2)
        self.assertAlmostEqual(first.interest_paid, 0.0, places=2)
        self.assertAlmostEqual(first.late_fee_paid, 0.0, places=2)
        self.assertAlmostEqual(first.amount_due, original_due, places=2)

    def test_payment_without_schedule_is_rejected(self):
        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.partner.id,
            'operation_type': 'loan',
            'principal_amount': 10000.0,
            'interest_rate': 3.0,
            'rate_period': 'monthly',
            'term_months': 12,
            'calculation_method': 'level',
        })
        payment = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'amount': 1000.0,
            'payment_method': 'cash',
        })
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            payment.action_post()

    def test_payment_above_total_capital_leaves_unapplied_balance(self):
        operation = self._operation()
        first = operation.schedule_line_ids.sorted('sequence')[0]
        payment = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': first.date,
            'amount': 200000.0,
            'payment_method': 'transfer',
        })
        payment.action_post()

        self.assertAlmostEqual(operation.outstanding_capital, 0.0, places=2)
        self.assertGreater(payment.unapplied_amount, 0.0)
        self.assertLessEqual(payment.capital_amount, operation.financed_amount + 0.01)

    def test_card_fee_rate_can_be_configured_globally(self):
        parameter = self.env['ir.config_parameter'].sudo()
        old_value = parameter.get_param('lenka_financiero.card_fee_rate')
        try:
            parameter.set_param('lenka_financiero.card_fee_rate', '4.25')
            operation = self._operation()
            payment = self.env['lenka.payment'].create({
                'operation_id': operation.id,
                'amount': 1000.0,
                'payment_method': 'card',
            })
            self.assertAlmostEqual(payment.card_fee_rate, 4.25, places=2)
            self.assertAlmostEqual(payment.card_fee_amount, 42.50, places=2)
            self.assertAlmostEqual(payment.net_bank_amount, 957.50, places=2)
        finally:
            if old_value is None:
                parameter.set_param('lenka_financiero.card_fee_rate', '3.5')
            else:
                parameter.set_param('lenka_financiero.card_fee_rate', old_value)

    def test_due_payment_after_extra_capital_cannot_collect_capital_twice(self):
        today = fields.Date.context_today(self.env.user)
        operation = self._operation(first_payment_date=fields.Date.add(today, months=1))
        advance = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': today,
            'amount': 99000.0,
            'payment_method': 'transfer',
        })
        advance.action_post()
        self.assertAlmostEqual(operation.outstanding_capital, 1000.0, places=2)

        first = operation.schedule_line_ids.sorted('sequence')[0]
        collection = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': first.date,
            'amount': first.interest + 5000.0,
            'payment_method': 'cash',
        })
        collection.action_post()
        self.assertAlmostEqual(collection.capital_amount, 1000.0, places=2)
        self.assertAlmostEqual(collection.extra_capital_amount, 0.0, places=2)
        self.assertAlmostEqual(collection.unapplied_amount, 4000.0, places=2)
        self.assertAlmostEqual(operation.paid_capital, operation.financed_amount, places=2)
        self.assertAlmostEqual(operation.outstanding_capital, 0.0, places=2)
        self.assertAlmostEqual(
            collection.capital_amount + collection.interest_amount
            + collection.late_fee_amount + collection.unapplied_amount,
            collection.net_bank_amount, places=2,
        )

        collection.action_cancel()
        self.assertAlmostEqual(operation.outstanding_capital, 1000.0, places=2)
        self.assertAlmostEqual(first.capital_paid, 0.0, places=2)
        advance.action_cancel()
        self.assertAlmostEqual(operation.outstanding_capital, operation.financed_amount, places=2)

    def test_fully_prepaid_capital_is_not_collected_at_maturity(self):
        today = fields.Date.context_today(self.env.user)
        operation = self._operation(first_payment_date=fields.Date.add(today, months=1))
        advance = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': today,
            'amount': operation.financed_amount,
            'payment_method': 'transfer',
        })
        advance.action_post()
        last = operation.schedule_line_ids.sorted('sequence')[-1]
        interest = sum(operation.schedule_line_ids.mapped('interest'))
        collection = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': last.date,
            'amount': interest + 5000.0,
            'payment_method': 'transfer',
        })
        collection.action_post()
        self.assertAlmostEqual(collection.capital_amount, 0.0, places=2)
        self.assertAlmostEqual(collection.unapplied_amount, 5000.0, places=2)
        self.assertAlmostEqual(operation.paid_capital, operation.financed_amount, places=2)

    def test_multiple_due_installments_are_paid_oldest_first(self):
        today = fields.Date.context_today(self.env.user)
        operation = self._operation(first_payment_date=fields.Date.add(today, months=-2))
        lines = operation.schedule_line_ids.sorted('sequence')
        first = lines[0]
        second = lines[1]
        first.late_fee_due = 100.0
        second.late_fee_due = 200.0

        amount = first.amount_due + 50.0
        payment = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': today,
            'amount': amount,
            'payment_method': 'cash',
        })
        payment.action_post()

        self.assertAlmostEqual(first.late_fee_paid, 100.0, places=2)
        self.assertAlmostEqual(second.late_fee_paid, 200.0, places=2)
        self.assertAlmostEqual(first.interest_paid, first.interest, places=2)
        self.assertGreaterEqual(first.capital_paid, 0.0)


    def test_payment_on_non_active_operation_is_rejected(self):
        from odoo.exceptions import ValidationError
        operation = self._operation()
        operation.state = 'approved'
        payment = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'amount': 1000.0,
            'payment_method': 'cash',
        })
        with self.assertRaises(ValidationError):
            payment.action_post()


    def test_paid_operation_marks_guarantee_pending_release(self):
        operation = self._operation()
        guarantee = self.env['lenka.guarantee'].create({
            'operation_id': operation.id,
            'guarantee_type': 'equipment',
            'description': 'Equipo financiado prueba',
            'state': 'active',
        })
        for line in operation.schedule_line_ids:
            line.write({
                'capital_paid': line.capital,
                'interest_paid': line.interest,
                'late_fee_paid': line.late_fee_due,
            })
        operation.action_close_paid_operation()
        self.assertEqual(operation.state, 'done')
        self.assertEqual(guarantee.state, 'release_pending')
        guarantee.action_release()
        self.assertEqual(guarantee.state, 'released')

    def test_guarantee_cannot_be_released_with_active_debt(self):
        from odoo.exceptions import ValidationError
        operation = self._operation()
        guarantee = self.env['lenka.guarantee'].create({
            'operation_id': operation.id,
            'guarantee_type': 'equipment',
            'description': 'Equipo aun garantizando deuda',
            'state': 'active',
        })
        with self.assertRaises(ValidationError):
            guarantee.action_release()
