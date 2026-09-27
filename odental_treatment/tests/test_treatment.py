from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestODentalTreatment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.organization = cls.env["odental.organization"].create(
            {
                "name": "Clínica tratamientos",
                "code": "TRT",
                "billing_mode": "centralized",
                "user_ids": [(4, cls.env.user.id)],
            }
        )
        cls.professional = cls.env["odental.professional"].create(
            {
                "name": "Dra. Tratamientos",
                "organization_ids": [(4, cls.organization.id)],
            }
        )
        cls.patient = cls.env["odental.patient"].create(
            {"name": "Paciente tratamiento", "organization_id": cls.organization.id}
        )
        cls.record = cls.env["odental.clinical.record"].create(
            {"patient_id": cls.patient.id}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Restauración O Dental", "type": "service", "list_price": 1200.0}
        )
        cls.service = cls.env["odental.service"].create(
            {
                "name": "Restauración",
                "code": "REST",
                "organization_id": cls.organization.id,
                "product_id": cls.product.id,
                "price_unit": 1200.0,
            }
        )

    def _new_plan(self):
        return self.env["odental.treatment.plan"].create(
            {
                "clinical_record_id": self.record.id,
                "responsible_professional_id": self.professional.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "service_id": self.service.id,
                            "quantity": 2,
                            "price_unit": 1200.0,
                            "discount": 10.0,
                        },
                    )
                ],
            }
        )

    def test_amount_approval_hash_and_immutability(self):
        plan = self._new_plan()
        self.assertEqual(plan.amount_untaxed, 2160.0)
        plan.action_offer()
        plan.write(
            {
                "signer_name": "Paciente tratamiento",
                "acceptance_method": "secure_portal",
                "acceptance_reference": "approval-event-001",
            }
        )
        plan.action_approve()
        self.assertEqual(plan.state, "approved")
        self.assertTrue(plan.content_hash)
        with self.assertRaises(UserError):
            plan.line_ids.write({"price_unit": 1.0})

    def test_service_creates_and_updates_billing_product_automatically(self):
        service = self.env["odental.service"].create(
            {
                "name": "Consulta automática",
                "code": "AUTO-CONS",
                "organization_id": self.organization.id,
                "price_unit": 850.0,
            }
        )
        self.assertTrue(service.product_id)
        self.assertTrue(service.product_auto_created)
        self.assertEqual(service.product_id.type, "service")
        self.assertTrue(service.product_id.sale_ok)
        self.assertFalse(service.product_id.purchase_ok)
        self.assertEqual(service.product_id.lst_price, 850.0)
        service.write({"name": "Consulta automática actualizada", "price_unit": 900.0})
        self.assertEqual(service.product_id.name, "Consulta automática actualizada")
        self.assertEqual(service.product_id.lst_price, 900.0)

    def test_approval_requires_verifiable_evidence(self):
        plan = self._new_plan()
        plan.action_offer()
        plan.write(
            {
                "signer_name": "Paciente tratamiento",
                "acceptance_method": "secure_portal",
            }
        )
        with self.assertRaises(ValidationError):
            plan.action_approve()

    def test_approval_fingerprint_includes_fdi_tooth(self):
        plan = self._new_plan()
        tooth = self.env["odental.tooth"].search([("code", "=", "11")], limit=1)
        self.assertTrue(tooth)
        initial_hash = plan._hash_payload()
        plan.line_ids.tooth_id = tooth
        self.assertEqual(plan.line_ids._snapshot_values()["tooth"], "11")
        self.assertNotEqual(plan._hash_payload(), initial_hash)
        plan.action_offer()
        plan.write({
            "signer_name": "Paciente tratamiento",
            "acceptance_method": "in_person",
            "acceptance_reference": "tooth-approval-001",
        })
        plan.action_approve()
        self.assertEqual(plan.state, "approved")
        self.assertEqual(plan.content_hash, plan._hash_payload())

    def test_revision_preserves_approved_version(self):
        plan = self._new_plan()
        plan.action_offer()
        plan.write(
            {
                "signer_name": "Paciente tratamiento",
                "acceptance_method": "in_person",
                "acceptance_reference": "desk-event-001",
            }
        )
        plan.action_approve()
        plan.revision_reason = "Paciente solicita una alternativa"
        action = plan.action_create_revision()
        revision = self.env["odental.treatment.plan"].browse(action["res_id"])
        self.assertEqual(plan.state, "superseded")
        self.assertEqual(revision.state, "draft")
        self.assertEqual(revision.version, 2)
        self.assertEqual(revision.previous_version_id, plan)
        self.assertEqual(len(revision.line_ids), 1)
        self.assertEqual(revision.amount_total, plan.amount_total)

    def test_create_draft_quotation_from_approved_plan(self):
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            self.env.user.write(
                {"groups_id": [(4, self.env.ref("odental_core.group_odental_manager").id)]}
            )
        if not self.env["product.pricelist"].search(
            [("currency_id", "=", self.organization.company_id.currency_id.id)], limit=1
        ):
            self.env["product.pricelist"].create(
                {
                    "name": "Tarifa O Dental",
                    "currency_id": self.organization.company_id.currency_id.id,
                }
            )
        plan = self._new_plan()
        plan.action_offer()
        plan.write(
            {
                "signer_name": "Paciente tratamiento",
                "acceptance_method": "email_otp",
                "acceptance_reference": "email-event-001",
            }
        )
        plan.action_approve()
        action = plan.action_create_quotation()
        order = self.env["sale.order"].browse(action["res_id"])
        self.assertEqual(order.state, "draft")
        self.assertEqual(order.odental_treatment_plan_id, plan)
        self.assertEqual(plan.sale_order_id, order)
        self.assertEqual(len(order.order_line), 1)

    def _approved(self):
        plan = self._new_plan()
        plan.action_offer()
        plan.write({'signer_name': 'Synthetic patient', 'acceptance_method': 'in_person',
                    'acceptance_reference': 'synthetic-approval'})
        plan.action_approve()
        return plan

    def test_context_does_not_unlock_approved_plan(self):
        plan = self._approved()
        for vals in ({'terms': 'Changed after approval'}, {'state': 'draft'}, {'content_hash': 'fake'}):
            with self.assertRaises(UserError):
                plan.with_context(allow_treatment_transition=True).write(vals)

    def test_cannot_create_approved_plan_or_signature_metadata(self):
        values = {'clinical_record_id': self.record.id,
                  'responsible_professional_id': self.professional.id}
        plans = self.env['odental.treatment.plan']
        for extra in ({'state': 'approved'}, {'content_hash': 'fake'},
                      {'accepted_by_user_id': self.env.user.id}):
            with self.assertRaises(UserError):
                plans.create(dict(values, **extra))
            with self.assertRaises(UserError):
                plans.with_context(**{'default_' + k: v for k, v in extra.items()}).create(values)

    def test_default_parent_cannot_add_to_approved_plan(self):
        plan = self._approved()
        with self.assertRaises(UserError):
            self.env['odental.treatment.plan.line'].with_context(default_plan_id=plan.id).create({
                'service_id': self.service.id, 'quantity': 1, 'price_unit': 500})

    def test_cannot_move_draft_line_into_approved_plan(self):
        approved = self._approved()
        draft = self._new_plan()
        with self.assertRaises(UserError):
            draft.line_ids.write({'plan_id': approved.id})

    def test_auto_product_flag_cannot_be_forged(self):
        with self.assertRaises(UserError):
            self.service.with_context(skip_odental_product_sync=True).write({'product_auto_created': True})
        with self.assertRaises(UserError):
            self.env['odental.service'].with_context(default_product_auto_created=True).create({
                'name': 'Synthetic forged product owner', 'code': 'FORGED',
                'organization_id': self.organization.id, 'product_id': self.product.id})

    def test_new_billing_contact_is_company_scoped(self):
        partner = self._new_plan()._ensure_invoice_partner()
        self.assertEqual(partner.company_id, self.organization.company_id)
