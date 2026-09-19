from datetime import datetime

from odoo.tests.common import TransactionCase


class TestODentalRental(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        manager_group = cls.env.ref("odental_core.group_odental_manager")
        if not cls.env.user.has_group("odental_core.group_odental_manager"):
            cls.env.user.write({"groups_id": [(4, manager_group.id)]})
        cls.provider = cls.env["odental.organization"].create({
            "name": "Centro dental compartido", "code": "CTR", "organization_type": "shared",
            "billing_mode": "centralized", "user_ids": [(4, cls.env.user.id)],
        })
        cls.renter = cls.env["odental.organization"].create({
            "name": "Clínica independiente", "code": "REN", "organization_type": "individual",
            "billing_mode": "independent", "user_ids": [(4, cls.env.user.id)],
        })
        cls.partner = cls.env["res.partner"].create({"name": "Dra. Arrendataria"})
        cls.professional = cls.env["odental.professional"].create({
            "name": "Dra. Arrendataria", "partner_id": cls.partner.id,
            "organization_ids": [(4, cls.renter.id)],
        })
        cls.patient = cls.env["odental.patient"].create({
            "name": "Paciente alquiler", "organization_id": cls.renter.id,
        })
        cls.service = cls.env["odental.service"].create({
            "name": "Consulta", "code": "CONS-ALQ", "organization_id": cls.renter.id,
            "duration_minutes": 60, "require_room": True,
        })
        cls.site = cls.env["odental.site"].create({
            "name": "Sede central", "organization_id": cls.provider.id,
            "shared_with_organization_ids": [(4, cls.renter.id)],
        })
        cls.product = cls.env["product.product"].create({
            "name": "Alquiler consultorio", "type": "service", "list_price": 100.0,
        })
        cls.standard_category = cls.env["odental.rental.category"].create({
            "name": "Consultorio estándar", "code": "STD", "tier": "standard",
            "organization_id": cls.provider.id,
        })
        cls.premium_category = cls.env["odental.rental.category"].create({
            "name": "Clínica premium", "code": "PREM", "tier": "premium",
            "organization_id": cls.provider.id,
        })
        cls.standard_room = cls.env["odental.resource"].create({
            "name": "Consultorio 1", "resource_type": "room", "organization_id": cls.provider.id,
            "site_id": cls.site.id, "is_rentable": True, "includes_chair": True,
            "rental_category_id": cls.standard_category.id,
            "shared_with_organization_ids": [(4, cls.renter.id)],
        })
        cls.premium_room = cls.env["odental.resource"].create({
            "name": "Clínica Dra. Jennifer", "resource_type": "room", "organization_id": cls.provider.id,
            "site_id": cls.site.id, "is_rentable": True, "includes_chair": True,
            "rental_category_id": cls.premium_category.id,
            "shared_with_organization_ids": [(4, cls.renter.id)],
        })
        cls.standard_rate = cls.env["odental.rental.rate"].create({
            "name": "Hora estándar", "organization_id": cls.provider.id,
            "category_id": cls.standard_category.id, "billing_basis": "hour",
            "price": 100.0, "minimum_minutes": 30, "increment_minutes": 30,
            "product_id": cls.product.id,
        })
        cls.premium_rate = cls.env["odental.rental.rate"].create({
            "name": "Hora premium", "organization_id": cls.provider.id,
            "category_id": cls.premium_category.id, "billing_basis": "hour",
            "price": 175.0, "minimum_minutes": 30, "increment_minutes": 30,
            "product_id": cls.product.id,
        })

    def _appointment(self, resource, hour, duration=60):
        return self.env["odental.appointment"].create({
            "organization_id": self.renter.id, "patient_id": self.patient.id,
            "professional_id": self.professional.id, "service_id": self.service.id,
            "site_id": self.site.id, "resource_ids": [(6, 0, [resource.id])],
            "start_datetime": datetime(2026, 10, 1, hour, 0), "duration_minutes": duration,
        })

    def test_cross_organization_booking_and_premium_rate(self):
        standard = self._appointment(self.standard_room, 8)
        premium = self._appointment(self.premium_room, 10)
        for appointment in standard | premium:
            appointment.action_schedule()
            appointment.action_confirm()
            appointment.action_start()
            appointment.action_done()
        self.assertEqual(standard.rental_booking_ids.amount_total, 100.0)
        self.assertEqual(premium.rental_booking_ids.amount_total, 175.0)
        self.assertEqual(premium.rental_booking_ids.state, "completed")

    def test_package_bonus_consumption_and_overage(self):
        package_type = self.env["odental.rental.package.type"].create({
            "name": "2 horas + 30 minutos", "organization_id": self.provider.id,
            "category_id": self.premium_category.id, "purchased_minutes": 120,
            "bonus_minutes": 30, "validity_days": 30, "price": 300.0,
            "product_id": self.product.id,
        })
        package = self.env["odental.rental.package"].create({
            "package_type_id": package_type.id, "renter_organization_id": self.renter.id,
            "professional_id": self.professional.id, "payment_reference": "PAGO-001",
        })
        package.action_activate()
        self.assertEqual(package.remaining_minutes, 150)
        appointment = self._appointment(self.premium_room, 12, duration=180)
        appointment.action_schedule()
        appointment.action_start()
        appointment.action_done()
        line = appointment.rental_booking_ids.line_ids
        self.assertEqual(line.covered_minutes, 150)
        self.assertEqual(line.overage_minutes, 30)
        self.assertEqual(line.amount_total, 87.5)
        self.assertEqual(package.remaining_minutes, 0)
        self.assertEqual(package.state, "exhausted")

    def test_expense_equal_allocation(self):
        second = self.env["odental.professional"].create({
            "name": "Dr. Segundo", "organization_ids": [(4, self.renter.id)],
        })
        expense = self.env["odental.shared.expense"].create({
            "description": "Alquiler mensual", "provider_organization_id": self.provider.id,
            "period_start": "2026-10-01", "period_end": "2026-10-31",
            "amount": 1000.0, "allocation_method": "equal",
            "line_ids": [(0, 0, {"professional_id": self.professional.id}),
                         (0, 0, {"professional_id": second.id})],
        })
        expense.action_calculate()
        self.assertEqual(expense.line_ids.mapped("allocated_amount"), [500.0, 500.0])
        expense.action_approve()
        self.assertEqual(expense.state, "approved")

    def test_package_quotation_remains_draft(self):
        if not self.env["product.pricelist"].search([
            ("currency_id", "=", self.provider.company_id.currency_id.id)
        ], limit=1):
            self.env["product.pricelist"].create({
                "name": "Tarifa alquiler", "currency_id": self.provider.company_id.currency_id.id,
            })
        package_type = self.env["odental.rental.package.type"].create({
            "name": "Cinco horas", "organization_id": self.provider.id,
            "category_id": self.standard_category.id, "purchased_minutes": 300,
            "validity_days": 30, "price": 450.0, "product_id": self.product.id,
        })
        package = self.env["odental.rental.package"].create({
            "package_type_id": package_type.id, "renter_organization_id": self.renter.id,
            "professional_id": self.professional.id,
        })
        action = package.action_create_quotation()
        order = self.env["sale.order"].browse(action["res_id"])
        self.assertEqual(order.state, "draft")
        self.assertEqual(order.odental_rental_package_id, package)

    def test_shared_location_does_not_expose_provider_patients(self):
        user_group = self.env.ref("odental_core.group_odental_user")
        renter_user = self.env["res.users"].create({
            "name": "Agenda arrendataria", "login": "agenda.renter@test.invalid",
            "groups_id": [(6, 0, [user_group.id])],
            "company_id": self.env.company.id, "company_ids": [(6, 0, [self.env.company.id])],
        })
        self.renter.with_context(active_test=False).write({"user_ids": [(4, renter_user.id)]})
        provider_patient = self.env["odental.patient"].create({
            "name": "Paciente privado del centro", "organization_id": self.provider.id,
        })
        organizations = self.env["odental.organization"].with_user(renter_user).search([
            ("id", "=", self.provider.id)
        ])
        patients = self.env["odental.patient"].with_user(renter_user).search([
            ("id", "=", provider_patient.id)
        ])
        # Sharing a location grants access to its resources, not the provider's
        # organization record or private patient records.
        self.assertFalse(organizations)
        sites = self.env["odental.site"].with_user(renter_user).search([
            ("id", "=", self.site.id)
        ])
        resources = self.env["odental.resource"].with_user(renter_user).search([
            ("id", "in", (self.standard_room | self.premium_room).ids)
        ])
        self.assertEqual(sites, self.site)
        self.assertEqual(set(resources.ids), {self.standard_room.id, self.premium_room.id})
        self.assertFalse(patients)
