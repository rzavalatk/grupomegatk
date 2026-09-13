from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestODentalAppointment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.organization = cls.env["odental.organization"].create({
            "name": "Clínica de prueba", "code": "TEST", "user_ids": [(4, cls.env.user.id)]
        })
        cls.professional = cls.env["odental.professional"].create({
            "name": "Dra. Prueba", "user_id": cls.env.user.id,
            "organization_ids": [(4, cls.organization.id)]
        })
        cls.second_user = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Profesional de turno",
            "login": "professional.shift@test.invalid",
        })
        cls.supervisor_user = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Docente supervisor",
            "login": "supervisor.shift@test.invalid",
        })
        cls.organization.write({
            "user_ids": [(4, cls.second_user.id), (4, cls.supervisor_user.id)]
        })
        cls.second_professional = cls.env["odental.professional"].create({
            "name": "Dr. Segundo",
            "user_id": cls.second_user.id,
            "organization_ids": [(4, cls.organization.id)],
        })
        cls.supervisor_professional = cls.env["odental.professional"].create({
            "name": "Docente supervisor",
            "user_id": cls.supervisor_user.id,
            "organization_ids": [(4, cls.organization.id)],
        })
        cls.patient = cls.env["odental.patient"].create({
            "name": "Paciente prueba", "organization_id": cls.organization.id
        })
        cls.site = cls.env["odental.site"].create({
            "name": "Sede principal", "organization_id": cls.organization.id
        })
        cls.room = cls.env["odental.resource"].create({
            "name": "Consultorio 1", "resource_type": "room",
            "organization_id": cls.organization.id, "site_id": cls.site.id
        })
        cls.chair = cls.env["odental.resource"].create({
            "name": "Sillón 1", "resource_type": "chair",
            "organization_id": cls.organization.id, "site_id": cls.site.id
        })
        cls.second_room = cls.env["odental.resource"].create({
            "name": "Consultorio 2", "resource_type": "room", "includes_chair": True,
            "organization_id": cls.organization.id, "site_id": cls.site.id,
            "assignment_mode": "shift",
        })
        cls.service = cls.env["odental.service"].create({
            "name": "Evaluación", "code": "EVAL", "organization_id": cls.organization.id,
            "duration_minutes": 30, "preparation_minutes": 5, "cleaning_minutes": 10
        })

    def _appointment_values(self, start, professional=None, resources=None, participants=None):
        values = {
            "organization_id": self.organization.id,
            "patient_id": self.patient.id,
            "professional_id": (professional or self.professional).id,
            "service_id": self.service.id,
            "site_id": self.site.id,
            "resource_ids": [(6, 0, (resources or (self.room | self.chair)).ids)],
            "start_datetime": start,
            "state": "confirmed",
        }
        if participants:
            values["participant_line_ids"] = [
                (0, 0, {"user_id": user.id, "role": role})
                for user, role in participants
            ]
        return values

    def test_service_defaults_and_blocking_window(self):
        start = datetime(2026, 9, 14, 14, 0)
        appointment = self.env["odental.appointment"].create(self._appointment_values(start))
        self.assertEqual(appointment.end_datetime, start + timedelta(minutes=30))
        self.assertEqual(appointment.blocking_start, start - timedelta(minutes=5))
        self.assertEqual(appointment.blocking_end, start + timedelta(minutes=40))

    def test_prevent_professional_overlap(self):
        start = datetime(2026, 9, 14, 14, 0)
        self.env["odental.appointment"].create(self._appointment_values(start))
        with self.assertRaises(ValidationError):
            self.env["odental.appointment"].create(self._appointment_values(start + timedelta(minutes=35)))

    def test_allow_adjacent_appointment_after_cleaning(self):
        start = datetime(2026, 9, 14, 14, 0)
        self.env["odental.appointment"].create(self._appointment_values(start))
        second = self.env["odental.appointment"].create(self._appointment_values(start + timedelta(minutes=40)))
        self.assertTrue(second)

    def test_fixed_room_selects_professional_and_operator(self):
        fixed_room = self.env["odental.resource"].create({
            "name": "Clínica Dra. Jennifer Jovel",
            "resource_type": "room",
            "includes_chair": True,
            "organization_id": self.organization.id,
            "site_id": self.site.id,
            "assignment_mode": "fixed",
            "fixed_professional_id": self.professional.id,
        })
        values = self._appointment_values(datetime(2026, 9, 15, 8, 0), resources=fixed_room)
        values.pop("professional_id")
        appointment = self.env["odental.appointment"].create(values)
        self.assertEqual(appointment.professional_id, self.professional)
        self.assertEqual(appointment.participant_line_ids.user_id, self.env.user)
        self.assertEqual(appointment.participant_line_ids.role, "operator")

    def test_fixed_room_requires_professional(self):
        with self.assertRaises(ValidationError):
            self.env["odental.resource"].create({
                "name": "Consultorio fijo incompleto",
                "resource_type": "room",
                "organization_id": self.organization.id,
                "site_id": self.site.id,
                "assignment_mode": "fixed",
            })

    def test_operator_cannot_use_two_units_at_same_time(self):
        start = datetime(2026, 9, 16, 8, 0)
        self.env["odental.appointment"].create(
            self._appointment_values(
                start,
                participants=[(self.env.user, "operator")],
            )
        )
        with self.assertRaises(ValidationError):
            self.env["odental.appointment"].create(
                self._appointment_values(
                    start,
                    professional=self.second_professional,
                    resources=self.second_room,
                    participants=[(self.env.user, "operator")],
                )
            )

    def test_supervisor_can_cover_multiple_units(self):
        start = datetime(2026, 9, 17, 8, 0)
        self.env["odental.appointment"].create(
            self._appointment_values(
                start,
                professional=self.supervisor_professional,
                participants=[
                    (self.env.user, "operator"),
                    (self.supervisor_user, "supervisor"),
                ],
            )
        )
        second = self.env["odental.appointment"].create(
            self._appointment_values(
                start,
                professional=self.supervisor_professional,
                resources=self.second_room,
                participants=[
                    (self.second_user, "operator"),
                    (self.supervisor_user, "supervisor"),
                ],
            )
        )
        self.assertTrue(second)
