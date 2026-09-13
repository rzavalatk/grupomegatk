import base64

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestODentalDiagnostics(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.organization = cls.env["odental.organization"].create(
            {"name": "Clínica diagnóstico", "code": "DIAG", "user_ids": [(4, cls.env.user.id)]}
        )
        cls.professional = cls.env["odental.professional"].create(
            {"name": "Dr. Diagnóstico", "organization_ids": [(4, cls.organization.id)]}
        )
        cls.patient = cls.env["odental.patient"].create(
            {"name": "Paciente diagnóstico", "organization_id": cls.organization.id}
        )
        cls.record = cls.env["odental.clinical.record"].create(
            {"patient_id": cls.patient.id}
        )
        cls.tooth_11 = cls.env.ref("odental_diagnostics.tooth_11")

    def test_signed_odontogram_is_immutable(self):
        chart = self.env["odental.odontogram"].create(
            {
                "clinical_record_id": self.record.id,
                "professional_id": self.professional.id,
                "dentition": "permanent",
                "finding_ids": [
                    (
                        0,
                        0,
                        {
                            "tooth_id": self.tooth_11.id,
                            "surface": "mesial",
                            "condition": "caries",
                            "status": "existing",
                        },
                    )
                ],
            }
        )
        chart.action_sign()
        self.assertEqual(chart.state, "signed")
        self.assertTrue(chart.content_hash)
        with self.assertRaises(UserError):
            chart.finding_ids.write({"notes": "Alteración"})

    def test_odontogram_amendment_copies_findings(self):
        chart = self.env["odental.odontogram"].create(
            {
                "clinical_record_id": self.record.id,
                "professional_id": self.professional.id,
                "finding_ids": [
                    (
                        0,
                        0,
                        {
                            "tooth_id": self.tooth_11.id,
                            "surface": "whole",
                            "condition": "healthy",
                            "status": "existing",
                        },
                    )
                ],
            }
        )
        chart.action_sign()
        action = chart.action_create_amendment()
        amendment = self.env["odental.odontogram"].browse(action["res_id"])
        self.assertEqual(amendment.version, 2)
        self.assertEqual(len(amendment.finding_ids), 1)
        amendment.amendment_reason = "Cambio clínico comprobado"
        amendment.action_sign()
        self.assertEqual(amendment.state, "signed")

    def test_primary_tooth_rejected_in_permanent_chart(self):
        tooth_51 = self.env.ref("odental_diagnostics.tooth_51")
        chart = self.env["odental.odontogram"].create(
            {
                "clinical_record_id": self.record.id,
                "professional_id": self.professional.id,
                "dentition": "permanent",
            }
        )
        with self.env.cr.savepoint(), self.assertRaises(ValidationError):
            self.env["odental.odontogram.finding"].create(
                {
                    "odontogram_id": chart.id,
                    "tooth_id": tooth_51.id,
                    "surface": "whole",
                    "condition": "healthy",
                }
            )

    def test_finalized_image_hash_and_immutability(self):
        content = b"O Dental clinical image test"
        image = self.env["odental.clinical.image"].create(
            {
                "clinical_record_id": self.record.id,
                "professional_id": self.professional.id,
                "category": "intraoral_photo",
                "modality": "PHOTO",
                "filename": "test.jpg",
                "file_data": base64.b64encode(content),
            }
        )
        self.assertEqual(image.file_size, len(content))
        self.assertTrue(image.file_hash)
        image.action_finalize()
        self.assertEqual(image.state, "final")
        with self.assertRaises(UserError):
            image.write({"notes": "Alteración posterior"})
