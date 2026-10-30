from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestExclusiveSoleSignatureApproval(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.email = 'lenka-test@example.invalid'
        cls.client = cls.env['res.partner'].create({'name': 'Cliente prueba autorizacion exclusiva'})
        users = cls.env['res.users'].with_context(no_reset_password=True, tracking_disable=True)
        def user(name, login, group):
            return users.create({
                'name': name, 'login': login, 'email': login + '@example.invalid',
                'company_id': cls.company.id, 'company_ids': [(6, 0, cls.company.ids)],
                'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref(group).id])],
            })
        cls.elisa = user('Elisa Rodriguez - prueba', 'lenka_elisa', 'lenka_financiero.group_lenka_manager')
        cls.luis = user('Luis Moran - prueba', 'lenka_luis', 'lenka_financiero.group_lenka_sole_authorizer')
        cls.other = user('Otro autorizador - prueba', 'lenka_other', 'lenka_financiero.group_lenka_sole_authorizer')
        cls.company.write({
            'lenka_sole_signature_requester_id': cls.elisa.id,
            'lenka_sole_signature_approver_id': cls.luis.id,
        })

    def _request(self):
        return self.env['lenka.financial.operation'].with_user(self.elisa).create({
            'partner_id': self.client.id, 'security_mode': 'sole_signature', 'is_quote': False,
            'state': 'review', 'principal_amount': 100000, 'interest_rate': 3,
            'rate_period': 'monthly', 'term_months': 12, 'calculation_method': 'level',
            'approval_notes': 'Cliente de confianza; solicita autorizacion sin respaldo',
        })

    def _pending(self):
        op = self._request()
        op.action_request_sole_signature()
        return op

    def test_three_requests_have_three_activities_and_mail_before_approval(self):
        operations = self._request() | self._request() | self._request()
        operations.action_request_sole_signature()
        self.assertEqual(len(operations.mapped('sole_signature_activity_id')), 3)
        self.assertEqual(len(operations.mapped('sole_signature_notification_id')), 3)
        for op in operations:
            self.assertEqual(op.state, 'review')
            self.assertEqual(op.sole_signature_status, 'pending')
            self.assertFalse(op.approved_by)
            self.assertFalse(op.approval_date)
            self.assertEqual(op.sole_signature_authorizer_id, self.luis)
            self.assertEqual(op.sole_signature_activity_id.sudo().user_id, self.luis)
            self.assertEqual(op.sole_signature_notification_id.sudo().email_to, self.luis.email)
            self.assertEqual(op.sole_signature_notification_id.sudo().state, 'outgoing')
            self.assertIn('pendiente', op.sole_signature_notification_id.sudo().subject)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            operations.action_request_sole_signature()
        self.assertEqual(len(operations.mapped('sole_signature_activity_id')), 3)

    def test_elisa_even_as_manager_cannot_authorize_or_forge_state(self):
        op = self._pending()
        with self.assertRaises(AccessError), self.cr.savepoint():
            op.action_approve()
        with self.assertRaises(AccessError), self.cr.savepoint():
            op.write({'state': 'approved'})
        with self.assertRaises(AccessError), self.cr.savepoint():
            op.write({'sole_signature_status': 'approved'})
        with self.assertRaises(AccessError), self.cr.savepoint():
            op.action_reject_sole_signature()
        self.assertEqual(op.state, 'review')

    def test_other_with_same_special_group_cannot_decide(self):
        op = self._pending().with_user(self.other)
        with self.assertRaises(AccessError), self.cr.savepoint():
            op.action_approve()
        with self.assertRaises(AccessError), self.cr.savepoint():
            op.write({'sole_signature_decision_notes': 'Intento no autorizado'})

    def test_only_luis_can_approve_and_activity_is_completed(self):
        op = self._pending().with_user(self.luis)
        activity = op.sole_signature_activity_id
        self.assertTrue(op.can_decide_sole_signature)
        self.assertFalse(op.env.user.has_group('lenka_financiero.group_lenka_manager'))
        op.action_approve()
        self.assertEqual(op.state, 'approved')
        self.assertEqual(op.sole_signature_status, 'approved')
        self.assertEqual(op.approved_by, self.luis)
        self.assertTrue(op.approval_date)
        self.assertTrue(op.sole_signature_decided_at)
        self.assertFalse(activity.exists())
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.action_approve()

    def test_rejection_and_resubmission_keep_history_and_require_new_decision(self):
        op = self._pending()
        as_luis = op.with_user(self.luis)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            as_luis.action_reject_sole_signature()
        as_luis.sole_signature_decision_notes = 'Se necesita revisar las condiciones'
        as_luis.action_reject_sole_signature()
        self.assertEqual(op.state, 'rejected')
        self.assertEqual(op.sole_signature_status, 'rejected')
        self.assertFalse(op.approved_by)
        op.principal_amount = 80000
        op.action_request_sole_signature()
        self.assertEqual(op.state, 'review')
        self.assertEqual(op.sole_signature_status, 'pending')
        self.assertFalse(op.sole_signature_decision_notes)
        self.assertEqual(op.schedule_line_ids[0].opening_balance, 80000)

    def test_pending_terms_and_schedule_are_frozen(self):
        op = self._pending()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.principal_amount = 200000
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.security_mode = 'backed'
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.action_generate_schedule()
        with self.assertRaises(AccessError), self.cr.savepoint():
            op.write({'state': 'contracted'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.action_mark_contracted()
        self.assertEqual(op.state, 'review')

    def test_missing_configuration_or_sender_prevents_sending(self):
        op = self._request()
        self.company.lenka_sole_signature_approver_id = False
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.action_request_sole_signature()
        self.assertEqual(op.sole_signature_status, 'none')
        self.company.lenka_sole_signature_approver_id = self.luis
        self.company.email = False
        self.elisa.email = False
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.action_request_sole_signature()
        self.assertEqual(op.sole_signature_status, 'none')

    def test_operator_cannot_change_authorizer_configuration(self):
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.company.with_user(self.elisa).write({'lenka_sole_signature_approver_id': self.other.id})

    def test_import_defaults_cannot_create_approved_or_pending_requests(self):
        for context in ({'default_security_mode': 'sole_signature', 'default_state': 'approved'},
                        {'default_security_mode': 'sole_signature', 'default_sole_signature_status': 'pending'}):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self.env['lenka.financial.operation'].with_context(**context).create({
                    'partner_id': self.client.id, 'principal_amount': 1000, 'interest_rate': 3,
                })

    def test_backed_operation_still_requires_guarantor_or_guarantee(self):
        op = self._request()
        op.security_mode = 'backed'
        op.action_generate_schedule()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.action_approve()

    def test_distinct_active_company_users_required(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.company.lenka_sole_signature_approver_id = self.elisa

    def test_legacy_unbacked_approval_is_returned_to_exclusive_authorization(self):
        op = self.env['lenka.financial.operation'].with_user(self.elisa).create({
            'partner_id': self.client.id, 'security_mode': 'backed', 'is_quote': False,
            'state': 'approved', 'principal_amount': 10000, 'interest_rate': 3,
            'term_months': 12, 'approval_notes': 'Reenviar prestamo sin respaldo a Luis',
        })
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.action_mark_contracted()
        op.action_request_legacy_sole_signature()
        self.assertEqual(op.state, 'review')
        self.assertEqual(op.security_mode, 'sole_signature')
        self.assertEqual(op.sole_signature_status, 'pending')
        self.assertFalse(op.approved_by)
        self.assertEqual(op.sole_signature_activity_id.sudo().user_id, self.luis)
        op.with_user(self.luis).action_approve()
        self.assertEqual(op.approved_by, self.luis)

    def test_mora_is_in_request_and_locked_while_pending(self):
        op=self._request()
        op.write({'late_fee_rate':1.25,'late_fee_method':'balance_monthly','grace_days':3})
        op.action_request_sole_signature()
        body=op.sole_signature_notification_id.sudo().body_html
        self.assertIn('1.25%',body)
        self.assertIn('Días de gracia',body)
        for values in ({'late_fee_rate':2},{'late_fee_method':'legacy'},{'grace_days':0}):
            with self.assertRaises(ValidationError),self.cr.savepoint():op.write(values)
        self.assertEqual(op.late_fee_rate,1.25)
