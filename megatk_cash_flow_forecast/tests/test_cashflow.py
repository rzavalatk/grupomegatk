from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestCashflowForecast(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.plan = self.env["cashflow.plan"].create({"company_id": self.company.id})
        self.partner = self.env["res.partner"].create({"name": "Cliente de prueba flujo"})

    def test_period_totals_include_manual_expense(self):
        self.env["cashflow.promise"].create({
            "plan_id": self.plan.id, "partner_id": self.partner.id,
            "direction": "receivable", "period": "week_1", "amount": 100,
        })
        self.env["cashflow.promise"].create({
            "plan_id": self.plan.id, "partner_id": self.partner.id,
            "direction": "payable", "period": "week_2", "amount": 40,
        })
        self.env["cashflow.manual.expense"].create({
            "plan_id": self.plan.id, "name": "Planilla", "period": "week_2", "amount": 60, "recurring": True,
        })
        self.assertEqual(self.plan.receivable_week_1, 100)
        self.assertEqual(self.plan.payable_week_2, 100)
        self.assertEqual(self.plan.total_expected_receivable, 100)
        self.assertEqual(self.plan.total_expected_payable, 100)
        self.assertEqual(self.plan.projected_week_1, 100)
        self.assertEqual(self.plan.projected_week_2, 0)

    def test_cancelled_promise_is_excluded_from_projection(self):
        promise = self.env["cashflow.promise"].create({
            "plan_id": self.plan.id, "partner_id": self.partner.id,
            "direction": "receivable", "period": "week_1", "amount": 100,
        })
        promise.action_cancel()
        self.assertEqual(promise.state, "cancelled")
        self.assertEqual(self.plan.total_expected_receivable, 0)

    def test_projection_amounts_must_be_positive(self):
        with self.assertRaises(ValidationError):
            self.env["cashflow.promise"].create({
                "plan_id": self.plan.id, "partner_id": self.partner.id,
                "direction": "receivable", "period": "week_1", "amount": 0,
            })
        with self.assertRaises(ValidationError):
            self.env["cashflow.manual.expense"].create({
                "plan_id": self.plan.id, "name": "Inválido",
                "period": "week_1", "amount": -1,
            })

    def test_management_note_updates_projected_collection_latest_note(self):
        promise = self.env["cashflow.promise"].create({
            "plan_id": self.plan.id, "partner_id": self.partner.id,
            "direction": "receivable", "period": "week_2", "amount": 100,
        })
        self.env["cashflow.management.note"].create({
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "promise_id": promise.id,
            "note": "Confirmó que pagará el lunes.",
        })
        self.assertEqual(promise.note, "Confirmó que pagará el lunes.")
        self.assertTrue(
            self.partner.message_ids.filtered(
                lambda message: "Confirmó que pagará el lunes" in (message.body or "")
            )
        )

    def test_projected_collection_opens_prefilled_management_and_history(self):
        promise = self.env["cashflow.promise"].create({
            "plan_id": self.plan.id, "partner_id": self.partner.id,
            "direction": "receivable", "period": "week_2", "amount": 100,
        })
        add_action = promise.action_add_management_note()
        history_action = promise.action_open_management_history()
        self.assertEqual(add_action["context"]["default_promise_id"], promise.id)
        self.assertEqual(add_action["context"]["default_partner_id"], self.partner.id)
        self.assertIn(("partner_id", "=", self.partner.id), history_action["domain"])

    def test_management_note_uses_commercial_partner(self):
        child = self.env["res.partner"].create({
            "name": "Sucursal de cobros",
            "parent_id": self.partner.id,
            "type": "invoice",
        })
        note = self.env["cashflow.management.note"].create({
            "company_id": self.company.id,
            "partner_id": child.id,
            "note": "Se contactó a la sucursal.",
        })
        self.assertEqual(note.partner_id, self.partner.commercial_partner_id)

    def test_management_note_updates_portfolio_detail_immediately(self):
        snapshot = self.env["cashflow.portfolio.snapshot"].create({
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "direction": "receivable",
            "classification": "customer",
        })
        self.env["cashflow.management.note"].create({
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "note": "Se envió un mensaje nuevo.",
            "next_action_date": "2026-10-01",
        })
        self.assertEqual(snapshot.last_management, "Se envió un mensaje nuevo.")
        self.assertTrue(snapshot.last_management_at)
        self.assertEqual(str(snapshot.next_action_date), "2026-10-01")

    def test_classification_is_company_specific(self):
        classification = self.env["cashflow.portfolio.classification"].create({
            "company_id": self.company.id, "partner_id": self.partner.id,
            "direction": "receivable", "classification": "legal",
        })
        self.assertEqual(classification.classification, "legal")

    def test_classification_must_match_account_direction(self):
        with self.assertRaises(ValidationError):
            self.env["cashflow.portfolio.classification"].create({
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "direction": "receivable",
                "classification": "supplier",
            })

    def test_classification_uses_commercial_partner(self):
        child = self.env["res.partner"].create({
            "name": "Sucursal del cliente",
            "parent_id": self.partner.id,
            "type": "invoice",
        })
        classification = self.env["cashflow.portfolio.classification"].create({
            "company_id": self.company.id,
            "partner_id": child.id,
            "direction": "receivable",
            "classification": "customer",
        })
        self.assertEqual(classification.partner_id, self.partner.commercial_partner_id)

    def test_current_plan_is_separate_for_each_company(self):
        other_company = self.env["res.company"].create({"name": "Otra empresa flujo"})
        other_plan = self.env["cashflow.plan"].with_company(other_company).get_or_create_current_plan()
        self.assertEqual(other_plan.company_id, other_company)
        self.assertNotEqual(other_plan, self.plan)

    def test_snapshot_classification_survives_refresh_source(self):
        snapshot = self.env["cashflow.portfolio.snapshot"].create({
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "direction": "receivable",
            "classification": "to_reconcile",
        })
        snapshot.write({"classification": "legal"})
        classification = self.env["cashflow.portfolio.classification"].search([
            ("company_id", "=", self.company.id),
            ("partner_id", "=", self.partner.id),
            ("direction", "=", "receivable"),
        ])
        self.assertEqual(classification.classification, "legal")

    def test_snapshot_accounting_values_are_read_only(self):
        snapshot = self.env["cashflow.portfolio.snapshot"].create({
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "direction": "receivable",
            "classification": "customer",
            "at_day": 100,
        })
        with self.assertRaises(UserError):
            snapshot.write({"at_day": 999})

    def test_manual_expense_uses_company_currency_amount(self):
        expense = self.env["cashflow.manual.expense"].create({
            "plan_id": self.plan.id,
            "name": "Alquiler",
            "period": "week_1",
            "currency_id": self.company.currency_id.id,
            "amount": 250,
            "recurring": True,
        })
        self.assertEqual(expense.company_amount, 250)
        self.assertEqual(self.plan.payable_week_1, 250)

    def test_snapshot_opens_prefilled_collection_management(self):
        snapshot = self.env["cashflow.portfolio.snapshot"].create({
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "direction": "receivable",
            "classification": "customer",
        })
        action = snapshot.action_add_management_note()
        self.assertEqual(action["res_model"], "cashflow.management.note")
        self.assertEqual(action["context"]["default_partner_id"], self.partner.id)
        self.assertEqual(action["context"]["default_company_id"], self.company.id)

    def test_snapshot_opens_prefilled_projection(self):
        snapshot = self.env["cashflow.portfolio.snapshot"].create({
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "direction": "receivable",
            "classification": "customer",
        })
        action = snapshot.action_schedule_promise()
        self.assertEqual(action["res_model"], "cashflow.promise")
        self.assertEqual(action["context"]["default_partner_id"], self.partner.id)
        self.assertEqual(action["context"]["default_direction"], "receivable")
        self.assertEqual(action["context"]["default_amount"], 0)

    def test_snapshot_projection_defaults_to_current_customer_balance(self):
        snapshot = self.env["cashflow.portfolio.snapshot"].create({
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "direction": "receivable",
            "classification": "employee_receivable",
            "days_1_30": 250,
        })
        action = snapshot.action_schedule_promise()
        self.assertEqual(action["context"]["default_amount"], 250)

    def test_refresh_one_customer_does_not_remove_other_customer(self):
        other = self.env["res.partner"].create({"name": "Otro cliente flujo"})
        self.env["cashflow.portfolio.snapshot"].create({
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "direction": "receivable",
            "classification": "customer",
        })
        other_snapshot = self.env["cashflow.portfolio.snapshot"].create({
            "company_id": self.company.id,
            "partner_id": other.id,
            "direction": "receivable",
            "classification": "customer",
        })
        self.env["cashflow.portfolio.snapshot"].refresh_partner(
            self.company, self.partner
        )
        self.assertTrue(other_snapshot.exists())

    def test_projection_week_badge_updates_without_portfolio_refresh(self):
        snapshot = self.env["cashflow.portfolio.snapshot"].create({
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "direction": "receivable",
            "classification": "customer",
        })
        promise = self.env["cashflow.promise"].create({
            "plan_id": self.plan.id,
            "partner_id": self.partner.id,
            "direction": "receivable",
            "period": "week_1",
            "amount": 100,
        })
        self.assertEqual(snapshot.projected_periods, "1")
        promise.write({"period": "week_2"})
        self.assertEqual(snapshot.projected_periods, "2")
        promise.action_cancel()
        self.assertFalse(snapshot.projected_periods)

    def test_partner_opens_integrated_receivable_and_payable_details(self):
        receivable_action = self.partner.action_cashflow_open_receivables()
        payable_action = self.partner.action_cashflow_open_payables()
        self.assertIn(("direction", "=", "receivable"), receivable_action["domain"])
        self.assertIn(("direction", "=", "payable"), payable_action["domain"])
        self.assertEqual(
            receivable_action["context"]["cashflow_report_direction"], "receivable"
        )
        self.assertEqual(
            payable_action["context"]["cashflow_report_direction"], "payable"
        )

    def test_partner_projection_button_opens_promises_not_management_notes(self):
        action = self.partner.action_cashflow_open_promises()
        self.assertEqual(action["res_model"], "cashflow.promise")
        self.assertIn(
            ("commercial_partner_id", "=", self.partner.commercial_partner_id.id),
            action["domain"],
        )

    def test_payables_screen_can_open_manual_or_recurring_expense(self):
        action = self.env[
            "cashflow.portfolio.snapshot"
        ].action_new_manual_expense()
        self.assertEqual(action["res_model"], "cashflow.manual.expense")
        self.assertEqual(action["context"]["default_plan_id"], self.plan.id)
        self.assertEqual(action["context"]["default_period"], "week_1")
