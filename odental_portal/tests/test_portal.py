from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase


class TestODentalPatientPortal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.env.user.has_group("odental_core.group_odental_manager"):
            cls.env.user.write(
                {"groups_id": [(4, cls.env.ref("odental_core.group_odental_manager").id)]}
            )
        cls.organization = cls.env["odental.organization"].create(
            {
                "name": "Clínica portal",
                "code": "PORTAL",
                "user_ids": [(4, cls.env.user.id)],
            }
        )
        cls.patient = cls.env["odental.patient"].create(
            {
                "name": "Paciente portal",
                "organization_id": cls.organization.id,
                "mobile": "+50499990000",
                "email": "paciente@example.com",
            }
        )
        cls.record = cls.env["odental.clinical.record"].create(
            {"patient_id": cls.patient.id}
        )

    def _new_invitation(self):
        return self.env["odental.patient.portal.invitation"].create(
            {
                "patient_id": self.patient.id,
                "delivery_channel": "whatsapp",
                "recipient": self.patient.mobile,
            }
        )

    def _new_update(self):
        return self.env["odental.patient.update.request"].with_context(
            odental_portal_submission=True
        ).create(
            {
                "patient_id": self.patient.id,
                "requested_name": "Paciente actualizado",
                "requested_mobile": "+50488880000",
                "requested_email": "actualizado@example.com",
            }
        )

    def _new_intake(self):
        return self.env["odental.patient.intake"].with_context(
            odental_portal_submission=True
        ).create(
            {
                "patient_id": self.patient.id,
                "clinical_record_id": self.record.id,
                "allergies": "Penicilina",
                "medications": "Ninguno",
                "truth_confirmed": True,
            }
        )

    def test_invitation_uses_hashed_single_use_credentials(self):
        invitation = self._new_invitation()
        action = invitation.action_prepare_access()
        wizard = self.env["odental.patient.portal.credentials"].browse(action["res_id"])
        token = wizard.access_url.rsplit("/", 1)[-1]
        self.assertEqual(invitation.state, "active")
        self.assertNotEqual(invitation.token_hash, token)
        self.assertNotEqual(invitation.otp_hash, wizard.otp)
        self.assertEqual(
            self.env["odental.patient.portal.invitation"]._find_by_token(token),
            invitation,
        )
        success, error = invitation._verify_otp("000000")
        self.assertFalse(success)
        self.assertTrue(error)
        success, error = invitation._verify_otp(wizard.otp)
        self.assertTrue(success)
        self.assertFalse(error)
        invitation._mark_used("127.0.0.1")
        self.assertEqual(invitation.state, "used")
        self.assertFalse(invitation.token_hash)
        self.assertFalse(invitation.otp_hash)

    def test_expired_invitation_revokes_credentials(self):
        invitation = self._new_invitation()
        action = invitation.action_prepare_access()
        wizard = self.env["odental.patient.portal.credentials"].browse(action["res_id"])
        token = wizard.access_url.rsplit("/", 1)[-1]
        invitation.with_context(allow_portal_invitation_transition=True).write(
            {"expires_at": fields.Datetime.now() - timedelta(minutes=1)}
        )
        self.assertFalse(
            self.env["odental.patient.portal.invitation"]._find_by_token(token)
        )
        self.assertEqual(invitation.state, "expired")
        self.assertFalse(invitation.token_hash)

    def test_patient_update_requires_review_before_applying(self):
        update = self._new_update()
        self.assertEqual(self.patient.name, "Paciente portal")
        self.assertTrue(update.previous_values_json)
        update.action_approve()
        self.assertEqual(update.state, "approved")
        self.assertEqual(self.patient.name, "Paciente actualizado")
        self.assertEqual(self.patient.mobile, "+50488880000")

    def test_intake_requires_secure_submission_context(self):
        with self.assertRaises(AccessError):
            self.env["odental.patient.intake"].create(
                {
                    "patient_id": self.patient.id,
                    "clinical_record_id": self.record.id,
                    "truth_confirmed": True,
                }
            )

    def test_reviewed_intake_creates_history_once(self):
        intake = self._new_intake()
        intake.action_review()
        intake.action_incorporate()
        self.assertEqual(intake.state, "incorporated")
        self.assertEqual(len(intake.incorporated_entry_ids), 2)
        self.assertIn("Penicilina", intake.incorporated_entry_ids.mapped("details"))
        with self.assertRaises(UserError):
            intake.action_incorporate()
