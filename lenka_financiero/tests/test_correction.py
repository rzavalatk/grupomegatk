from odoo.exceptions import AccessError, ValidationError
from .test_sole_signature_approval import TestExclusiveSoleSignatureApproval
from .test_secured_loan import TestSecuredLoanContract


class TestCorrectionSecurity(TestExclusiveSoleSignatureApproval):
    def _approved(self):
        op = self._pending().with_user(self.luis)
        op.action_approve()
        return op

    def test_correction_preserves_audit_and_requires_new_request(self):
        op = self._approved()
        old_date = op.approval_date
        op._return_for_correction('Corregir respaldo')
        self.assertEqual(op.state, 'review')
        self.assertEqual(op.revision_count, 1)
        self.assertFalse(op.approval_date)
        self.assertIn(str(old_date), str(op.message_ids[0].body))
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.action_generate_contract_documents()
        with self.assertRaises(AccessError), self.cr.savepoint():
            op.write({'state': 'approved', 'approval_date': old_date})
        op.with_user(self.elisa).action_request_sole_signature()
        op.action_approve()
        self.assertEqual(op.state, 'approved')
        self.assertEqual(op.approved_by, self.luis)

    def test_other_authorizer_and_blank_reason_denied(self):
        op = self._approved()
        with self.assertRaises(AccessError), self.cr.savepoint():
            op.with_user(self.other)._return_for_correction('Cambio')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op._return_for_correction('   ')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.write({'state': 'draft'})

    def test_signed_and_disbursed_not_returnable(self):
        op = self._approved()
        op.contract_signed = True
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op._return_for_correction('Cambio')
        op.contract_signed = False
        self.env['lenka.disbursement'].create({'operation_id': op.id, 'amount': 1})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op._return_for_correction('Cambio')


class TestRepresentativeIdentity(TestSecuredLoanContract):
    def test_same_contact_uses_entered_identity_without_using_rtn(self):
        self.person.lenka_identity_number = False
        op = self.operation(contract_buyer_identity='IDENTIDAD-EXPLICITA', guarantor_ids=[(6, 0, self.person.ids)])
        self.assertIn('IDENTIDAD-EXPLICITA', op._render_lenka_template(self.template))
        self.assertFalse(self.person.lenka_identity_number)
        op.action_add_representative_as_guarantor()
        self.assertEqual(self.person.lenka_identity_number, 'IDENTIDAD-EXPLICITA')

    def test_conflicting_identity_is_rejected(self):
        op = self.operation(contract_buyer_identity='OTRA-IDENTIDAD', guarantor_ids=[(6, 0, self.person.ids)])
        with self.assertRaisesRegex(ValidationError, 'no coincide'):
            op._render_lenka_template(self.template)

    def test_company_contacts_cannot_cross_operations(self):
        company = self.env['res.company'].create({'name': 'Empresa separada de prueba'})
        self.person.company_id = company
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.operation(guarantor_ids=[(6, 0, self.person.ids)])
