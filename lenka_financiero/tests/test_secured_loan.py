from datetime import date

from lxml import html

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSecuredLoanContract(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Partner = cls.env['res.partner'].with_context(no_vat_validation=True)
        cls.entity = Partner.create({'name': 'Entidad ficticia', 'is_company': True, 'vat': 'RTN-PRUEBA'})
        cls.person = Partner.create({'name': 'Representante ficticio', 'vat': 'RTN-PERSONA', 'lenka_identity_number': 'ID-PRUEBA'})
        cls.other = Partner.create({'name': 'Otro aval ficticio', 'vat': 'RTN-OTRO', 'lenka_identity_number': 'OTRO-ID'})
        cls.template = cls.env['lenka.contract.template']._approved_secured_loan_template(cls.env.company)

    def operation(self, **values):
        op = self.env['lenka.financial.operation'].create({
            'partner_id': self.entity.id, 'operation_type': 'loan', 'is_quote': False,
            'principal_amount': 10000, 'interest_rate': 3, 'term_months': 18,
            'calculation_method': 'interest_then_level', 'interest_only_months': 6,
            'first_payment_date': date(2026, 11, 1), 'late_fee_rate': 1.5,
            'late_fee_method': 'balance_monthly', 'security_mode': 'backed',
            'contract_buyer_partner_id': self.person.id,
            'contract_buyer_authority': 'Poder ficticio de pruebas',
            'contract_seller_representative': 'Representante Lenka ficticio',
            'contract_seller_identity': 'LENKA-ID-PRUEBA',
            'contract_payment_instructions': 'Pagos según cuenta ficticia de pruebas.',
            **values,
        })
        op.action_generate_schedule()
        return op

    def test_representative_is_not_automatically_guarantor(self):
        op = self.operation()
        self.assertFalse(op.guarantor_ids)
        with self.assertRaisesRegex(ValidationError, 'al menos un Aval'):
            op._render_lenka_template(self.template)
        op.action_add_representative_as_guarantor()
        self.assertEqual(op.guarantor_ids, self.person)
        op.action_add_representative_as_guarantor()
        self.assertEqual(len(op.guarantor_ids), 1)

    def test_representative_identity_is_independent_from_fiscal_rtn(self):
        op = self.operation()
        op._onchange_contract_buyer_partner()
        self.assertEqual(op.contract_buyer_identity, self.person.lenka_identity_number)
        self.assertNotEqual(op.contract_buyer_identity, self.person.vat)

    def test_rtn_alone_does_not_satisfy_guarantor_identity(self):
        self.other.lenka_identity_number = False
        op = self.operation(guarantor_ids=[(6, 0, self.other.ids)])
        with self.assertRaisesRegex(ValidationError, 'identidad del aval'):
            op._render_lenka_template(self.template)

    def test_same_person_has_separate_capacity_and_signature(self):
        op = self.operation(guarantor_ids=[(6, 0, self.person.ids)])
        body = op._render_lenka_template(self.template)
        doc = html.fromstring(body)
        signatures = doc.xpath('//div[contains(@class,"lenka-firmas")]')
        self.assertEqual(len(signatures), 2)
        self.assertIn('REPRESENTANTE LEGAL DE Entidad ficticia', signatures[0].text_content())
        self.assertIn('AVAL SOLIDARIO - a título personal', signatures[1].text_content())
        self.assertIn(self.person.name, signatures[0].text_content())
        self.assertIn(self.person.name, signatures[1].text_content())
        self.assertIn('1.5 % mensual', body)
        self.assertIn('6 meses de solo intereses y 12 meses de cuota nivelada', body)
        self.assertIn('Anexo 1: plan de pagos', body)
        self.assertNotIn('{{', body)

    def test_third_person_and_multiple_guarantors_have_individual_signatures(self):
        op = self.operation(guarantor_ids=[(6, 0, (self.person | self.other).ids)])
        body = op._render_lenka_template(self.template)
        self.assertEqual(body.count('AVAL SOLIDARIO - a título personal'), 2)
        self.assertIn(self.other.lenka_identity_number, body)
        self.assertNotIn(self.other.vat, body)
        self.assertIn(self.other.name, body)

    def test_guarantee_only_does_not_make_owner_or_representative_guarantor(self):
        op = self.operation(guarantee_ids=[(0, 0, {
            'guarantee_type': 'vehicle', 'owner_id': self.other.id,
            'description': 'Vehículo ficticio', 'serial_reference': 'VIN-PRUEBA',
            'declared_value': 14000, 'appraisal_value': 12000,
        })])
        body = op._render_lenka_template(self.template)
        self.assertIn('VIN-PRUEBA', body)
        self.assertIn('14,000.00', body)
        self.assertIn('12,000.00', body)
        self.assertIn('No se ha pactado aval personal', body)
        self.assertNotIn('AVAL SOLIDARIO - a título personal', body)

    def test_personal_debtor_with_guarantor(self):
        op = self.operation(partner_id=self.person.id, contract_buyer_partner_id=False,
                            guarantor_ids=[(6, 0, self.other.ids)])
        body = op._render_lenka_template(self.template)
        self.assertIn('PRESTATARIO - en nombre propio', body)
        self.assertNotIn('REPRESENTANTE LEGAL DE', body)

    def test_missing_signer_and_guarantor_identity_report_specific_fields(self):
        missing = self.env['res.partner'].create({'name': 'Aval sin identidad'})
        op = self.operation(contract_buyer_partner_id=False, guarantor_ids=[(6, 0, missing.ids)])
        with self.assertRaisesRegex(ValidationError, 'nombre del representante'):
            op._render_lenka_template(self.template)
        op.contract_buyer_partner_id = self.person
        with self.assertRaisesRegex(ValidationError, 'identidad del aval Aval sin identidad'):
            op._render_lenka_template(self.template)

    def test_released_guarantee_is_not_sufficient_backing(self):
        op = self.operation(guarantee_ids=[(0, 0, {
            'guarantee_type': 'other', 'owner_id': self.other.id,
            'description': 'Respaldo liberado', 'state': 'released',
        })])
        with self.assertRaisesRegex(ValidationError, 'al menos un Aval'):
            op._render_lenka_template(self.template)

    def test_html_and_template_tokens_in_names_are_never_executed(self):
        self.other.name = '<img src=x onerror=alert(1)> {{MONTO}}'
        op = self.operation(guarantor_ids=[(6, 0, self.other.ids)])
        body = op._render_lenka_template(self.template)
        self.assertIn('&lt;img', body)
        self.assertNotIn('<img src=x', body)
        self.assertIn('{{MONTO}}', body)

    def test_generation_selects_only_matching_loan_template_and_is_idempotent(self):
        op = self.operation(guarantor_ids=[(6, 0, self.person.ids)])
        self.env['lenka.contract.template']._approved_unsecured_loan_template(op.company_id)
        op.action_generate_contract_documents()
        op.action_generate_contract_documents()
        self.assertEqual(op.generated_document_ids.filtered(lambda d: d.document_type == 'contract').template_id, self.template)
        self.assertEqual(len(op.generated_document_ids.filtered(lambda d: d.document_type == 'contract')), 1)
        with self.assertRaises(ValidationError):
            self.operation(security_mode='sole_signature')._render_lenka_template(self.template)

    def test_signed_document_cannot_be_regenerated(self):
        op = self.operation(guarantor_ids=[(6, 0, self.person.ids)])
        doc = self.env['lenka.generated.document'].create({
            'name': 'Contrato ficticio', 'operation_id': op.id, 'template_id': self.template.id,
        })
        doc.action_render()
        doc.state = 'signed'
        with self.assertRaises(ValidationError):
            doc.action_render()

    def test_company_and_legacy_mora_mismatches_rejected(self):
        op = self.operation(guarantor_ids=[(6, 0, self.person.ids)], late_fee_method='legacy')
        with self.assertRaisesRegex(ValidationError, 'Base de mora'):
            op._render_lenka_template(self.template)
        other_company = self.env['res.company'].create({'name': 'Prestamista ficticio separado'})
        other_template = self.env['lenka.contract.template']._approved_secured_loan_template(other_company)
        with self.assertRaisesRegex(ValidationError, 'misma empresa'):
            op._render_lenka_template(other_template)
