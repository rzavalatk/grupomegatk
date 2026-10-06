from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestLenkaPaymentAccess(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente permisos Lenka'})
        users = cls.env['res.users'].with_context(no_reset_password=True, tracking_disable=True)
        cls.operator = users.create({
            'name': 'Operador Lenka prueba', 'login': 'lenka_operator_access_test',
            'company_id': cls.company.id, 'company_ids': [(6, 0, cls.company.ids)],
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('lenka_financiero.group_lenka_user').id])],
        })
        cls.outsider = users.create({
            'name': 'Usuario sin Lenka prueba', 'login': 'lenka_outsider_access_test',
            'company_id': cls.company.id, 'company_ids': [(6, 0, cls.company.ids)],
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def _operation(self, company=None):
        company = company or self.company
        operation = self.env['lenka.financial.operation'].with_company(company).create({
            'partner_id': self.partner.id, 'company_id': company.id,
            'operation_type': 'loan', 'principal_amount': 10000.0,
            'interest_rate': 3.0, 'rate_period': 'monthly', 'term_months': 12,
            'calculation_method': 'level', 'first_payment_date': fields.Date.today(),
        })
        operation.action_generate_schedule()
        operation.state = 'active'
        operation.schedule_line_ids.sorted('sequence')[0].late_fee_due = 100.0
        return operation

    def _payment(self, operation):
        return self.env['lenka.payment'].create({
            'operation_id': operation.id, 'payment_date': fields.Date.today(),
            'amount': 2500.0, 'payment_method': 'cash',
        })

    def test_operator_can_create_apply_and_cancel_collection(self):
        operation = self._operation()
        self.assertFalse(self.operator.has_group('lenka_financiero.group_lenka_manager'))
        payment = self.env['lenka.payment'].with_user(self.operator).create({
            'operation_id': operation.id, 'amount': 2500.0, 'payment_method': 'cash',
            'payment_date': fields.Date.today(),
        })
        payment.action_post()
        self.assertEqual(payment.state, 'posted')
        self.assertAlmostEqual(payment.late_fee_amount, 100.0, places=2)
        self.assertAlmostEqual(payment.interest_amount, 300.0, places=2)
        self.assertAlmostEqual(payment.capital_amount, 2100.0, places=2)
        self.assertTrue(payment.allocation_line_ids)
        self.assertAlmostEqual(operation.outstanding_capital, 7900.0, places=2)
        payment.action_cancel()
        self.assertEqual(payment.state, 'cancelled')
        self.assertAlmostEqual(operation.outstanding_capital, 10000.0, places=2)
        self.assertAlmostEqual(operation.paid_interest, 0.0, places=2)
        self.assertAlmostEqual(operation.paid_late_fees, 0.0, places=2)

    def test_operator_cannot_edit_schedule_or_allocation_manually(self):
        operation = self._operation()
        payment = self._payment(operation).with_user(self.operator)
        payment.action_post()
        line = operation.schedule_line_ids.sorted('sequence')[0].with_user(self.operator)
        with self.assertRaises(AccessError):
            line.write({'capital_paid': 9000.0})
        with self.assertRaises(AccessError):
            payment.allocation_line_ids.write({'capital_amount': 9000.0})
        with self.assertRaises(AccessError):
            self.env['lenka.payment.allocation'].with_user(self.operator).create({
                'payment_id': payment.id, 'schedule_line_id': line.id, 'capital_amount': 9000.0,
            })
        self.assertAlmostEqual(operation.outstanding_capital, 7900.0, places=2)

    def test_user_without_lenka_cannot_apply_or_cancel(self):
        operation = self._operation()
        payment = self._payment(operation)
        with self.assertRaises(AccessError):
            payment.with_user(self.outsider).action_post()
        self.assertEqual(payment.state, 'draft')
        self.assertFalse(payment.allocation_line_ids)
        self.assertAlmostEqual(operation.outstanding_capital, 10000.0, places=2)
        payment.action_post()
        with self.assertRaises(AccessError):
            payment.with_user(self.outsider).action_cancel()
        self.assertEqual(payment.state, 'posted')
        self.assertAlmostEqual(operation.outstanding_capital, 7900.0, places=2)

    def test_operator_cannot_apply_or_cancel_other_company_collection(self):
        other_company = self.env['res.company'].create({'name': 'Empresa aislada Lenka pruebas'})
        operation = self._operation(other_company)
        payment = self._payment(operation)
        restricted = payment.with_user(self.operator).with_context(allowed_company_ids=self.company.ids)
        with self.assertRaises(AccessError):
            restricted.action_post()
        self.assertEqual(payment.state, 'draft')
        self.assertAlmostEqual(operation.outstanding_capital, 10000.0, places=2)
        payment.action_post()
        with self.assertRaises(AccessError):
            restricted.action_cancel()
        self.assertEqual(payment.state, 'posted')
        self.assertAlmostEqual(operation.outstanding_capital, 7900.0, places=2)

    def test_mixed_company_batch_rejected_before_any_allocation(self):
        own_payment = self._payment(self._operation())
        other_company = self.env['res.company'].create({'name': 'Empresa lote aislado Lenka'})
        other_payment = self._payment(self._operation(other_company))
        batch = (own_payment | other_payment).with_user(self.operator).with_context(allowed_company_ids=self.company.ids)
        with self.assertRaises(AccessError):
            batch.action_post()
        self.assertEqual(own_payment.state, 'draft')
        self.assertEqual(other_payment.state, 'draft')
        self.assertFalse(own_payment.allocation_line_ids)
        self.assertFalse(other_payment.allocation_line_ids)
