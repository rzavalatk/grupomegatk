from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestODentalBilling(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.write(
            {"groups_id": [(4, cls.env.ref("odental_core.group_odental_manager").id)]}
        )
        cls.organization = cls.env["odental.organization"].create(
            {
                "name": "Clínica caja",
                "code": "CAJA",
                "billing_mode": "centralized",
                "require_hn_fiscal_control": True,
                "user_ids": [(4, cls.env.user.id)],
            }
        )
        cls.site = cls.env["odental.site"].create(
            {"name": "Sede fiscal", "organization_id": cls.organization.id}
        )
        cls.professional = cls.env["odental.professional"].create(
            {
                "name": "Dra. Caja",
                "organization_ids": [(4, cls.organization.id)],
            }
        )
        cls.patient = cls.env["odental.patient"].create(
            {"name": "Paciente caja", "organization_id": cls.organization.id}
        )
        cls.record = cls.env["odental.clinical.record"].create(
            {"patient_id": cls.patient.id}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Servicio de caja", "type": "service", "list_price": 500.0}
        )
        cls.service = cls.env["odental.service"].create(
            {
                "name": "Servicio de caja",
                "code": "CAJA-SRV",
                "organization_id": cls.organization.id,
                "product_id": cls.product.id,
                "price_unit": 500.0,
            }
        )
        cls.sale_journal = cls.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", cls.organization.company_id.id)],
            limit=1,
        )

    def _authorization(self, **overrides):
        today = fields.Date.context_today(self.env.user)
        values = {
            "name": "CAI pruebas",
            "organization_id": self.organization.id,
            "company_id": self.organization.company_id.id,
            "site_id": self.site.id,
            "journal_id": self.sale_journal.id,
            "cai": "TEST-CAI-ISSUED-BY-SAR",
            "document_type": "01",
            "establishment_code": "000",
            "emission_point_code": "001",
            "range_start": 1,
            "range_end": 2,
            "next_number": 1,
            "date_from": today - timedelta(days=1),
            "date_limit": today + timedelta(days=30),
        }
        values.update(overrides)
        return self.env["odental.fiscal.authorization"].create(values)

    def _approved_plan(self):
        plan = self.env["odental.treatment.plan"].create(
            {
                "clinical_record_id": self.record.id,
                "responsible_professional_id": self.professional.id,
                "billing_site_id": self.site.id,
                "line_ids": [
                    (0, 0, {"service_id": self.service.id, "quantity": 1, "price_unit": 500})
                ],
            }
        )
        plan.action_offer()
        plan.write(
            {
                "signer_name": self.patient.name,
                "acceptance_method": "in_person",
                "acceptance_reference": "billing-test-approval",
            }
        )
        plan.action_approve()
        return plan

    def test_fiscal_range_allocates_once_and_exhausts(self):
        authorization = self._authorization()
        authorization.action_activate()
        self.assertEqual(authorization._allocate_number(), "000-001-01-00000001")
        self.assertEqual(authorization._allocate_number(), "000-001-01-00000002")
        self.assertEqual(authorization.state, "exhausted")
        with self.assertRaises(ValidationError):
            authorization._allocate_number()

    def test_active_authorization_is_immutable(self):
        authorization = self._authorization()
        authorization.action_activate()
        with self.assertRaises(UserError):
            authorization.write({"cai": "CHANGED"})

    def test_expired_authorization_cannot_activate(self):
        today = fields.Date.context_today(self.env.user)
        authorization = self._authorization(
            date_from=today - timedelta(days=30),
            date_limit=today - timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            authorization.action_activate()

    def test_cash_session_lifecycle_and_immutability(self):
        session = self.env["odental.cash.session"].create(
            {
                "organization_id": self.organization.id,
                "company_id": self.organization.company_id.id,
                "site_id": self.site.id,
                "opening_amount": 100,
            }
        )
        session.action_open()
        self.assertEqual(session.state, "open")
        with self.assertRaises(UserError):
            session.write({"opening_amount": 50})
        session.actual_closing_amount = 100
        session.action_close()
        self.assertEqual(session.state, "closed")
        self.assertEqual(session.difference_amount, 0)

    def test_plan_creates_draft_invoice_without_consuming_range(self):
        authorization = self._authorization()
        authorization.action_activate()
        plan = self._approved_plan()
        action = plan.action_create_invoice()
        invoice = self.env["account.move"].browse(action["res_id"])
        self.assertEqual(invoice.state, "draft")
        self.assertEqual(invoice.odental_treatment_plan_id, plan)
        self.assertEqual(invoice.odental_fiscal_authorization_id, authorization)
        self.assertFalse(invoice.odental_fiscal_number)
        self.assertEqual(authorization.next_number, 1)
