from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestMixedPlan(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = cls.env['res.partner'].create({'name': 'Cliente pruebas plan mixto'})
        cls.aval = cls.env['res.partner'].create({'name': 'Aval pruebas plan mixto'})

    def _quote(self, **extra):
        vals = dict(partner_id=self.client.id, principal_amount=100000,
                    interest_rate=3, rate_period='monthly', term_months=18,
                    calculation_method='interest_then_level', interest_only_months=6,
                    first_payment_date='2027-01-31', is_quote=True)
        vals.update(extra)
        return self.env['lenka.financial.operation'].create(vals)

    def test_six_interest_twelve_level_and_quote_conversion(self):
        op = self._quote()
        op.action_generate_schedule()
        lines = op.schedule_line_ids.sorted('sequence')
        self.assertEqual(len(lines), 18)
        self.assertEqual(lines[:6].mapped('capital'), [0.0] * 6)
        self.assertEqual(lines[:6].mapped('payment'), [3000.0] * 6)
        expected = 100000 * .03 / (1 - 1.03 ** -12)
        for line in lines[6:-1]:
            self.assertAlmostEqual(line.payment, expected, delta=.02)
        self.assertAlmostEqual(sum(lines.mapped('capital')), 100000, places=2)
        self.assertEqual(lines[-1].closing_balance, 0)
        self.assertEqual(op.level_payment_months, 12)
        self.assertEqual(op.level_payment_start_date, fields.Date.to_date('2027-07-31'))
        self.assertEqual(lines[6].date, op.level_payment_start_date)
        op.action_convert_to_application()
        self.assertFalse(op.is_quote)
        self.assertEqual(op.interest_only_months, 6)
        self.assertEqual(op.calculation_method, 'interest_then_level')

    def test_zero_rate_and_phase_boundaries(self):
        for months in (1, 6, 17):
            op = self._quote(interest_rate=0, interest_only_months=months)
            op.action_generate_schedule()
            lines = op.schedule_line_ids.sorted('sequence')
            self.assertEqual(len(lines), 18)
            self.assertEqual(lines[:months].mapped('payment'), [0.0] * months)
            self.assertAlmostEqual(sum(lines.mapped('capital')), 100000, places=2)
            self.assertEqual(lines[-1].closing_balance, 0)

    def test_annual_rate_and_financed_amount_after_down_payment(self):
        op = self._quote(principal_amount=120000, down_payment=20000,
                         interest_rate=36, rate_period='annual', operation_type='financing')
        op.action_generate_schedule()
        self.assertEqual(op.financed_amount, 100000)
        self.assertEqual(op.schedule_line_ids.sorted('sequence')[:6].mapped('interest'), [3000.0] * 6)
        self.assertEqual(op.schedule_line_ids.sorted('sequence')[-1].closing_balance, 0)

    def test_invalid_phase_lengths(self):
        for months in (-1, 0, 18, 19):
            with self.subTest(months=months), self.assertRaises(ValidationError), self.cr.savepoint():
                self._quote(interest_only_months=months)

    def test_transition_without_explicit_first_payment(self):
        op = self._quote(date='2027-01-15', first_payment_date=False)
        self.assertEqual(op.level_payment_start_date, fields.Date.to_date('2027-08-15'))
        op.action_generate_schedule()
        self.assertEqual(op.schedule_line_ids.sorted('sequence')[6].date, op.level_payment_start_date)

    def test_contract_tokens_and_quote_report(self):
        op = self._quote()
        op.action_generate_schedule()
        tokens = op._template_values()
        self.assertEqual(tokens['{{MESES_SOLO_INTERESES}}'], '6')
        self.assertEqual(tokens['{{MESES_CUOTA_NIVELADA}}'], '12')
        self.assertEqual(tokens['{{INICIO_CUOTA_NIVELADA}}'], '2027-07-31')
        html, _ = self.env['ir.actions.report']._render_qweb_html(
            'lenka_financiero.action_report_lenka_quote', [op.id])
        self.assertIn(b'Solo intereses', html)
        self.assertIn(b'Cuota nivelada', html)

    def test_approved_mixed_terms_cannot_change(self):
        op = self._quote(is_quote=False, state='review', guarantor_ids=[(4, self.aval.id)])
        op.action_generate_schedule()
        op.action_approve()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.interest_only_months = 3

    def test_restructuring_preserves_phases(self):
        op = self._quote(is_quote=False, state='review', guarantor_ids=[(4, self.aval.id)])
        op.action_generate_schedule()
        op.state = 'active'
        change = self.env['lenka.restructuring'].create({
            'operation_id': op.id, 'reason': 'Mantener fases del plan',
            'settlement_method': 'capitalize',
        })
        self.assertEqual(change.proposed_interest_only_months, 6)
        change.action_submit()
        change.action_approve()
        change.action_prepare_successor()
        successor = change.successor_operation_id
        self.assertEqual(successor.interest_only_months, 6)
        self.assertEqual(successor.calculation_method, 'interest_then_level')
        self.assertEqual(successor.level_payment_months, 12)

    def test_exclusive_approval_freezes_mixed_plan(self):
        company = self.env.company
        company.email = 'lenka-test@example.invalid'
        users = self.env['res.users'].with_context(no_reset_password=True, tracking_disable=True)
        def user(name, group):
            return users.create({'name': name, 'login': name, 'email': name + '@example.invalid',
                                 'company_id': company.id, 'company_ids': [(6, 0, company.ids)],
                                 'groups_id': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref(group).id])]})
        elisa = user('mixed_elisa', 'lenka_financiero.group_lenka_user')
        luis = user('mixed_luis', 'lenka_financiero.group_lenka_sole_authorizer')
        company.write({'lenka_sole_signature_requester_id': elisa.id,
                       'lenka_sole_signature_approver_id': luis.id})
        op = self._quote(is_quote=False, state='review', security_mode='sole_signature',
                         approval_notes='Solicito autorizacion con fases de pago').with_user(elisa)
        op.action_request_sole_signature()
        self.assertEqual(op.sole_signature_status, 'pending')
        self.assertEqual(op.schedule_line_ids.sorted('sequence')[:6].mapped('capital'), [0.0] * 6)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.interest_only_months = 3
        op.with_user(luis).action_approve()
        self.assertEqual(op.approved_by, luis)
