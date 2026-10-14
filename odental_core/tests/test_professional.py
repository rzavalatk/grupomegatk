from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestODentalProfessional(TransactionCase):
    def _partner_compatible_values(self, **values):
        """Supply defaults required by optional Grupo Mega partner extensions."""
        if "autopost_bills" in self.env["res.partner"]._fields:
            values.setdefault("autopost_bills", "never")
        return values

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.organization = cls.env["odental.organization"].create(
            {
                "name": "Clínica de profesionales",
                "code": "PROF-TEST",
                "user_ids": [(4, cls.env.user.id)],
            }
        )

    def _values(self, **overrides):
        values = {
            "first_name": "Jennifer",
            "middle_name": "María",
            "first_surname": "Jovel",
            "second_surname": "López",
            "specialty_ids": [(4, self.env.ref("odental_core.specialty_endodontics").id)],
            "organization_ids": [(4, self.organization.id)],
        }
        values.update(overrides)
        return values

    def test_structured_name_generates_legal_name_code_and_display(self):
        professional = self.env["odental.professional"].create(self._values())
        self.assertEqual(professional.name, "Jennifer María Jovel López")
        self.assertEqual(professional.professional_code, f"PRO-{professional.id:06d}")
        self.assertEqual(
            professional.display_name,
            "Jovel López, Jennifer María — Endodoncia",
        )

    def test_legacy_name_is_kept_and_split(self):
        professional = self.env["odental.professional"].create(
            {
                "name": "Jennifer Jovel",
                "organization_ids": [(4, self.organization.id)],
            }
        )
        self.assertEqual(professional.first_name, "Jennifer")
        self.assertEqual(professional.first_surname, "Jovel")
        self.assertEqual(professional.name, "Jennifer Jovel")

    def test_multiple_catalog_specialties_and_uncontrolled_text_rejected(self):
        specialties = self.env["odental.specialty"].browse([
            self.env.ref("odental_core.specialty_endodontics").id,
            self.env.ref("odental_core.specialty_orthodontics").id,
            self.env.ref("odental_core.specialty_periodontics").id,
        ])
        professional = self.env["odental.professional"].create(
            self._values(specialty_ids=[(6, 0, specialties.ids)])
        )
        self.assertEqual(set(professional.specialty_ids.ids), set(specialties.ids))
        self.assertIn("Ortodoncia", professional.display_name)
        with self.assertRaisesRegex(ValidationError, "catálogo clínico"):
            professional.write({"specialty": "Terrorista"})
        with self.assertRaisesRegex(ValidationError, "catálogo clínico"):
            self.env["odental.professional"].create(self._values(
                first_name="Ana", specialty="Terrorista"
            ))

    def test_specialty_must_belong_to_same_company(self):
        other = self.env["res.company"].search(
            [("id", "!=", self.env.company.id)], limit=1
        )
        if not other:
            self.skipTest("Se requiere una segunda compañía para probar el aislamiento")
        other_specialty = self.env["odental.specialty"].sudo().with_company(other).create({
            "name": "Especialidad propia de otra clínica", "company_id": other.id,
        })
        with self.assertRaisesRegex(ValidationError, "compañía"):
            self.env["odental.professional"].create(self._values(
                specialty_ids=[(4, other_specialty.id)]
            ))

    def test_clinic_report_counts_unique_doctors_and_each_specialty(self):
        endo = self.env.ref("odental_core.specialty_endodontics")
        ortho = self.env.ref("odental_core.specialty_orthodontics")
        first = self.env["odental.professional"].create(self._values(
            specialty_ids=[(6, 0, [endo.id, ortho.id])]
        ))
        self.env["odental.professional"].create(self._values(
            first_name="Ana", specialty_ids=[(4, endo.id)]
        ))
        self.env["odental.professional"].create(self._values(
            first_name="Elena", specialty_ids=[]
        ))
        self.env["odental.professional"].create(self._values(
            first_name="Inactiva", active=False, specialty_ids=[(4, ortho.id)]
        ))
        report = self.env["odental.specialty.report"].create({
            "organization_id": self.organization.id
        })
        report.action_generate()
        counts = {line.specialty_id.id: line.professional_count for line in report.line_ids}
        self.assertEqual(report.total_professionals, 3)
        self.assertEqual(report.without_specialty_count, 1)
        self.assertEqual(counts[endo.id], 2)
        self.assertEqual(counts[ortho.id], 1)
        action = report.line_ids.filtered(lambda line: line.specialty_id == ortho).action_open_professionals()
        self.assertEqual(
            self.env["odental.professional"].search(action["domain"]).ids, first.ids
        )

    def test_homonyms_are_distinguished_without_blocking_real_people(self):
        first = self.env["odental.professional"].create(
            self._values(license_number="COL-1234")
        )
        second = self.env["odental.professional"].create(
            self._values(license_number="COL-9876")
        )
        first._compute_display_name()
        second._compute_display_name()
        self.assertIn("colegiación …1234", first.display_name)
        self.assertIn("colegiación …9876", second.display_name)

    def test_duplicate_license_is_blocked_case_insensitively(self):
        self.env["odental.professional"].create(
            self._values(license_number="COL-1234")
        )
        with self.assertRaisesRegex(ValidationError, "colegiación"):
            self.env["odental.professional"].create(
                self._values(
                    first_name="Juana",
                    first_surname="Pérez",
                    license_number=" col-1234 ",
                )
            )

    def test_duplicate_user_and_contact_are_blocked(self):
        contact = self.env["res.partner"].create(
            self._partner_compatible_values(name="Jennifer Jovel")
        )
        self.env["odental.professional"].create(
            self._values(user_id=self.env.user.id, partner_id=contact.id)
        )
        with self.assertRaisesRegex(ValidationError, "usuario de Odoo"):
            self.env["odental.professional"].create(
                self._values(
                    first_name="Juana",
                    first_surname="Pérez",
                    user_id=self.env.user.id,
                )
            )
        with self.assertRaisesRegex(ValidationError, "contacto"):
            self.env["odental.professional"].create(
                self._values(
                    first_name="Juana",
                    first_surname="Pérez",
                    partner_id=contact.id,
                )
            )
