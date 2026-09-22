from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestODentalProfessional(TransactionCase):
    def _partner_compatible_values(self, **values):
        """Supply defaults required by optional Grupo Mega partner extensions."""
        if "autopost_bills" in self.env["res.partner"]._fields:
            values.setdefault("autopost_bills", False)
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
            "specialty": "Endodoncia",
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
