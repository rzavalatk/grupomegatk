from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestODentalLaboratory(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        manager_group = cls.env.ref("odental_core.group_odental_manager")
        if not cls.env.user.has_group("odental_core.group_odental_manager"):
            cls.env.user.write({"groups_id": [(4, manager_group.id)]})
        cls.organization = cls.env["odental.organization"].create({
            "name": "Clínica laboratorio", "code": "LAB", "user_ids": [(4, cls.env.user.id)],
        })
        cls.professional = cls.env["odental.professional"].create({
            "name": "Dra. Prótesis", "organization_ids": [(4, cls.organization.id)],
        })
        cls.patient = cls.env["odental.patient"].create({
            "name": "Paciente laboratorio", "organization_id": cls.organization.id,
        })
        cls.record = cls.env["odental.clinical.record"].create({"patient_id": cls.patient.id})
        cls.vendor = cls.env["res.partner"].create({"name": "Laboratorio Central"})
        cls.laboratory = cls.env["odental.laboratory"].create({
            "name": "Laboratorio Central", "organization_id": cls.organization.id,
            "partner_id": cls.vendor.id, "default_turnaround_days": 5,
        })
        cls.product = cls.env["product.product"].create({
            "name": "Servicio de corona", "type": "service", "list_price": 2500.0,
        })

    def _case(self):
        return self.env["odental.lab.case"].create({
            "clinical_record_id": self.record.id,
            "laboratory_id": self.laboratory.id,
            "responsible_professional_id": self.professional.id,
            "work_type": "crown", "material": "Zirconia", "shade": "A2",
            "instructions": "Corona individual con ajuste cervical.",
            "expected_return_date": "2026-10-15", "estimated_cost": 2500.0,
            "purchase_product_id": self.product.id,
        })

    def test_purchase_order_remains_draft(self):
        case = self._case()
        action = case.action_create_purchase_order()
        order = self.env["purchase.order"].browse(action["res_id"])
        self.assertEqual(order.state, "draft")
        self.assertEqual(order.odental_lab_case_id, case)
        self.assertEqual(case.purchase_order_id, order)

    def test_rework_keeps_immutable_timeline(self):
        case = self._case()
        case.action_send()
        case.action_receive()
        case.rework_reason = "El punto de contacto requiere corrección"
        case.action_rework()
        self.assertEqual(case.state, "rework")
        self.assertEqual(case.rework_count, 1)
        self.assertTrue(case.event_ids.filtered(lambda event: event.event_type == "rework"))
        case.action_send()
        case.action_receive()
        case.action_accept()
        self.assertEqual(case.state, "accepted")

    def test_case_rejects_laboratory_from_other_organization(self):
        other = self.env["odental.organization"].create({
            "name": "Otra clínica", "code": "LAB2", "user_ids": [(4, self.env.user.id)],
        })
        wrong_lab = self.env["odental.laboratory"].create({
            "name": "Laboratorio externo", "organization_id": other.id,
            "partner_id": self.vendor.id,
        })
        values = {
            "clinical_record_id": self.record.id, "laboratory_id": wrong_lab.id,
            "responsible_professional_id": self.professional.id,
            "work_type": "model", "instructions": "Modelo de estudio",
        }
        with self.assertRaises(ValidationError):
            self.env["odental.lab.case"].create(values)
