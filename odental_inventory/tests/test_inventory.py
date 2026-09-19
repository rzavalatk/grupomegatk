from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestODentalInventory(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        manager_group = cls.env.ref("odental_core.group_odental_manager")
        if not cls.env.user.has_group("odental_core.group_odental_manager"):
            cls.env.user.write({"groups_id": [(4, manager_group.id)]})
        cls.organization = cls.env["odental.organization"].create({
            "name": "Clínica inventario", "code": "INV", "user_ids": [(4, cls.env.user.id)],
        })
        cls.source = cls.env["stock.location"].create({
            "name": "Material clínico", "usage": "internal", "company_id": cls.env.company.id,
        })
        cls.destination = cls.env["stock.location"].create({
            "name": "Consumo odontológico", "usage": "inventory", "company_id": cls.env.company.id,
        })
        cls.picking_type = cls.env["stock.picking.type"].create({
            "name": "Consumo clínico de prueba",
            "code": "internal",
            "sequence_code": "ODENTAL-TEST",
            "company_id": cls.env.company.id,
            "default_location_src_id": cls.source.id,
            "default_location_dest_id": cls.destination.id,
        })
        cls.organization.write({
            "clinical_stock_location_id": cls.source.id,
            "clinical_consumption_location_id": cls.destination.id,
            "clinical_picking_type_id": cls.picking_type.id,
        })
        cls.professional = cls.env["odental.professional"].create({
            "name": "Dra. Inventario", "organization_ids": [(4, cls.organization.id)],
        })
        cls.patient = cls.env["odental.patient"].create({
            "name": "Paciente inventario", "organization_id": cls.organization.id,
        })
        cls.site = cls.env["odental.site"].create({
            "name": "Sede inventario", "organization_id": cls.organization.id,
        })
        cls.material = cls.env["product.product"].create({
            "name": "Guantes clínicos", "type": "consu",
        })
        cls.service = cls.env["odental.service"].create({
            "name": "Profilaxis", "code": "PROF-INV", "organization_id": cls.organization.id,
            "require_room": False, "require_chair": False,
            "material_template_ids": [(0, 0, {
                "product_id": cls.material.id, "quantity": 2,
                "product_uom_id": cls.material.uom_id.id, "mandatory": True,
            })],
        })

    def _appointment(self, hour=8, service=None):
        return self.env["odental.appointment"].create({
            "organization_id": self.organization.id, "patient_id": self.patient.id,
            "professional_id": self.professional.id, "service_id": (service or self.service).id,
            "site_id": self.site.id, "start_datetime": datetime(2026, 10, 5, hour, 0),
        })

    def test_finished_appointment_prepares_reviewable_consumption(self):
        appointment = self._appointment()
        appointment.action_schedule()
        appointment.action_start()
        appointment.action_done()
        consumption = appointment.material_consumption_ids
        self.assertEqual(consumption.state, "draft")
        self.assertEqual(consumption.line_ids.product_id, self.material)
        self.assertEqual(consumption.line_ids.quantity_planned, 2)
        self.assertEqual(consumption.line_ids.quantity_used, 2)
        consumption.action_ready()
        action = consumption.action_create_picking()
        picking = self.env["stock.picking"].browse(action["res_id"])
        self.assertNotEqual(picking.state, "done")
        self.assertEqual(picking.odental_consumption_id, consumption)
        self.assertEqual(consumption.state, "allocated")

    def test_expired_lot_is_rejected(self):
        tracked = self.env["product.product"].create({
            "name": "Anestésico trazable", "type": "consu", "tracking": "lot",
        })
        service = self.env["odental.service"].create({
            "name": "Tratamiento con anestesia", "code": "ANEST-INV",
            "organization_id": self.organization.id, "require_room": False, "require_chair": False,
            "material_template_ids": [(0, 0, {
                "product_id": tracked.id, "quantity": 1,
                "product_uom_id": tracked.uom_id.id,
            })],
        })
        lot = self.env["stock.lot"].create({
            "name": "LOTE-VENCIDO", "product_id": tracked.id, "company_id": self.env.company.id,
            "expiration_date": datetime.now() - timedelta(days=1),
        })
        appointment = self._appointment(hour=10, service=service)
        appointment.action_done()
        appointment.material_consumption_ids.line_ids.lot_id = lot
        with self.assertRaises(ValidationError):
            appointment.material_consumption_ids.action_ready()
