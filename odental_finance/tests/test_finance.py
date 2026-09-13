from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestODentalFinance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.organization = cls.env["odental.organization"].create({
            "name": "Clínica financiera", "code": "FIN",
            "user_ids": [(4, cls.env.user.id)],
        })
        cls.patient = cls.env["odental.patient"].create({
            "name": "Paciente financiero", "organization_id": cls.organization.id,
        })

    def test_installment_split_preserves_total(self):
        agreement = self.env["odental.payment.agreement"].create({
            "patient_id": self.patient.id,
            "company_id": self.organization.company_id.id,
            "installment_count": 3,
        })
        amounts = agreement._split_amount(1000, 3)
        self.assertEqual(len(amounts), 3)
        self.assertEqual(sum(amounts), 1000)

    def test_commission_percentage_is_bounded(self):
        with self.assertRaises(ValidationError):
            self.env["odental.commission.rule"].create({
                "name": "Inválida",
                "organization_id": self.organization.id,
                "company_id": self.organization.company_id.id,
                "percentage": 101,
            })

    def test_settlement_date_range_is_validated(self):
        with self.assertRaises(ValidationError):
            self.env["odental.commission.settlement"].create({
                "organization_id": self.organization.id,
                "company_id": self.organization.company_id.id,
                "date_from": "2026-09-30",
                "date_to": "2026-09-01",
            })
