from datetime import datetime

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestODentalAI(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.env.user.has_group("odental_core.group_odental_manager"):
            cls.env.user.write(
                {"groups_id": [(4, cls.env.ref("odental_core.group_odental_manager").id)]}
            )
        cls.env.user.tz = "America/Tegucigalpa"
        cls.organization = cls.env["odental.organization"].create(
            {"name": "Clínica IA", "code": "AI", "user_ids": [(4, cls.env.user.id)]}
        )
        cls.professional = cls.env["odental.professional"].create(
            {
                "name": "Dra. IA",
                "user_id": cls.env.user.id,
                "organization_ids": [(4, cls.organization.id)],
            }
        )
        cls.patient = cls.env["odental.patient"].create(
            {"name": "Paciente IA", "organization_id": cls.organization.id}
        )
        cls.record = cls.env["odental.clinical.record"].create(
            {"patient_id": cls.patient.id}
        )
        cls.site = cls.env["odental.site"].create(
            {"name": "Sede IA", "organization_id": cls.organization.id}
        )
        cls.room = cls.env["odental.resource"].create(
            {
                "name": "Consultorio IA",
                "resource_type": "room",
                "organization_id": cls.organization.id,
                "site_id": cls.site.id,
            }
        )
        cls.chair = cls.env["odental.resource"].create(
            {
                "name": "Sillón IA",
                "resource_type": "chair",
                "organization_id": cls.organization.id,
                "site_id": cls.site.id,
            }
        )
        cls.service = cls.env["odental.service"].create(
            {
                "name": "Evaluación IA",
                "code": "AI-EVAL",
                "organization_id": cls.organization.id,
                "duration_minutes": 30,
            }
        )

    def _session(self, command, **extra):
        values = {
            "organization_id": self.organization.id,
            "patient_id": self.patient.id,
            "professional_id": self.professional.id,
            "command_text": command,
        }
        values.update(extra)
        return self.env["odental.ai.session"].create(values)

    def test_clinical_proposal_requires_confirmation_and_can_be_undone(self):
        session = self._session(
            "Motivo: dolor espontáneo\nDiagnóstico: pulpitis irreversible\nPieza 26 caries oclusal"
        )
        session.action_analyze()
        self.assertEqual(session.state, "analyzed")
        self.assertEqual(len(session.action_ids), 2)
        self.assertTrue(session.input_hash)
        self.assertTrue(session.proposal_hash)
        with self.assertRaises(UserError):
            session.action_execute()
        session.action_confirm()
        session.action_execute()
        self.assertEqual(session.state, "executed")
        self.assertTrue(session.execution_hash)
        encounter = session.action_ids.filtered(
            lambda action: action.action_type == "create_encounter_draft"
        )
        finding = session.action_ids.filtered(
            lambda action: action.action_type == "odontogram_finding"
        )
        self.assertEqual(self.env[encounter.target_model].browse(encounter.target_res_id).state, "draft")
        self.assertEqual(
            self.env[finding.target_model].browse(finding.target_res_id).tooth_id.code, "26"
        )
        session.action_undo()
        self.assertEqual(session.state, "undone")
        self.assertFalse(self.env[encounter.target_model].browse(encounter.target_res_id).exists())
        self.assertFalse(self.env[finding.target_model].browse(finding.target_res_id).exists())

    def test_unknown_line_blocks_confirmation(self):
        session = self._session("Diagnóstico: caries\nHaga cualquier cambio que considere")
        session.action_analyze()
        self.assertTrue(session.warning_text)
        with self.assertRaises(ValidationError):
            session.action_confirm()

    def test_appointment_is_created_as_draft_and_can_be_undone(self):
        session = self._session(
            "Agendar 01/01/2099 10:30",
            service_id=self.service.id,
            site_id=self.site.id,
            resource_ids=[(6, 0, (self.room | self.chair).ids)],
        )
        session.action_analyze()
        session.action_confirm()
        session.action_execute()
        action = session.action_ids
        appointment = self.env[action.target_model].browse(action.target_res_id)
        self.assertEqual(appointment.state, "draft")
        self.assertEqual(appointment.start_datetime, datetime(2099, 1, 1, 16, 30))
        session.action_undo()
        self.assertFalse(appointment.exists())

    def test_reschedule_executes_only_after_confirmation_and_is_not_auto_undoable(self):
        appointment = self.env["odental.appointment"].create(
            {
                "organization_id": self.organization.id,
                "patient_id": self.patient.id,
                "professional_id": self.professional.id,
                "service_id": self.service.id,
                "site_id": self.site.id,
                "resource_ids": [(6, 0, (self.room | self.chair).ids)],
                "start_datetime": datetime(2099, 1, 1, 15, 0),
                "state": "draft",
            }
        )
        session = self._session(
            "Reprogramar 02/01/2099 09:00", appointment_id=appointment.id
        )
        session.action_analyze()
        self.assertEqual(appointment.start_datetime, datetime(2099, 1, 1, 15, 0))
        session.action_confirm()
        session.action_execute()
        self.assertEqual(appointment.start_datetime, datetime(2099, 1, 2, 15, 0))
        self.assertFalse(session.action_ids.undo_supported)
        with self.assertRaises(ValidationError):
            session.action_undo()

    def test_actions_and_audit_cannot_be_created_directly(self):
        session = self._session("Diagnóstico: caries")
        with self.assertRaises(UserError):
            session.with_context(odental_ai_transition=True).write({"state": "executed"})
        with self.assertRaises(AccessError):
            self.env["odental.ai.action"].create(
                {
                    "session_id": session.id,
                    "action_type": "create_encounter_draft",
                    "payload_json": "{}",
                    "preview": "No autorizado",
                }
            )
        with self.assertRaises(AccessError):
            self.env["odental.ai.audit"].create(
                {
                    "organization_id": self.organization.id,
                    "session_id": session.id,
                    "event_type": "captured",
                    "summary": "No autorizado",
                }
            )
