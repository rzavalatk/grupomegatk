from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


class TestODentalClinical(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.organization = cls.env["odental.organization"].create(
            {"name": "Clínica prueba", "code": "CLIN", "user_ids": [(4, cls.env.user.id)]}
        )
        cls.professional = cls.env["odental.professional"].create(
            {"name": "Dra. Clínica", "organization_ids": [(4, cls.organization.id)]}
        )
        cls.patient = cls.env["odental.patient"].create(
            {"name": "Paciente clínico", "organization_id": cls.organization.id}
        )
        cls.record = cls.env["odental.clinical.record"].create(
            {"patient_id": cls.patient.id}
        )

    def test_one_record_per_patient(self):
        # A duplicate must fail; its expected SQL error must not mark the
        # entire Odoo.sh build as failed. Roll back before checking the result.
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.env["odental.clinical.record"].create({"patient_id": self.patient.id})
        self.assertEqual(self.env["odental.clinical.record"].search_count([
            ("patient_id", "=", self.patient.id)
        ]), 1)

    def test_signed_encounter_is_immutable(self):
        encounter = self.env["odental.clinical.encounter"].create(
            {
                "clinical_record_id": self.record.id,
                "professional_id": self.professional.id,
                "chief_complaint": "Dolor dental",
                "diagnosis_summary": "Pulpitis irreversible",
            }
        )
        encounter.action_sign()
        self.assertEqual(encounter.state, "signed")
        self.assertTrue(encounter.content_hash)
        with self.assertRaises(UserError):
            encounter.write({"diagnosis_summary": "Contenido alterado"})

    def test_amendment_preserves_original(self):
        encounter = self.env["odental.clinical.encounter"].create(
            {
                "clinical_record_id": self.record.id,
                "professional_id": self.professional.id,
                "clinical_findings": "Hallazgo inicial",
            }
        )
        encounter.action_sign()
        action = encounter.action_create_amendment()
        amendment = self.env["odental.clinical.encounter"].browse(action["res_id"])
        self.assertEqual(encounter.state, "amended")
        self.assertEqual(amendment.state, "draft")
        self.assertEqual(amendment.version, 2)
        self.assertEqual(amendment.previous_version_id, encounter)
        amendment.amendment_reason = "Aclaración del diagnóstico"
        amendment.action_sign()
        self.assertEqual(amendment.state, "signed")

    def test_consent_snapshot_and_signature(self):
        template = self.env["odental.consent.template"].create(
            {
                "name": "Tratamiento general",
                "organization_id": self.organization.id,
                "purpose": "treatment",
                "version": 1,
                "text": "Autorizo el tratamiento indicado.",
            }
        )
        consent = self.env["odental.patient.consent"].create(
            {
                "clinical_record_id": self.record.id,
                "professional_id": self.professional.id,
                "template_id": template.id,
                "signer_name": "Paciente clínico",
                "verification_method": "secure_portal",
                "verification_reference": "event-001",
            }
        )
        self.assertEqual(consent.template_version, 1)
        self.assertEqual(consent.consent_text, template.text)
        consent.action_sign()
        self.assertEqual(consent.state, "signed")
        self.assertTrue(consent.content_hash)
        with self.assertRaises(UserError):
            consent.write({"scope_summary": "Alteración posterior"})

    def test_consent_requires_evidence(self):
        template = self.env["odental.consent.template"].create(
            {
                "name": "Imágenes",
                "organization_id": self.organization.id,
                "purpose": "images",
                "text": "Autorizo las imágenes clínicas.",
            }
        )
        consent = self.env["odental.patient.consent"].create(
            {
                "clinical_record_id": self.record.id,
                "template_id": template.id,
                "signer_name": "Paciente clínico",
                "verification_method": "secure_portal",
            }
        )
        with self.assertRaises(ValidationError):
            consent.action_sign()


@tagged("post_install", "-at_install")
class TestODentalPatientFlow(TransactionCase):
    @classmethod
    def _test_company(cls, name):
        values = {'name': name}
        if 'autopost_bills' in cls.env['res.partner']._fields:
            values['autopost_bills'] = 'never'
        partner = cls.env['res.partner'].create(values)
        # Grupo Mega assigns every new contact to the current company.
        # A company address must be shared before creating its warehouse.
        partner.write({'company_id': False})
        return cls.env['res.company'].create({'name': name, 'partner_id': partner.id})

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls._test_company('Dental flow test')
        values = {
            'name': 'Dental flow professional',
            'login': 'odental-flow-professional',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, cls.company.ids)],
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('odental_core.group_odental_professional').id])],
        }
        if 'autopost_bills' in cls.env['res.users']._fields:
            values['autopost_bills'] = 'never'
        cls.operator = cls.env['res.users'].with_context(no_reset_password=True).create(values)
        cls.organization = cls.env['odental.organization'].create({
            'name': 'Authorized dental organization', 'code': 'FLOW-A',
            'company_id': cls.company.id, 'user_ids': [(4, cls.operator.id)],
        })
        cls.hidden = cls.env['odental.organization'].create({
            'name': 'Other dental organization', 'code': 'FLOW-B',
            'company_id': cls.company.id,
        })
        cls.patients = cls.env['odental.patient'].with_user(cls.operator).with_company(cls.company)
        cls.patient = cls.patients.create({'name': 'Flow patient', 'organization_id': cls.organization.id})

    def test_default_uses_only_authorized_organization(self):
        self.assertEqual(self.patients.default_get(['organization_id'])['organization_id'], self.organization.id)

    def test_ambiguous_organization_is_not_chosen(self):
        self.hidden.write({'user_ids': [(4, self.operator.id)]})
        self.assertFalse(self.patients.default_get(['organization_id']).get('organization_id'))

    def test_context_choice_is_preserved(self):
        self.assertFalse(self.patients.with_context(default_organization_id=False).default_get(['organization_id'])['organization_id'])
        self.assertEqual(self.patients.with_context(default_organization_id=self.organization.id).default_get(['organization_id'])['organization_id'], self.organization.id)

    def test_no_default_from_another_company(self):
        other_company = self._test_company('Empty dental company')
        self.operator.write({'company_ids': [(4, other_company.id)]})
        self.assertFalse(self.patients.with_company(other_company).default_get(['organization_id']).get('organization_id'))

    def test_open_new_record_does_not_save_it(self):
        action = self.patient.action_open_clinical_record()
        self.assertFalse(action['res_id'])
        self.assertEqual(action['context']['default_patient_id'], self.patient.id)
        self.assertFalse(self.env['odental.clinical.record'].search_count([('patient_id', '=', self.patient.id)]))

    def test_open_reuses_closed_record(self):
        record = self.env['odental.clinical.record'].create({'patient_id': self.patient.id})
        record.action_close()
        action = self.patient.action_open_clinical_record()
        self.assertEqual(action['res_id'], record.id)
        self.assertEqual(record.state, 'closed')
        self.assertEqual(self.env['odental.clinical.record'].search_count([('patient_id', '=', self.patient.id)]), 1)

    def test_other_organization_patient_is_denied(self):
        from odoo.exceptions import AccessError
        hidden_patient = self.env['odental.patient'].create({'name': 'Other flow patient', 'organization_id': self.hidden.id})
        with self.assertRaises(AccessError):
            hidden_patient.with_user(self.operator).action_open_clinical_record()

    def test_reception_role_cannot_open_clinical_record(self):
        from odoo.exceptions import AccessError
        self.operator.write({'groups_id': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('odental_core.group_odental_user').id])]})
        with self.assertRaises(AccessError):
            self.patient.action_open_clinical_record()
