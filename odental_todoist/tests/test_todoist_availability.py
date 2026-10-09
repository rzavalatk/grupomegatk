import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged

from ..controllers.webhook import valid_signature


@tagged("post_install", "-at_install")
class TestTodoistAvailability(TransactionCase):
    def test_webhook_signature_rejects_forgery_and_modified_payload(self):
        body = b'{"event_name":"item:updated","user_id":"doctor-1"}'
        signature = base64.b64encode(hmac.new(
            b"synthetic-secret", body, hashlib.sha256,
        ).digest()).decode()
        self.assertTrue(valid_signature("synthetic-secret", body, signature))
        self.assertFalse(valid_signature("synthetic-secret", body + b" ", signature))
        self.assertFalse(valid_signature("another-secret", body, signature))
        self.assertFalse(valid_signature("", body, signature))

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.organization = cls.env["odental.organization"].create({
            "name": "Clínica piloto", "code": "TODOIST-TEST",
            "user_ids": [(4, cls.env.user.id)],
        })
        cls.professional = cls.env["odental.professional"].create({
            "name": "Jennifer Ejemplo", "user_id": cls.env.user.id,
            "organization_ids": [(4, cls.organization.id)],
        })
        cls.patient = cls.env["odental.patient"].create({
            "name": "Paciente sintético", "organization_id": cls.organization.id,
        })
        cls.site = cls.env["odental.site"].create({
            "name": "Sede de prueba", "organization_id": cls.organization.id,
        })
        cls.service = cls.env["odental.service"].create({
            "name": "Valoración", "code": "TEST-TODOIST",
            "organization_id": cls.organization.id, "duration_minutes": 30,
            "require_room": False, "require_chair": False,
        })
        cls.connection = cls.env["odental.todoist.connection"].sudo().create({
            "professional_id": cls.professional.id,
            "organization_id": cls.organization.id,
            "pilot_patient_id": cls.patient.id,
            "api_token": "synthetic-test-token",
            "todoist_user_id": "doctor-1",
        })

    def _task(self, date="2026-10-02T10:00:00-06:00", labels=None, checked=False):
        return {
            "id": "task-A", "labels": labels if labels is not None else ["reunión"],
            "due": {"date": date}, "duration": {"amount": 60, "unit": "minute"},
            "checked": checked, "is_deleted": False,
            "responsible_uid": "doctor-1",
            "content": "Motivo privado que nunca debe copiarse a la clínica",
        }

    def _clinical_values(self, start):
        return {
            "organization_id": self.organization.id,
            "professional_id": self.professional.id,
            "patient_id": self.patient.id,
            "site_id": self.site.id,
            "service_id": self.service.id,
            "start_datetime": start,
            "state": "scheduled",
        }

    def _future_start(self, hour_utc=16):
        day = fields.Date.today() + timedelta(days=2)
        return datetime.combine(day, datetime.min.time()).replace(hour=hour_utc)

    def _block(self):
        return self.env["odental.appointment"].sudo().search([
            ("entry_type", "=", "busy"),
            ("professional_id", "=", self.professional.id),
            ("external_uid", "=", "task-A"),
        ])

    def test_private_block_conflict_and_completion_release(self):
        self.connection._reconcile_tasks([self._task()])
        block = self._block()
        self.assertEqual(len(block), 1)
        self.assertEqual(block.name, "No disponible")
        self.assertEqual(block.start_datetime, datetime(2026, 10, 2, 16))
        self.assertFalse(block.patient_id or block.service_id or block.site_id or block.notes)
        self.assertNotIn("Motivo privado", block.name)
        with self.assertRaisesRegex(ValidationError, "no está disponible"), self.env.cr.savepoint():
            self.env["odental.appointment"].create(
                self._clinical_values(datetime(2026, 10, 2, 16, 15))
            )
        self.connection._reconcile_tasks([self._task(checked=True)])
        self.assertEqual(block.state, "cancelled")
        clinical = self.env["odental.appointment"].create(
            self._clinical_values(datetime(2026, 10, 2, 16, 15))
        )
        self.assertEqual(clinical.state, "scheduled")

    def test_move_and_label_removal_release_original_slot(self):
        self.connection._reconcile_tasks([self._task()])
        self.connection._reconcile_tasks([self._task(date="2026-10-02T12:00:00-06:00")])
        block = self._block()
        self.assertEqual(len(block), 1)
        self.assertEqual(block.start_datetime, datetime(2026, 10, 2, 18))
        self.connection._reconcile_tasks([self._task(labels=["personal"])])
        self.assertEqual(block.state, "cancelled")
        self.assertEqual(block.last_schedule_change_source, "todoist")
        self.assertEqual(block.last_schedule_changed_by, self.professional.user_id)
        self.assertEqual(block.schedule_audit_ids.sorted("id").mapped("event"),
                         ["created", "changed", "cancelled"])

    def test_incomplete_provider_response_keeps_existing_block(self):
        self.connection._reconcile_tasks([self._task()])
        with patch.object(type(self.connection), "_get_json", return_value={"results": None}):
            with self.assertRaises(UserError):
                self.connection._sync_one()
        self.assertEqual(self._block().state, "scheduled")

    def test_other_organization_block_is_untouched(self):
        second = self.env["odental.organization"].create({
            "name": "Otra clínica sintética", "code": "OTHER-TODOIST-TEST",
            "user_ids": [(4, self.env.user.id)],
        })
        self.professional.organization_ids = [(4, second.id)]
        second_patient = self.env["odental.patient"].create({
            "name": "Paciente de segunda clínica", "organization_id": second.id,
        })
        other_connection = self.env["odental.todoist.connection"].sudo().create({
            "professional_id": self.professional.id,
            "organization_id": second.id,
            "pilot_patient_id": second_patient.id,
            "api_token": "synthetic-test-token", "todoist_user_id": "doctor-1",
        })
        self.connection._reconcile_tasks([self._task()])
        other_connection._reconcile_tasks([self._task()])
        self.connection._reconcile_tasks([])
        blocks = self._block()
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks.filtered(lambda item: item.organization_id == second).state, "scheduled")
        self.assertEqual(blocks.filtered(lambda item: item.organization_id == self.organization).state, "cancelled")

    def test_untimed_task_never_blocks_and_cancelled_action_exists(self):
        self.connection._reconcile_tasks([self._task(date="2026-10-02")])
        self.assertFalse(self._block())
        action = self.env.ref("odental_core.action_odental_appointment")
        self.assertIn("cancelled", action.domain)

    def test_timed_task_without_paid_duration_uses_default(self):
        task = self._task()
        task["duration"] = None
        self.connection.default_duration_minutes = 45
        self.connection._reconcile_tasks([task])
        self.assertEqual(self._block().duration_minutes, 45)

    def test_clinical_appointment_creates_moves_and_deletes_private_todoist_task(self):
        appointment = self.env["odental.appointment"].create(
            {**self._clinical_values(self._future_start()),
             "notes": "Diagnóstico confidencial que nunca sale de O Dental"}
        )
        with patch.object(type(self.connection), "_send_json", return_value={"id": "mirror-1"}) as send:
            self.connection._reconcile_exports([])
        payload = send.call_args.args[3]
        self.assertEqual(send.call_args.args[1:3], ("POST", "tasks"))
        self.assertIn(self.patient.name, payload["content"])
        self.assertIn(self.service.name, payload["content"])
        self.assertNotIn("Diagnóstico confidencial", str(payload))
        self.assertIn("10:00", payload["content"])
        self.assertIn("reunión", payload["labels"])
        mirror = self.env["odental.todoist.mirror"].sudo().search([
            ("appointment_id", "=", appointment.id)
        ])
        self.assertEqual(mirror.task_id, "mirror-1")
        remote = {"id": "mirror-1", "content": payload["content"],
                  "description": payload["description"], "labels": ["odental"],
                  "due": {"datetime": payload["due_datetime"]}}
        appointment.write({"start_datetime": self._future_start(18)})
        with patch.object(type(self.connection), "_send_json", return_value=None) as send:
            self.connection._reconcile_exports([remote])
        self.assertEqual(send.call_args.args[1:3], ("POST", "tasks/mirror-1"))
        self.assertIn("12:00", send.call_args.args[3]["content"])
        appointment.action_cancel()
        with patch.object(type(self.connection), "_send_json", return_value=None) as send:
            self.connection._reconcile_exports([remote])
        self.assertEqual(send.call_args.args[1:3], ("DELETE", "tasks/mirror-1"))
        self.assertFalse(mirror.exists())

    def test_pilot_never_exports_other_patient_appointments(self):
        real_patient = self.env["odental.patient"].create({
            "name": "Paciente fuera de prueba", "organization_id": self.organization.id,
        })
        real_appointment = self.env["odental.appointment"].create({
            **self._clinical_values(self._future_start()), "patient_id": real_patient.id,
        })
        with patch.object(type(self.connection), "_send_json") as send:
            self.connection._reconcile_exports([])
            send.assert_not_called()
        self.assertFalse(self.env["odental.todoist.mirror"].sudo().search([
            ("appointment_id", "=", real_appointment.id),
        ]))

    def test_full_scope_requires_explicit_setting_and_stays_in_clinic(self):
        real_patient = self.env["odental.patient"].create({
            "name": "Paciente de activación", "organization_id": self.organization.id,
        })
        appointment = self.env["odental.appointment"].create({
            **self._clinical_values(self._future_start()), "patient_id": real_patient.id,
        })
        self.assertFalse(self.connection.export_all_patients)
        with patch.object(type(self.connection), "_send_json") as send:
            self.connection._reconcile_exports([])
            send.assert_not_called()
        self.connection.export_all_patients = True
        with patch.object(type(self.connection), "_send_json", return_value={"id": "real-mirror"}) as send:
            self.connection._reconcile_exports([])
        self.assertEqual(send.call_args.args[3]["content"].split(" · ")[0],
                         f"Atender a {real_patient.name}")
        mirror = self.env["odental.todoist.mirror"].sudo().search([
            ("appointment_id", "=", appointment.id),
            ("connection_id", "=", self.connection.id),
        ])
        self.assertEqual(mirror.task_id, "real-mirror")

    def test_pilot_patient_must_belong_to_clinic(self):
        second = self.env["odental.organization"].create({
            "name": "Otra clínica", "code": "PILOT-OTHER",
            "user_ids": [(4, self.env.user.id)],
        })
        other_patient = self.env["odental.patient"].create({
            "name": "Otra persona", "organization_id": second.id,
        })
        with self.assertRaisesRegex(ValidationError, "paciente de prueba"), self.env.cr.savepoint():
            self.connection.pilot_patient_id = other_patient

    def test_doctor_moving_todoist_mirror_updates_clinical_appointment(self):
        appointment = self.env["odental.appointment"].create(
            self._clinical_values(self._future_start())
        )
        with patch.object(type(self.connection), "_send_json", return_value={"id": "mirror-2"}):
            self.connection._reconcile_exports([])
        original = self.connection._export_payload(appointment)
        # Reception and the doctor both move the visit before the next poll.
        appointment.write({"start_datetime": self._future_start(17)})
        doctor_edit = {"id": "mirror-2", "content": original["content"],
                       "description": original["description"], "labels": ["reunión", "odental"],
                       "due": {"datetime": self._future_start(18).isoformat() + "Z"}}
        with patch.object(type(self.connection), "_send_json", return_value=None):
            self.connection._reconcile_exports([doctor_edit])
        self.assertEqual(appointment.start_datetime, self._future_start(18))
        self.assertFalse(appointment.external_conflict)
        entries = appointment.schedule_audit_ids.sorted("id")
        self.assertEqual(entries.mapped("source"), ["odoo", "odoo", "todoist"])
        self.assertEqual(entries[-1].actor_user_id, self.professional.user_id)
        self.assertEqual(entries[-1].old_values["start_datetime"],
                         fields.Datetime.to_string(self._future_start(17)))
        self.assertEqual(entries[-1].new_values["start_datetime"],
                         fields.Datetime.to_string(self._future_start(18)))

    def test_doctor_move_into_occupied_clinical_slot_is_flagged(self):
        appointment = self.env["odental.appointment"].create(
            self._clinical_values(self._future_start())
        )
        with patch.object(type(self.connection), "_send_json", return_value={"id": "mirror-3"}):
            self.connection._reconcile_exports([])
        self.env["odental.appointment"].create(self._clinical_values(self._future_start(18)))
        original = self.connection._export_payload(appointment)
        doctor_edit = {"id": "mirror-3", "content": original["content"],
                       "description": original["description"], "labels": ["reunión", "odental"],
                       "due": {"datetime": self._future_start(18).isoformat() + "Z"}}
        with patch.object(type(self.connection), "_send_json", return_value={"id": "mirror-4"}) as send:
            conflict = self.connection._reconcile_exports([doctor_edit])
        self.assertTrue(conflict)
        self.assertTrue(appointment.external_conflict)
        self.assertEqual(appointment.start_datetime, self._future_start())
        self.assertFalse(any(call.args[2] == "tasks/mirror-3" for call in send.call_args_list))

    def test_conflict_clears_when_doctor_restores_original_time(self):
        appointment = self.env["odental.appointment"].create(
            self._clinical_values(self._future_start())
        )
        with patch.object(type(self.connection), "_send_json", return_value={"id": "mirror-return"}):
            self.connection._reconcile_exports([])
        self.env["odental.appointment"].create(self._clinical_values(self._future_start(18)))
        original = self.connection._export_payload(appointment)
        remote = {"id": "mirror-return", "content": original["content"],
                  "description": original["description"], "labels": ["reunión", "odental"],
                  "due": {"datetime": self._future_start(18).isoformat() + "Z"}}
        with patch.object(type(self.connection), "_send_json", return_value={"id": "mirror-second"}):
            self.assertTrue(self.connection._reconcile_exports([remote]))
        self.assertTrue(appointment.external_conflict)
        remote["due"]["datetime"] = self._future_start().isoformat() + "Z"
        with patch.object(type(self.connection), "_send_json", return_value={"id": "mirror-second"}):
            self.assertFalse(self.connection._reconcile_exports([remote]))
        self.assertFalse(appointment.external_conflict)
        self.assertEqual(appointment.start_datetime, self._future_start())

    def test_clinical_mirror_never_reimports_as_meeting(self):
        appointment = self.env["odental.appointment"].create(
            self._clinical_values(self._future_start())
        )
        remote = {"id": "mirror-1", "description": self.connection._export_payload(appointment)["description"],
                  "labels": ["reunión", "odental"], "due": {"datetime": "2026-10-02T16:00:00Z"},
                  "duration": {"amount": 60, "unit": "minute"}}
        self.connection._reconcile_tasks([remote])
        self.assertFalse(self._block())

    def test_cross_company_user_cannot_sync(self):
        other_company = self.env["res.company"].sudo().search([
            ("id", "!=", self.env.company.id),
        ], limit=1)
        if not other_company:
            self.skipTest("La prueba de aislamiento requiere una segunda compañía.")
        wrong_user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Profesional con cuenta equivocada",
            "login": "odental-todoist-mismatch@example.invalid",
            "company_id": other_company.id,
            "company_ids": [(6, 0, [other_company.id])],
        })
        self.professional.user_id = wrong_user
        with patch.object(type(self.connection), "_fetch_tasks") as fetch:
            with self.assertRaisesRegex(ValidationError, "acceso a la compañía"):
                self.connection._sync_one()
            fetch.assert_not_called()

    def test_secondary_company_professional_can_sync_own_clinic(self):
        other_company = self.env["res.company"].sudo().search([
            ("id", "!=", self.env.company.id),
        ], limit=1)
        if not other_company:
            self.skipTest("La prueba requiere una segunda compañía.")
        professional_user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Profesional multiempresa",
            "login": "odental-todoist-multicompany@example.invalid",
            "company_id": other_company.id,
            "company_ids": [(6, 0, [other_company.id, self.env.company.id])],
        })
        self.professional.user_id = professional_user
        with patch.object(type(self.connection), "_fetch_tasks", return_value=[]) as fetch, \
             patch.object(type(self.connection), "_reconcile_tasks"), \
             patch.object(type(self.connection), "_reconcile_exports", return_value=[]):
            self.connection._sync_one()
            fetch.assert_called_once_with("synthetic-test-token")
