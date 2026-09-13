from datetime import datetime
from uuid import uuid4

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestODentalOffline(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.env.user.has_group("odental_core.group_odental_manager"):
            cls.env.user.write(
                {"groups_id": [(4, cls.env.ref("odental_core.group_odental_manager").id)]}
            )
        cls.organization = cls.env["odental.organization"].create(
            {"name": "Clínica Contingencia", "code": "OFF", "user_ids": [(4, cls.env.user.id)]}
        )
        cls.professional = cls.env["odental.professional"].create(
            {
                "name": "Dra. Contingencia",
                "user_id": cls.env.user.id,
                "organization_ids": [(4, cls.organization.id)],
            }
        )
        cls.patient = cls.env["odental.patient"].create(
            {"name": "Paciente Offline", "organization_id": cls.organization.id}
        )
        cls.record = cls.env["odental.clinical.record"].create(
            {"patient_id": cls.patient.id}
        )
        cls.site = cls.env["odental.site"].create(
            {"name": "Sede Contingencia", "organization_id": cls.organization.id}
        )
        cls.service = cls.env["odental.service"].create(
            {
                "name": "Evaluación Offline",
                "code": "OFF-EVAL",
                "organization_id": cls.organization.id,
                "duration_minutes": 30,
            }
        )
        cls.appointment = cls.env["odental.appointment"].create(
            {
                "organization_id": cls.organization.id,
                "patient_id": cls.patient.id,
                "professional_id": cls.professional.id,
                "service_id": cls.service.id,
                "site_id": cls.site.id,
                "start_datetime": datetime(2099, 1, 1, 15, 0),
                "state": "confirmed",
            }
        )

    def _entry(self, entry_type="clinical_note", **values):
        result = {
            "client_uuid": str(uuid4()),
            "appointment_id": self.appointment.id,
            "entry_type": entry_type,
            "content": "Dolor localizado registrado durante la contingencia.",
            "tooth_code": "",
            "surface": "",
            "condition": "",
            "finding_status": "",
            "client_created_at": datetime(2099, 1, 1, 15, 30),
        }
        result.update(values)
        return result

    def _batch(self, entries):
        return self.env["odental.contingency.batch"]._ingest(
            self.organization,
            self.env.user,
            str(uuid4()),
            str(uuid4()),
            entries,
            metadata={"ip": "127.0.0.1", "user_agent": "O Dental test"},
        )

    def test_ingest_is_idempotent_and_hashes_device(self):
        device = str(uuid4())
        batch_uuid = str(uuid4())
        entry = self._entry()
        model = self.env["odental.contingency.batch"]
        first = model._ingest(
            self.organization, self.env.user, device, batch_uuid, [entry]
        )
        second = model._ingest(
            self.organization, self.env.user, device, batch_uuid, [entry]
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first.device_hash, device)
        self.assertEqual(len(first.device_hash), 64)
        self.assertEqual(first.entry_ids.client_uuid, entry["client_uuid"])

    def test_clinical_note_requires_review_and_creates_only_draft(self):
        batch = self._batch([self._entry()])
        with self.assertRaises(UserError):
            batch.entry_ids.action_apply()
        batch.action_review()
        batch.entry_ids.action_apply()
        encounter = self.env[batch.entry_ids.target_model].browse(
            batch.entry_ids.target_res_id
        )
        self.assertEqual(encounter.state, "draft")
        self.assertEqual(encounter.clinical_record_id, self.record)
        self.assertEqual(batch.state, "applied")
        self.assertFalse(encounter.signed_at)

    def test_prescription_is_a_separate_draft(self):
        batch = self._batch(
            [self._entry("prescription", content="Indicaciones revisables de prueba.")]
        )
        batch.action_review()
        batch.entry_ids.action_apply()
        encounter = self.env["odental.clinical.encounter"].browse(
            batch.entry_ids.target_res_id
        )
        self.assertEqual(encounter.prescriptions, "Indicaciones revisables de prueba.")
        self.assertEqual(encounter.state, "draft")

    def test_odontogram_finding_creates_unsigned_finding(self):
        batch = self._batch(
            [
                self._entry(
                    "odontogram_finding",
                    content="Hallazgo observado sin conexión.",
                    tooth_code="26",
                    surface="occlusal",
                    condition="caries",
                    finding_status="existing",
                )
            ]
        )
        batch.action_review()
        batch.entry_ids.action_apply()
        finding = self.env["odental.odontogram.finding"].browse(
            batch.entry_ids.target_res_id
        )
        self.assertEqual(finding.tooth_id.code, "26")
        self.assertEqual(finding.odontogram_id.state, "draft")

    def test_direct_creation_and_spoofed_transition_are_blocked(self):
        with self.assertRaises(AccessError):
            self.env["odental.contingency.batch"].create(
                {
                    "organization_id": self.organization.id,
                    "user_id": self.env.user.id,
                    "device_hash": "x" * 64,
                    "client_batch_uuid": str(uuid4()),
                    "content_hash": "y" * 64,
                }
            )
        batch = self._batch([self._entry()])
        with self.assertRaises(UserError):
            batch.with_context(odental_offline_batch_transition=True).write(
                {"state": "applied"}
            )
        with self.assertRaises(UserError):
            batch.entry_ids.with_context(odental_offline_entry_transition=True).write(
                {"state": "applied"}
            )

    def test_duplicate_entry_in_a_different_batch_is_rejected(self):
        entry = self._entry()
        self._batch([entry])
        with self.assertRaises(ValidationError):
            self._batch([entry])

