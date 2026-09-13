from datetime import date, datetime, timedelta

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestODentalCommunications(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        manager_group = cls.env.ref("odental_core.group_odental_manager")
        if not cls.env.user.has_group("odental_core.group_odental_manager"):
            cls.env.user.write({"groups_id": [(4, manager_group.id)]})
        cls.organization = cls.env["odental.organization"].create({
            "name": "Clínica comunicaciones", "code": "COM",
            "user_ids": [(4, cls.env.user.id)],
            "automatic_appointment_messages": True,
            "reminder_hours_before": 24, "waitlist_offer_minutes": 30,
        })
        cls.professional = cls.env["odental.professional"].create({
            "name": "Dra. Agenda", "organization_ids": [(4, cls.organization.id)],
        })
        cls.service = cls.env["odental.service"].create({
            "name": "Profilaxis", "code": "PROF-COM",
            "organization_id": cls.organization.id,
            "require_room": False, "require_chair": False,
        })
        cls.site = cls.env["odental.site"].create({
            "name": "Sede comunicaciones", "organization_id": cls.organization.id,
        })
        cls.patient = cls.env["odental.patient"].create({
            "name": "Paciente con permiso", "organization_id": cls.organization.id,
            "mobile": "+50499990000", "preferred_appointment_channel": "whatsapp",
            "appointment_messages_consent": True,
            "appointment_messages_consent_source": "Formulario de ingreso",
        })
        cls.waiting_patient = cls.env["odental.patient"].create({
            "name": "Paciente en espera", "organization_id": cls.organization.id,
            "mobile": "+50499990001", "preferred_appointment_channel": "whatsapp",
            "appointment_messages_consent": True,
            "appointment_messages_consent_source": "Portal del paciente",
        })

    def _appointment(self, patient=None, hour=9):
        return self.env["odental.appointment"].create({
            "organization_id": self.organization.id,
            "patient_id": (patient or self.patient).id,
            "professional_id": self.professional.id,
            "service_id": self.service.id,
            "site_id": self.site.id,
            "start_datetime": datetime(2026, 10, 20, hour, 0),
        })

    def test_consent_is_logged_and_channel_change_revokes_it(self):
        events = self.patient.communication_consent_event_ids
        self.assertEqual(len(events), 1)
        self.assertEqual(events.event_type, "granted")
        self.patient.write({"preferred_appointment_channel": "email"})
        self.assertFalse(self.patient.appointment_messages_consent)
        revoked = self.patient.communication_consent_event_ids.filtered(
            lambda event: event.event_type == "revoked"
        )
        self.assertEqual(revoked.channel, "whatsapp")
        with self.assertRaises(UserError):
            events.write({"source": "Alterado"})

    def test_scheduling_prepares_message_without_external_send(self):
        appointment = self._appointment()
        appointment.action_schedule()
        message = appointment.communication_message_ids.filtered(
            lambda item: item.message_type == "confirmation"
        )
        self.assertEqual(message.state, "queued")
        self.assertFalse(message.sent_at)
        appointment.action_prepare_reminder()
        appointment.action_prepare_reminder()
        reminders = appointment.communication_message_ids.filtered(
            lambda item: item.message_type == "reminder"
        )
        self.assertEqual(len(reminders), 1)

    def test_message_cannot_be_fabricated_outside_the_workflow(self):
        with self.assertRaises(AccessError):
            self.env["odental.communication.message"].create({
                "organization_id": self.organization.id,
                "patient_id": self.patient.id,
                "message_type": "reminder", "channel": "whatsapp",
                "recipient": self.patient.mobile, "body": "Mensaje ajeno al flujo",
                "deduplication_key": "manual",
            })

    def test_patient_confirmation_closes_the_pending_request(self):
        appointment = self._appointment(hour=10)
        appointment.action_schedule()
        request_message = appointment.communication_message_ids
        appointment.action_register_patient_confirmation()
        self.assertEqual(appointment.patient_response, "confirmed")
        self.assertEqual(appointment.state, "confirmed")
        self.assertEqual(request_message.state, "cancelled")
        acknowledgement = appointment.communication_message_ids.filtered(
            lambda item: item.message_type == "confirmed"
        )
        self.assertEqual(acknowledgement.state, "queued")

    def test_missing_consent_blocks_delivery(self):
        patient = self.env["odental.patient"].create({
            "name": "Paciente sin permiso", "organization_id": self.organization.id,
            "mobile": "+50499990002", "preferred_appointment_channel": "whatsapp",
        })
        appointment = self._appointment(patient=patient, hour=11)
        appointment.action_schedule()
        message = appointment.communication_message_ids
        self.assertEqual(message.state, "blocked")
        self.assertIn("no ha autorizado", message.blocking_reason)

    def test_rescheduling_cancels_old_notice_and_prepares_a_new_one(self):
        appointment = self._appointment(hour=12)
        appointment.action_schedule()
        old_message = appointment.communication_message_ids
        appointment.write({"start_datetime": datetime(2026, 10, 20, 13, 30)})
        self.assertEqual(old_message.state, "cancelled")
        rescheduled = appointment.communication_message_ids.filtered(
            lambda item: item.message_type == "rescheduled"
        )
        self.assertEqual(rescheduled.state, "queued")
        self.assertEqual(appointment.patient_response, "pending")

    def test_cancelled_slot_is_offered_and_rebooked(self):
        entry = self.env["odental.waitlist.entry"].create({
            "organization_id": self.organization.id,
            "patient_id": self.waiting_patient.id,
            "service_id": self.service.id,
            "desired_start_date": date(2026, 10, 1),
            "desired_end_date": date(2026, 10, 31),
            "priority": "urgent",
        })
        original = self._appointment()
        original.action_schedule()
        original.action_cancel()
        offer = original.slot_offer_ids
        self.assertEqual(entry.state, "offered")
        self.assertEqual(offer.state, "offered")
        self.assertEqual(offer.message_ids.state, "queued")
        self.assertIn(self.waiting_patient.name, offer.message_ids.body)
        self.assertNotIn(self.patient.name, offer.message_ids.body)
        action = offer.action_accept()
        replacement = self.env["odental.appointment"].browse(action["res_id"])
        self.assertEqual(replacement.state, "scheduled")
        self.assertEqual(replacement.patient_id, self.waiting_patient)
        self.assertEqual(replacement.start_datetime, original.start_datetime)
        self.assertEqual(replacement.replaced_appointment_id, original)
        self.assertEqual(original.replacement_appointment_id, replacement)
        self.assertEqual(entry.state, "booked")
        self.assertEqual(offer.state, "accepted")

    def test_invalid_template_placeholder_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["odental.communication.template"].create({
                "name": "Plantilla inválida", "organization_id": self.organization.id,
                "message_type": "reminder", "channel": "whatsapp",
                "body": "Dato no permitido: {diagnosis}",
            })

    def test_expired_offer_releases_waitlist_entry(self):
        entry = self.env["odental.waitlist.entry"].create({
            "organization_id": self.organization.id,
            "patient_id": self.waiting_patient.id,
            "service_id": self.service.id,
            "desired_start_date": date(2026, 10, 1),
            "desired_end_date": date(2026, 10, 31),
        })
        original = self._appointment(hour=14)
        original.action_schedule()
        original.action_cancel()
        offer = original.slot_offer_ids
        offer.with_context(odental_offer_transition=True).write({
            "expires_at": datetime.now() - timedelta(minutes=1)
        })
        offer.action_expire()
        self.assertEqual(offer.state, "expired")
        self.assertEqual(entry.state, "waiting")
