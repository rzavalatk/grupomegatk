from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestODentalReferral(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.env.user.has_group("odental_core.group_odental_manager"):
            cls.env.user.write(
                {"groups_id": [(4, cls.env.ref("odental_core.group_odental_manager").id)]}
            )
        cls.organization = cls.env["odental.organization"].create(
            {
                "name": "Clínica referencias",
                "code": "REF",
                "user_ids": [(4, cls.env.user.id)],
            }
        )
        cls.professional = cls.env["odental.professional"].create(
            {"name": "Dra. Origen", "organization_ids": [(4, cls.organization.id)]}
        )
        cls.patient = cls.env["odental.patient"].create(
            {"name": "Paciente referido", "organization_id": cls.organization.id}
        )
        cls.record = cls.env["odental.clinical.record"].create(
            {"patient_id": cls.patient.id, "alerts": "Alergia a penicilina"}
        )
        cls.history = cls.env["odental.medical.history.entry"].create(
            {
                "clinical_record_id": cls.record.id,
                "category": "allergy",
                "name": "Penicilina",
                "details": "Reacción alérgica confirmada",
                "referral_sharing": "include",
            }
        )
        cls.template = cls.env["odental.consent.template"].create(
            {
                "name": "Referencia a especialista",
                "organization_id": cls.organization.id,
                "purpose": "referral",
                "text": "Autorizo compartir la información mínima descrita en esta referencia.",
            }
        )

    def _new_referral(self):
        return self.env["odental.referral"].create(
            {
                "clinical_record_id": self.record.id,
                "referring_professional_id": self.professional.id,
                "recipient_name": "Dr. Especialista",
                "recipient_email": "especialista@example.com",
                "recipient_license": "COL-001",
                "referral_reason": "Evaluación endodóntica",
                "clinical_question": "Confirmar pronóstico de la pieza afectada.",
                "share_alerts": True,
                "history_entry_ids": [(6, 0, self.history.ids)],
                "consent_template_id": self.template.id,
            }
        )

    def _activate(self, referral):
        referral.action_request_consent()
        referral.consent_id.write(
            {
                "signer_name": self.patient.name,
                "verification_method": "secure_portal",
                "verification_reference": "consent-event-001",
            }
        )
        referral.consent_id.action_sign()
        action = referral.action_activate()
        return self.env["odental.referral.credentials.wizard"].browse(action["res_id"])

    def test_activation_requires_signed_consent(self):
        referral = self._new_referral()
        referral.action_request_consent()
        with self.assertRaises(ValidationError):
            referral.action_activate()

    def test_patient_can_sign_digital_consent_with_otp(self):
        referral = self._new_referral()
        action = referral.action_request_consent()
        wizard = self.env["odental.referral.credentials.wizard"].browse(action["res_id"])
        token = wizard.access_url.rsplit("/", 1)[-1]
        self.assertEqual(wizard.credential_purpose, "patient")
        self.assertEqual(
            self.env["odental.referral"]._find_by_consent_token(token), referral
        )
        success, error = referral._verify_consent_otp(token, wizard.one_time_code)
        self.assertTrue(success)
        self.assertFalse(error)
        referral._portal_sign_consent(
            self.patient.name, "0801-2000-00000", "patient"
        )
        self.assertEqual(referral.consent_id.state, "signed")
        self.assertFalse(referral.consent_access_token_hash)

    def test_hashed_credentials_and_single_use_otp(self):
        referral = self._new_referral()
        wizard = self._activate(referral)
        token = wizard.access_url.rsplit("/", 1)[-1]
        self.assertEqual(referral.state, "active")
        self.assertNotEqual(referral.access_token_hash, token)
        self.assertNotEqual(referral.otp_hash, wizard.one_time_code)
        success, error = referral._verify_otp(token, wizard.one_time_code)
        self.assertTrue(success)
        self.assertFalse(error)
        self.assertFalse(referral.otp_hash)
        success, error = referral._verify_otp(token, wizard.one_time_code)
        self.assertFalse(success)
        self.assertTrue(error)

    def test_restricted_data_requires_justification(self):
        restricted = self.env["odental.medical.history.entry"].create(
            {
                "clinical_record_id": self.record.id,
                "category": "mental_health",
                "name": "Información restringida",
                "sensitivity": "restricted",
                "referral_sharing": "review",
            }
        )
        with self.env.cr.savepoint(), self.assertRaises(ValidationError):
            self.env["odental.referral"].create(
                {
                    "clinical_record_id": self.record.id,
                    "referring_professional_id": self.professional.id,
                    "recipient_name": "Dr. Especialista",
                    "recipient_email": "especialista@example.com",
                    "referral_reason": "Segunda opinión",
                    "history_entry_ids": [(6, 0, restricted.ids)],
                    "consent_template_id": self.template.id,
                }
            )

    def test_external_report_is_separate_and_immutable(self):
        referral = self._new_referral()
        wizard = self._activate(referral)
        token = wizard.access_url.rsplit("/", 1)[-1]
        self.assertEqual(
            self.env["odental.referral"]._find_by_token(token), referral
        )
        report = self.env["odental.referral.report"].sudo().create(
            {
                "referral_id": referral.id,
                "author_name": referral.recipient_name,
                "summary": "Se recomienda tratamiento endodóntico.",
            }
        )
        self.assertEqual(referral.state, "report_submitted")
        self.assertEqual(report.state, "submitted")
        self.assertTrue(report.content_hash)
        self.assertFalse(self.env["odental.referral"]._find_by_token(token))
        with self.assertRaises(UserError):
            report.write({"summary": "Alteración posterior"})
        report.action_mark_reviewed()
        self.assertEqual(report.state, "reviewed")

    def test_scope_is_frozen_after_consent_request(self):
        referral = self._new_referral()
        referral.action_request_consent()
        with self.assertRaises(UserError):
            referral.write({"referral_reason": "Cambio posterior no autorizado"})

    def test_expiration_revokes_token(self):
        referral = self._new_referral()
        self._activate(referral)
        referral.with_context(allow_referral_transition=True).write(
            {"expires_at": fields.Datetime.now() - timedelta(minutes=1)}
        )
        referral._expire_access()
        self.assertEqual(referral.state, "expired")
        self.assertFalse(referral.access_token_hash)

    def test_clinical_change_invalidates_active_capsule(self):
        referral = self._new_referral()
        self._activate(referral)
        self.history.details = "El antecedente clínico cambió"
        referral._expire_access()
        self.assertEqual(referral.state, "invalidated")
        self.assertFalse(referral.access_token_hash)
