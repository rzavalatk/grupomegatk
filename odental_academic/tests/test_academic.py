from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestODentalAcademic(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Odoo's install-time superuser is archived but serves as the test
        # supervisor; keep it visible in the rotation's user relations.
        cls.env = cls.env(context={**cls.env.context, "active_test": False})
        manager_group = cls.env.ref("odental_academic.group_odental_academic_manager")
        if manager_group not in cls.env.user.groups_id:
            cls.env.user.write({"groups_id": [(4, manager_group.id)]})
        cls.organization = cls.env["odental.organization"].create(
            {
                "name": "Universidad Clínica",
                "code": "UNI",
                "organization_type": "university",
                "billing_mode": "centralized",
                "user_ids": [(4, cls.env.user.id)],
            }
        )
        cls.supervisor_professional = cls.env["odental.professional"].create(
            {
                "name": "Dra. Docente",
                "user_id": cls.env.user.id,
                "organization_ids": [(4, cls.organization.id)],
            }
        )
        cls.student = cls.env["res.users"].create(
            {
                "name": "Estudiante Uno",
                "login": "student-academic-test@example.invalid",
                "email": "student-academic-test@example.invalid",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("odental_academic.group_odental_academic_student").id,
                        ],
                    )
                ],
            }
        )
        cls.patient = cls.env["odental.patient"].create(
            {"name": "Paciente Universitario", "organization_id": cls.organization.id}
        )
        cls.record = cls.env["odental.clinical.record"].create(
            {"patient_id": cls.patient.id}
        )
        today = fields.Date.today()
        cls.program = cls.env["odental.academic.program"].create(
            {"name": "Doctorado en Cirugía Dental", "code": "DCD", "organization_id": cls.organization.id}
        )
        cls.period = cls.env["odental.academic.period"].create(
            {
                "name": "III Período 2026",
                "program_id": cls.program.id,
                "date_start": today - timedelta(days=30),
                "date_end": today + timedelta(days=90),
            }
        )
        cls.period.action_activate()
        cls.rotation = cls.env["odental.academic.rotation"].create(
            {
                "name": "Clínica integral",
                "code": "CI-01",
                "period_id": cls.period.id,
                "date_start": today - timedelta(days=10),
                "date_end": today + timedelta(days=30),
                "student_user_ids": [(4, cls.student.id)],
                "supervisor_user_ids": [(4, cls.env.user.id)],
            }
        )
        cls.rotation.action_activate()
        cls.case = cls.env["odental.academic.case"].create(
            {
                "rotation_id": cls.rotation.id,
                "patient_id": cls.patient.id,
                "student_user_id": cls.student.id,
                "supervisor_user_id": cls.env.user.id,
                "supervisor_professional_id": cls.supervisor_professional.id,
                "access_start": today - timedelta(days=1),
                "access_end": today + timedelta(days=10),
                "reason_for_care": "Evaluación clínica integral asignada.",
                "relevant_alerts": "Sin alergias reportadas para esta atención.",
            }
        )
        cls.case.action_activate()

    def _student_submission(self, **extra):
        values = {
            "case_id": self.case.id,
            "submission_type": "clinical_note",
            "content": "Hallazgos preparados por el estudiante para revisión.",
            "procedure_code": "EVAL",
            "procedure_name": "Evaluación integral",
        }
        values.update(extra)
        submission = self.env["odental.academic.submission"].with_user(self.student).create(values)
        # Submission is made as the student; review actions below are performed
        # by the supervisor, with student actions explicitly using with_user.
        return submission.with_env(self.env)

    def test_student_profile_cannot_receive_general_clinical_access(self):
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.student.write(
                {"groups_id": [(4, self.env.ref("odental_core.group_odental_user").id)]}
            )
        with self.assertRaises(AccessError):
            self.env["odental.patient"].with_user(self.student).search([]).read(["name"])
        values = self.case.with_user(self.student).read(
            ["patient_display_name", "reason_for_care"]
        )[0]
        self.assertEqual(values["patient_display_name"], "Paciente Universitario")

    def test_student_work_requires_supervisor_and_creates_only_draft(self):
        submission = self._student_submission()
        with self.assertRaises(UserError):
            submission.with_user(self.env.user).action_apply()
        submission.with_user(self.student).action_submit()
        self.assertEqual(submission.state, "submitted")
        self.assertTrue(submission.submitted_hash)
        submission.write(
            {
                "supervisor_comments": "Trabajo revisado.",
                "supervisor_score": 92,
                "competency": "competent",
            }
        )
        submission.action_approve()
        submission.action_apply()
        encounter = self.env[submission.target_model].browse(submission.target_res_id)
        self.assertEqual(encounter.state, "draft")
        self.assertEqual(encounter.professional_id, self.supervisor_professional)
        self.assertFalse(encounter.signed_at)

    def test_api_cannot_skip_academic_states(self):
        submission = self.env["odental.academic.submission"].with_user(self.student).create(
            {
                "case_id": self.case.id,
                "submission_type": "clinical_note",
                "content": "Intento controlado.",
                "state": "approved",
                "supervisor_score": 100,
            }
        )
        self.assertEqual(submission.state, "draft")
        self.assertEqual(submission.supervisor_score, 0)
        with self.assertRaises(UserError):
            submission.with_context(odental_academic_submission_transition=True).write(
                {"state": "approved"}
            )
        with self.assertRaises(UserError):
            self.period.with_context(odental_academic_period_transition=True).write(
                {"state": "closed"}
            )

    def test_rejected_work_creates_traceable_revision(self):
        submission = self._student_submission()
        submission.with_user(self.student).action_submit()
        submission.supervisor_comments = "Amplíe los hallazgos clínicos."
        submission.action_reject()
        revision_action = submission.with_user(self.student).action_create_revision()
        revision = self.env["odental.academic.submission"].browse(
            revision_action["res_id"]
        )
        self.assertEqual(revision.state, "draft")
        self.assertEqual(revision.previous_submission_id, submission)

    def test_odontogram_submission_remains_unsigned(self):
        submission = self._student_submission(
            submission_type="odontogram_finding",
            content="Lesión observada para validación docente.",
            tooth_code="26",
            surface="occlusal",
            condition="caries",
            finding_status="existing",
        )
        submission.with_user(self.student).action_submit()
        submission.action_approve()
        submission.action_apply()
        finding = self.env["odental.odontogram.finding"].browse(
            submission.target_res_id
        )
        self.assertEqual(finding.tooth_id.code, "26")
        self.assertEqual(finding.odontogram_id.state, "draft")

    def test_case_completion_removes_student_visibility(self):
        self.case.action_complete()
        with self.assertRaises(AccessError):
            self.case.with_user(self.student).read(["patient_display_name"])
