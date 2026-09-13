from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


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
        with self.env.cr.savepoint(), self.assertRaises(Exception):
            self.env["odental.clinical.record"].create({"patient_id": self.patient.id})

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
