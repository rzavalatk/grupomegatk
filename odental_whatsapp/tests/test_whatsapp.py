import hashlib
import hmac
from datetime import datetime
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase


class FakeResponse:
    ok = True
    status_code = 200

    def json(self):
        return {"messages": [{"id": "wamid.test-001"}]}


class TestODentalWhatsApp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        admin_group = cls.env.ref("odental_core.group_odental_admin")
        if not cls.env.user.has_group("odental_core.group_odental_admin"):
            cls.env.user.write({"groups_id": [(4, admin_group.id)]})
        cls.organization = cls.env["odental.organization"].create({
            "name": "Clínica WhatsApp", "code": "WAT",
            "user_ids": [(4, cls.env.user.id)], "automatic_appointment_messages": True,
        })
        cls.account = cls.env["odental.whatsapp.account"].create({
            "name": "Recepción principal", "organization_id": cls.organization.id,
            "phone_number_id": "123456789", "display_phone": "+504 2200-0000",
        })
        cls.account._set_secret("access_token", "test-access-token")
        cls.account._set_secret("app_secret", "test-app-secret")
        cls.account._set_secret("verify_token_hash", hashlib.sha256(b"test-verify-token").hexdigest())
        cls.account.automatic_delivery = True
        cls.organization.whatsapp_default_account_id = cls.account
        cls.professional = cls.env["odental.professional"].create({
            "name": "Dra. WhatsApp", "organization_ids": [(4, cls.organization.id)],
        })
        cls.service = cls.env["odental.service"].create({
            "name": "Evaluación", "code": "EVA-WA", "organization_id": cls.organization.id,
            "require_room": False, "require_chair": False,
        })
        cls.site = cls.env["odental.site"].create({
            "name": "Sede WhatsApp", "organization_id": cls.organization.id,
        })
        cls.patient = cls.env["odental.patient"].create({
            "name": "Paciente WhatsApp", "organization_id": cls.organization.id,
            "mobile": "+504 9999-0000", "preferred_appointment_channel": "whatsapp",
            "appointment_messages_consent": True,
            "appointment_messages_consent_source": "Portal",
        })
        cls.template = cls.env["odental.communication.template"].create({
            "name": "Confirmación Meta", "organization_id": cls.organization.id,
            "message_type": "confirmation", "channel": "whatsapp",
            "body": "Hola {patient_name}, confirme {appointment_datetime}",
            "whatsapp_template_name": "odental_confirmacion",
            "whatsapp_language_code": "es",
            "whatsapp_template_status": "approved",
            "whatsapp_body_parameter_names": "patient_name, appointment_datetime",
            "whatsapp_action_mode": "appointment",
        })

    def _appointment(self):
        appointment = self.env["odental.appointment"].create({
            "organization_id": self.organization.id,
            "patient_id": self.patient.id,
            "professional_id": self.professional.id,
            "service_id": self.service.id,
            "site_id": self.site.id,
            "start_datetime": datetime(2026, 10, 20, 9, 0),
        })
        appointment.action_schedule()
        return appointment

    def test_credentials_are_verified_without_exposing_verify_token(self):
        self.assertTrue(self.account.credentials_configured)
        self.assertTrue(self.account._verify_challenge_token("test-verify-token"))
        self.assertFalse(self.account._verify_challenge_token("incorrect"))
        raw = b'{"object":"whatsapp_business_account"}'
        signature = "sha256=" + hmac.new(b"test-app-secret", raw, hashlib.sha256).hexdigest()
        self.assertTrue(self.account._verify_signature(raw, signature))

    def test_message_builds_approved_template_and_quick_replies(self):
        message = self._appointment().communication_message_ids.filtered(
            lambda item: item.message_type == "confirmation"
        )
        payload = message._whatsapp_payload()
        self.assertEqual(payload["to"], "50499990000")
        self.assertEqual(payload["template"]["name"], "odental_confirmacion")
        self.assertEqual(len(message.whatsapp_action_token_ids), 3)
        self.assertEqual(payload["template"]["components"][0]["type"], "body")

    def test_verified_button_can_confirm_once(self):
        appointment = self._appointment()
        message = appointment.communication_message_ids.filtered(
            lambda item: item.message_type == "confirmation"
        )
        message._whatsapp_payload()
        token = message.whatsapp_action_token_ids.filtered(lambda item: item.action == "confirm")
        request_record = token._consume(self.patient.whatsapp_wa_id)
        self.assertEqual(request_record.state, "applied")
        self.assertEqual(appointment.state, "confirmed")
        with self.assertRaises(ValidationError):
            token._consume(self.patient.whatsapp_wa_id)

    def test_token_rejects_another_phone(self):
        message = self._appointment().communication_message_ids.filtered(
            lambda item: item.message_type == "confirmation"
        )
        message._whatsapp_payload()
        token = message.whatsapp_action_token_ids[:1]
        with self.assertRaises(AccessError):
            token._consume("50488880000")

    def test_outbound_send_records_provider_id_and_digest(self):
        message = self._appointment().communication_message_ids.filtered(
            lambda item: item.message_type == "confirmation"
        )
        with patch("odoo.addons.odental_whatsapp.models.whatsapp.requests.post", return_value=FakeResponse()):
            message.action_send_whatsapp()
        self.assertEqual(message.state, "sent")
        self.assertEqual(message.whatsapp_provider_message_id, "wamid.test-001")
        self.assertTrue(message.whatsapp_payload_digest)

    def test_event_log_is_immutable(self):
        event = self.env["odental.whatsapp.event"].with_context(
            odental_whatsapp_event_create=True
        ).create({
            "account_id": self.account.id, "event_key": "message:test-event",
            "event_type": "message", "payload_digest": "abc", "state": "ignored",
        })
        with self.assertRaises(UserError):
            event.write({"processing_note": "alterado"})

