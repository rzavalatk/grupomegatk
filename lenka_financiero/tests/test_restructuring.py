from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestLenkaRestructuring(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente Reestructuracion Lenka'})
        cls.guarantor = cls.env['res.partner'].create({'name': 'Aval Reestructuracion Lenka'})
        cls.operation = cls.env['lenka.financial.operation'].create({
            'partner_id': cls.partner.id,
            'guarantor_ids': [(6, 0, [cls.guarantor.id])],
            'operation_type': 'loan',
            'principal_amount': 100000.0,
            'interest_rate': 3.0,
            'rate_period': 'monthly',
            'term_months': 12,
            'calculation_method': 'level',
            'is_quote': False,
            'state': 'review',
        })
        cls.operation.action_generate_schedule()
        cls.operation.state = 'active'
        users = cls.env['res.users'].with_context(no_reset_password=True)
        cls.operator = users.create({
            'name': 'Operador reestructuracion', 'login': 'lenka_restructuring_operator',
            'company_id': cls.env.company.id, 'company_ids': [(6, 0, cls.env.company.ids)],
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('lenka_financiero.group_lenka_user').id])],
        })
        cls.manager = users.create({
            'name': 'Gerente reestructuracion', 'login': 'lenka_restructuring_manager',
            'company_id': cls.env.company.id, 'company_ids': [(6, 0, cls.env.company.ids)],
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('lenka_financiero.group_lenka_manager').id])],
        })

    def test_restructuring_preserves_original_snapshot(self):
        restructuring = self.env['lenka.restructuring'].create({
            'operation_id': self.operation.id, 'settlement_method': 'capitalize',
            'reason': 'Cliente solicita ampliar plazo',
            'proposed_interest_rate': 2.5,
            'proposed_term_months': 18,
        })
        self.assertAlmostEqual(restructuring.original_outstanding_capital, self.operation.outstanding_capital, places=2)
        self.assertAlmostEqual(restructuring.original_interest_rate, 3.0, places=2)
        self.assertEqual(restructuring.original_term_months, 12)

    def test_restructuring_requires_active_operation(self):
        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.partner.id,
            'operation_type': 'loan',
            'principal_amount': 50000.0,
            'interest_rate': 2.0,
            'rate_period': 'monthly',
            'term_months': 6,
            'calculation_method': 'level',
            'is_quote': False,
            'state': 'review',
        })
        with self.assertRaises(ValidationError):
            self.env['lenka.restructuring'].create({
                'operation_id': operation.id,
                'reason': 'No debe permitirse aun',
                'proposed_principal_amount': 50000.0,
                'proposed_interest_rate': 2.0,
                'proposed_term_months': 6,
            })

    def test_approved_restructuring_prepares_successor_without_mutating_original(self):
        original_rate = self.operation.interest_rate
        original_term = self.operation.term_months
        restructuring = self.env['lenka.restructuring'].create({
            'operation_id': self.operation.id, 'settlement_method': 'capitalize',
            'reason': 'Extender plazo y reducir tasa',
            'proposed_principal_amount': self.operation.outstanding_capital,
            'proposed_interest_rate': 2.5,
            'proposed_rate_period': 'monthly',
            'proposed_term_months': 18,
            'proposed_calculation_method': 'level',
        })
        restructuring.action_submit()
        restructuring.action_approve()
        restructuring.action_prepare_successor()
        self.assertEqual(restructuring.state, 'prepared')
        self.assertTrue(restructuring.successor_operation_id)
        successor = restructuring.successor_operation_id
        self.assertEqual(successor.state, 'review')
        self.assertAlmostEqual(successor.interest_rate, 2.5, places=2)
        self.assertEqual(successor.term_months, 18)
        self.assertEqual(len(successor.schedule_line_ids), 18)
        self.assertAlmostEqual(self.operation.interest_rate, original_rate, places=2)
        self.assertEqual(self.operation.term_months, original_term)
        self.assertEqual(self.operation.state, 'active')

    def test_restructuring_blocked_when_unapplied_collection_exists(self):
        payment = self.env['lenka.payment'].create({
            'operation_id': self.operation.id,
            'payment_date': fields.Date.context_today(self.env.user),
            'amount': 110000.0,
            'payment_method': 'cash',
        })
        payment.action_post()
        self.assertGreater(payment.unapplied_amount, 0.0)
        restructuring = self.env['lenka.restructuring'].create({
            'operation_id': self.operation.id, 'settlement_method': 'capitalize',
            'reason': 'Debe regularizar cobro',
            'proposed_principal_amount': 1000.0,
            'proposed_interest_rate': 2.0,
            'proposed_term_months': 18,
        })
        restructuring.action_submit()
        with self.assertRaises(ValidationError):
            restructuring.action_approve()


    def test_approved_restructuring_terms_are_locked(self):
        restructuring = self.env['lenka.restructuring'].create({
            'operation_id': self.operation.id, 'settlement_method': 'capitalize',
            'reason': 'Propuesta que debe quedar congelada',
            'proposed_principal_amount': self.operation.outstanding_capital,
            'proposed_interest_rate': 2.5,
            'proposed_term_months': 18,
        })
        restructuring.action_submit()
        restructuring.action_approve()
        with self.assertRaises(ValidationError):
            restructuring.write({'proposed_interest_rate': 4.0})
        with self.assertRaises(ValidationError):
            restructuring.write({'proposed_term_months': 24})


    def test_original_cannot_close_until_successor_is_active(self):
        restructuring = self.env['lenka.restructuring'].create({
            'operation_id': self.operation.id, 'settlement_method': 'capitalize',
            'reason': 'Sustitucion pendiente de activar',
            'proposed_principal_amount': self.operation.outstanding_capital,
            'proposed_interest_rate': 2.5,
            'proposed_term_months': 18,
        })
        restructuring.action_submit()
        restructuring.action_approve()
        restructuring.action_prepare_successor()
        self.assertEqual(restructuring.successor_operation_id.state, 'review')
        with self.assertRaises(ValidationError):
            restructuring.action_complete_restructuring()
        self.assertEqual(self.operation.state, 'active')
        self.assertFalse(restructuring.original_operation_closed)

    def test_complete_restructuring_closes_original_only_after_successor_active(self):
        guarantee = self.env['lenka.guarantee'].create({
            'operation_id': self.operation.id,
            'guarantee_type': 'equipment',
            'description': 'Garantia de operacion reestructurada',
            'state': 'active',
        })
        restructuring = self.env['lenka.restructuring'].create({
            'operation_id': self.operation.id, 'settlement_method': 'capitalize',
            'reason': 'Sustitucion completa',
            'proposed_principal_amount': self.operation.outstanding_capital,
            'proposed_interest_rate': 2.5,
            'proposed_term_months': 18,
        })
        restructuring.action_submit()
        restructuring.action_approve()
        restructuring.action_prepare_successor()
        restructuring.successor_operation_id.state = 'active'
        restructuring.action_complete_restructuring()
        self.assertEqual(self.operation.state, 'done')
        self.assertTrue(restructuring.original_operation_closed)
        self.assertEqual(guarantee.state, 'release_pending')

    def _request(self, user=None, **values):
        model = self.env['lenka.restructuring']
        if user:
            model = model.with_user(user)
        return model.create(dict({'operation_id': self.operation.id, 'settlement_method': 'capitalize', 'reason': 'Prueba de control de reestructuracion'}, **values))

    def test_operator_cannot_approve_prepare_or_complete_via_direct_call(self):
        request = self._request(user=self.operator)
        request.action_submit()
        with self.assertRaises(AccessError):
            request.action_approve()
        request.with_user(self.manager).action_approve()
        with self.assertRaises(AccessError):
            request.action_prepare_successor()
        request.with_user(self.manager).action_prepare_successor()
        with self.assertRaises(AccessError):
            request.action_complete_restructuring()
        self.assertEqual(self.operation.state, 'active')
        self.assertFalse(request.original_operation_closed)

    def test_state_and_successor_cannot_be_injected(self):
        for values in ({'state': 'approved'}, {'successor_operation_id': self.operation.id}, {'original_operation_closed': True}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                self._request(**values)
        request = self._request()
        for values in ({'state': 'approved'}, {'successor_operation_id': self.operation.id}, {'original_operation_closed': True}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                request.write(values)
        self.assertEqual(request.state, 'draft')

    def test_original_snapshot_is_captured_and_cannot_be_overwritten(self):
        request = self._request(original_outstanding_capital=1.0, original_interest_rate=99.0)
        self.assertAlmostEqual(request.original_outstanding_capital, self.operation.outstanding_capital)
        self.assertAlmostEqual(request.original_interest_rate, self.operation.interest_rate)
        for field in ('original_outstanding_capital', 'original_payoff_amount', 'original_interest_rate', 'original_term_months'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                request.write({field: 1.0})
        other = self.operation.copy({'state': 'active'})
        with self.assertRaises(ValidationError):
            request.operation_id = other

    def test_prepared_request_copy_starts_as_unlinked_draft(self):
        request = self._request()
        request.action_submit()
        request.action_approve()
        request.action_prepare_successor()
        copied = request.copy()
        self.assertEqual(copied.state, 'draft')
        self.assertNotEqual(copied.name, 'Nuevo')
        self.assertNotEqual(copied.name, request.name)
        self.assertFalse(copied.successor_operation_id)
        self.assertFalse(copied.original_operation_closed)
        self.assertAlmostEqual(copied.original_outstanding_capital, self.operation.outstanding_capital)

    def test_prepared_request_cannot_be_reopened_deleted_or_detached(self):
        request = self._request()
        request.action_submit()
        request.action_approve()
        request.action_prepare_successor()
        for values in ({'state': 'draft'}, {'successor_operation_id': False}, {'request_date': '2020-01-01'}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                request.write(values)
        with self.assertRaises(ValidationError):
            request.unlink()
        with self.assertRaises(ValidationError):
            request.action_cancel()

    def test_prepare_and_complete_are_safe_to_repeat(self):
        request = self._request(user=self.manager)
        request.action_submit()
        request.action_approve()
        request.action_prepare_successor()
        successor = request.successor_operation_id
        request.action_prepare_successor()
        self.assertEqual(request.successor_operation_id, successor)
        successor.state = 'active'
        request.action_complete_restructuring()
        request.action_complete_restructuring()
        self.assertEqual(self.operation.state, 'done')
        self.assertTrue(request.original_operation_closed)

    def test_inactive_original_blocks_approval_and_successor_creation(self):
        request = self._request()
        request.action_submit()
        self.operation.state = 'done'
        with self.assertRaises(ValidationError):
            request.action_approve()
        self.operation.state = 'active'
        request.action_approve()
        self.operation.state = 'done'
        with self.assertRaises(ValidationError):
            request.action_prepare_successor()
        self.assertFalse(request.successor_operation_id)

    def test_manager_cannot_approve_mixed_company_batch(self):
        own = self._request()
        own.action_submit()
        company = self.env['res.company'].create({'name': 'Empresa ajena reestructuracion'})
        other_operation = self.operation.copy({'company_id': company.id, 'state': 'active'})
        other = self.env['lenka.restructuring'].create({'operation_id': other_operation.id, 'reason': 'Solicitud de otra empresa'})
        other.action_submit()
        with self.assertRaises(AccessError):
            (own | other).with_user(self.manager).with_context(allowed_company_ids=self.env.company.ids).action_approve()
        self.assertEqual(own.state, 'review')
        self.assertEqual(other.state, 'review')

    def _operation_with_due_charges(self):
        operation = self.operation.copy({
            'state': 'review', 'first_payment_date': fields.Date.context_today(self.operation),
        })
        operation.action_generate_schedule()
        operation.schedule_line_ids.sorted('sequence')[0].late_fee_due = 200.0
        operation.state = 'active'
        self.operation = operation
        return operation

    def _pay(self, amount):
        payment = self.env['lenka.payment'].create({
            'operation_id': self.operation.id, 'amount': amount,
            'payment_date': fields.Date.context_today(self.operation), 'payment_method': 'cash',
        })
        payment.action_post()
        return payment

    def test_modality_must_be_explicitly_chosen(self):
        request = self._request(settlement_method=False)
        request.action_submit()
        with self.assertRaisesRegex(ValidationError, 'modalidad'):
            request.action_approve()
        self.assertEqual(request.state, 'review')

    def test_capitalize_due_charges_uses_new_principal_and_new_rate(self):
        self._operation_with_due_charges()
        request = self._request(proposed_interest_rate=2.0, proposed_term_months=18)
        self.assertAlmostEqual(request.pending_interest, 3000.0)
        self.assertAlmostEqual(request.pending_late_fees, 200.0)
        self.assertAlmostEqual(request.proposed_principal_amount, 103200.0)
        request.action_submit()
        request.with_user(self.manager).action_approve()
        self.assertEqual(request.approved_by, self.manager)
        self.assertAlmostEqual(request.approved_capital, 100000.0)
        self.assertAlmostEqual(request.approved_interest, 3000.0)
        request.with_user(self.manager).action_prepare_successor()
        successor = request.successor_operation_id
        self.assertAlmostEqual(successor.principal_amount, 103200.0)
        self.assertAlmostEqual(successor.schedule_line_ids.sorted('sequence')[0].interest, 2064.0)
        self.assertEqual(successor.term_months, 18)
        self.assertFalse(self.operation.payment_ids)

    def test_separate_payment_must_be_real_and_complete(self):
        self._operation_with_due_charges()
        request = self._request(settlement_method='pay_separately', proposed_interest_rate=2.0)
        request.action_submit()
        request.action_approve()
        with self.assertRaisesRegex(ValidationError, 'Registre el pago'):
            request.action_prepare_successor()
        self._pay(1000.0)
        with self.assertRaisesRegex(ValidationError, 'Registre el pago'):
            request.action_prepare_successor()
        self._pay(2200.0)
        request.action_prepare_successor()
        self.assertAlmostEqual(request.successor_operation_id.principal_amount, 100000.0)
        self.assertAlmostEqual(request.successor_operation_id.schedule_line_ids.sorted('sequence')[0].interest, 2000.0)
        self.assertAlmostEqual(self.operation.paid_interest, 3000.0)
        self.assertAlmostEqual(self.operation.paid_late_fees, 200.0)
        self.assertAlmostEqual(self.operation.paid_capital, 0.0)

    def test_cancelled_separate_payment_blocks_completion(self):
        self._operation_with_due_charges()
        request = self._request(settlement_method='pay_separately')
        request.action_submit()
        request.action_approve()
        payment = self._pay(3200.0)
        request.action_prepare_successor()
        request.successor_operation_id.state = 'active'
        payment.action_cancel()
        with self.assertRaisesRegex(ValidationError, 'Registre el pago'):
            request.action_complete_restructuring()
        self.assertEqual(self.operation.state, 'active')
        self.assertFalse(request.original_operation_closed)

    def test_changed_capital_requires_new_manager_approval(self):
        self._operation_with_due_charges()
        request = self._request(settlement_method='pay_separately')
        request.action_submit()
        request.action_approve()
        self._pay(4200.0)
        with self.assertRaisesRegex(ValidationError, 'capital cambio'):
            request.action_prepare_successor()
        with self.assertRaises(AccessError):
            request.with_user(self.operator).action_return_to_review()
        request.with_user(self.manager).action_return_to_review()
        request.action_refresh_proposal()
        self.assertAlmostEqual(request.proposed_principal_amount, 99000.0)
        request.action_approve()
        request.action_prepare_successor()
        self.assertAlmostEqual(request.successor_operation_id.financed_amount, 99000.0)

    def test_changed_charges_block_capitalization_until_reviewed(self):
        self._operation_with_due_charges()
        request = self._request()
        request.action_submit()
        request.action_approve()
        self.operation.schedule_line_ids.sorted('sequence')[0].late_fee_due = 300.0
        with self.assertRaisesRegex(ValidationError, 'intereses o la mora cambiaron'):
            request.action_prepare_successor()
        request.action_return_to_review()
        request.action_refresh_proposal()
        self.assertAlmostEqual(request.proposed_principal_amount, 103300.0)
        request.action_approve()
        request.action_prepare_successor()

    def test_changing_negotiated_modality_recalculates_before_approval(self):
        self._operation_with_due_charges()
        request = self._request()
        request.settlement_method = 'pay_separately'
        request.action_submit()
        with self.assertRaisesRegex(ValidationError, 'no coincide'):
            request.action_approve()
        request.action_refresh_proposal()
        self.assertAlmostEqual(request.proposed_principal_amount, 100000.0)
        request.action_approve()
        with self.assertRaises(ValidationError):
            request.settlement_method = 'capitalize'
        with self.assertRaises(ValidationError):
            request.approved_interest = 0.0

    def test_future_interest_is_not_added_to_restructured_principal(self):
        request = self._request()
        self.assertGreater(sum(self.operation.schedule_line_ids.mapped('interest')), 0.0)
        self.assertAlmostEqual(request.pending_interest, 0.0)
        self.assertAlmostEqual(request.proposed_principal_amount, 100000.0)

    def _contract_successor(self, request):
        successor = request.successor_operation_id
        successor.action_approve()
        self.env['lenka.contract.template'].create({
            'name': 'Contrato reestructuracion prueba', 'company_id': successor.company_id.id,
            'document_type': 'contract', 'operation_type': 'loan',
            'body_html': '<p>{{CLIENTE}} {{MONTO_FINANCIADO}}</p>',
        })
        successor.action_generate_contract_documents()
        document = successor.generated_document_ids.filtered(lambda d: d.document_type == 'contract')[0]
        document.attachment_id = self.env['ir.attachment'].create({
            'name': 'contrato-reestructuracion-prueba.pdf', 'datas': 'RklSTUFETw==',
            'res_model': document._name, 'res_id': document.id,
        })
        document.action_mark_signed()
        successor.action_mark_contracted()
        return successor

    def test_capitalized_debt_moves_without_cash_or_duplicate_balance(self):
        original = self._operation_with_due_charges()
        request = self._request(proposed_interest_rate=2.0)
        request.action_submit()
        request.action_approve()
        request.action_prepare_successor()
        successor = self._contract_successor(request)
        request.action_complete_restructuring()
        request.action_complete_restructuring()
        self.assertEqual(original.state, 'done')
        self.assertEqual(successor.state, 'active')
        self.assertAlmostEqual(original.outstanding_capital, 0.0)
        self.assertAlmostEqual(original.get_payoff_amount(), 0.0)
        self.assertAlmostEqual(original.paid_capital, 0.0)
        self.assertAlmostEqual(original.paid_interest, 0.0)
        self.assertAlmostEqual(original.net_collections, 0.0)
        self.assertAlmostEqual(original.transferred_capital, 100000.0)
        self.assertAlmostEqual(successor.outstanding_capital, 103200.0)
        self.assertAlmostEqual(successor.restructured_funding_amount, 103200.0)
        self.assertAlmostEqual(successor.disbursed_amount, 0.0)
        self.assertAlmostEqual(successor.pending_disbursement, 0.0)
        self.assertFalse(successor.disbursement_ids)
        self.assertFalse(original.payment_ids)
        self.assertTrue(request.completed_date)
        self.assertAlmostEqual(request.pending_capital, 0.0)
        self.assertAlmostEqual(request.pending_interest, 0.0)
        self.assertAlmostEqual(request.pending_late_fees, 0.0)
        self.assertAlmostEqual(request.approved_interest, 3000.0)
        with self.assertRaises(ValidationError):
            original.state = 'active'
        with self.assertRaises(ValidationError):
            request.completed_date = fields.Date.add(request.completed_date, days=1)

        model = self.env['lenka.statement']
        statement = model.create({
            'statement_type': 'operation', 'operation_id': original.id,
            'partner_id': original.partner_id.id, 'company_id': original.company_id.id,
            'currency_id': original.currency_id.id,
            'date_from': request.completed_date, 'date_to': request.completed_date,
        })
        statement.action_generate()
        statement.action_generate()
        self.assertAlmostEqual(statement.opening_balance, 100000.0)
        self.assertAlmostEqual(statement.closing_balance, 0.0)
        self.assertEqual(len(statement.line_ids), 1)
        self.assertEqual(statement.line_ids.reference, successor.name)
        self.assertIn('sin cobro', statement.line_ids.description)
        next_day = fields.Date.add(request.completed_date, days=1)
        following = statement.copy({'date_from': next_day, 'date_to': next_day})
        following.action_generate()
        self.assertAlmostEqual(following.opening_balance, 0.0)
        self.assertFalse(following.line_ids)

    def test_separate_payment_transfers_only_capital_and_keeps_actual_collections(self):
        original = self._operation_with_due_charges()
        request = self._request(settlement_method='pay_separately')
        request.action_submit()
        request.action_approve()
        payment = self._pay(3200.0)
        request.action_prepare_successor()
        successor = self._contract_successor(request)
        request.action_complete_restructuring()
        self.assertAlmostEqual(successor.outstanding_capital, 100000.0)
        self.assertAlmostEqual(original.outstanding_capital, 0.0)
        self.assertAlmostEqual(original.net_collections, 3200.0)
        self.assertAlmostEqual(original.paid_interest, 3000.0)
        self.assertAlmostEqual(original.paid_late_fees, 200.0)
        with self.assertRaises(ValidationError):
            payment.action_cancel()

    def test_restructuring_successor_cannot_receive_cash_disbursement(self):
        request = self._request()
        request.action_submit()
        request.action_approve()
        request.action_prepare_successor()
        successor = self._contract_successor(request)
        disbursement = self.env['lenka.disbursement'].create({
            'operation_id': successor.id, 'amount': successor.financed_amount,
        })
        with self.assertRaisesRegex(ValidationError, 'sin un nuevo desembolso'):
            disbursement.action_post()
        self.assertEqual(disbursement.state, 'draft')
        self.assertFalse(disbursement.move_id)
        self.assertAlmostEqual(successor.restructured_funding_amount, 0.0)
        with self.assertRaises(ValidationError):
            successor.action_activate()

    def test_successor_terms_must_match_approved_negotiation(self):
        request = self._request()
        request.action_submit()
        request.action_approve()
        request.action_prepare_successor()
        successor = request.successor_operation_id
        successor.interest_rate = 9.0
        successor.action_generate_schedule()
        self._contract_successor(request)
        with self.assertRaisesRegex(ValidationError, 'condiciones aprobadas'):
            request.action_complete_restructuring()
        self.assertEqual(self.operation.state, 'active')
        self.assertFalse(request.original_operation_closed)
        self.assertAlmostEqual(successor.restructured_funding_amount, 0.0)

    def test_successor_identity_cannot_change_before_contract(self):
        request = self._request()
        request.action_submit()
        request.action_approve()
        request.action_prepare_successor()
        successor = request.successor_operation_id
        other_currency = self.env['res.currency'].search([
            ('id', '!=', successor.currency_id.id),
        ], limit=1)
        other_company = self.env['res.company'].create({'name': 'Otra empresa Lenka'})
        changes = {
            'partner_id': self.guarantor.id,
            'company_id': other_company.id,
            'currency_id': other_currency.id,
            'operation_type': 'leasing',
        }
        for name, value in changes.items():
            with self.subTest(field=name), self.assertRaisesRegex(ValidationError, 'conservar el cliente'):
                successor.write({name: value})
        self.assertEqual(successor.partner_id, self.operation.partner_id)
        self.assertEqual(successor.company_id, self.operation.company_id)
        self.assertEqual(successor.currency_id, self.operation.currency_id)
        self.assertEqual(successor.operation_type, self.operation.operation_type)
        self.assertFalse(request.original_operation_closed)

    def test_successor_identity_noop_write_remains_allowed(self):
        request = self._request()
        request.action_submit()
        request.action_approve()
        request.action_prepare_successor()
        successor = request.successor_operation_id
        successor.write({
            'partner_id': successor.partner_id.id,
            'company_id': successor.company_id.id,
            'currency_id': successor.currency_id.id,
            'operation_type': successor.operation_type,
        })
        self._contract_successor(request)
        request.action_complete_restructuring()
        self.assertTrue(request.original_operation_closed)

    def test_changed_balance_can_replace_uncontracted_successor_with_new_approval(self):
        self._operation_with_due_charges()
        request = self._request()
        request.action_submit()
        request.action_approve()
        request.action_prepare_successor()
        former = request.successor_operation_id
        self._pay(3200.0)
        request.with_user(self.manager).action_return_to_review()
        self.assertEqual(former.state, 'cancelled')
        self.assertFalse(request.successor_operation_id)
        self.assertFalse(request.approved_by)
        request.action_refresh_proposal()
        request.with_user(self.manager).action_approve()
        request.with_user(self.manager).action_prepare_successor()
        self.assertNotEqual(request.successor_operation_id, former)
        self.assertAlmostEqual(request.successor_operation_id.financed_amount, 100000.0)
        self.assertEqual(self.operation.state, 'active')

    def test_signed_successor_cannot_be_cancelled_by_review_action(self):
        request = self._request()
        request.action_submit()
        request.action_approve()
        request.action_prepare_successor()
        successor = self._contract_successor(request)
        with self.assertRaisesRegex(ValidationError, 'contratada'):
            request.action_return_to_review()
        self.assertEqual(successor.state, 'contracted')
        self.assertEqual(request.state, 'prepared')
        self.assertEqual(request.successor_operation_id, successor)
