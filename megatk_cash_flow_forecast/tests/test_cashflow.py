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

    def test_other_income_is_separate_and_increases_projection(self):
        income = self.env["cashflow.manual.income"].create({
            "plan_id": self.plan.id,
            "name": "Préstamo para capital de trabajo",
            "income_type": "loan",
            "counterparty_name": "Persona que no existe en Odoo",
            "period": "week_1",
            "amount": 500,
        })
        self.assertFalse(income.partner_id)
        self.assertEqual(income.company_amount, 500)
        self.assertEqual(self.plan.total_expected_receivable, 0)
        self.assertEqual(self.plan.total_expected_financing, 500)
        self.assertEqual(self.plan.total_other_income, 0)
        self.assertEqual(self.plan.financing_week_1, 500)
        self.assertEqual(self.plan.projected_week_1, 500)

    def test_projected_financing_does_not_require_accounting_entry(self):
        financing = self.env["cashflow.manual.income"].create({
            "plan_id": self.plan.id,
            "name": "Préstamo solicitado sin desembolso",
            "income_type": "loan",
            "counterparty_name": "Banco de prueba",
            "state": "requested",
            "period": "week_3",
            "amount": 1000000,
        })
        self.assertFalse(financing.source_move_id)
        self.assertFalse(financing.destination_journal_id)
        self.assertEqual(self.plan.financing_week_3, 1000000)
        self.assertEqual(self.plan.projected_week_1, 0)
        self.assertEqual(self.plan.projected_week_2, 0)
        self.assertEqual(self.plan.projected_week_3, 1000000)

    def test_received_financing_is_not_counted_twice(self):
        financing = self.env["cashflow.manual.income"].create({
            "plan_id": self.plan.id,
            "name": "Préstamo desembolsado",
            "income_type": "loan",
            "state": "confirmed",
            "period": "week_1",
            "amount": 1000,
        })
        self.assertEqual(self.plan.financing_week_1, 1000)
        financing.state = "received"
        self.assertEqual(self.plan.financing_week_1, 0)
        self.assertEqual(self.plan.total_expected_financing, 0)

    def test_bank_cash_and_new_financing_build_weekly_available_cash(self):
        liquidity_account = self.env["account.account"].search([
            ("account_type", "=", "asset_cash"),
            ("company_ids", "in", self.company.id),
        ], limit=1)
        if not liquidity_account:
            self.skipTest("La compañía de prueba no tiene una cuenta de liquidez.")
        self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "account_id": liquidity_account.id,
            "real_balance": 1000000,
        })
        for values in (
            {
                "name": "Efectivo recibido de tarjeta",
                "income_type": "credit_card_draw",
                "period": "week_1",
                "amount": 100000,
            },
            {
                "name": "Préstamo nuevo por recibir",
                "income_type": "loan",
                "period": "week_1",
                "amount": 1000000,
            },
        ):
            self.env["cashflow.manual.income"].create({
                "plan_id": self.plan.id,
                **values,
            })
        self.assertEqual(self.plan.total_real_available, 1000000)
        self.assertEqual(self.plan.financing_week_1, 1100000)
        self.assertEqual(self.plan.projected_week_1, 2100000)

    def test_credit_card_and_loan_do_not_reduce_available_cash(self):
        liquidity_account = self.env["account.account"].search([
            ("account_type", "=", "asset_cash"),
            ("company_ids", "in", self.company.id),
        ], limit=1)
        liability_account = self.env["account.account"].search([
            ("account_type", "in", ("liability_credit_card", "liability_current", "liability_payable")),
            ("company_ids", "in", self.company.id),
        ], limit=1)
        if not liquidity_account or not liability_account:
            self.skipTest("La compañía de prueba no tiene cuentas de liquidez y pasivo.")
        self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "account_id": liquidity_account.id,
            "real_balance": 1000,
        })
        self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "credit_card",
            "account_id": liability_account.id,
            "real_balance": 400,
        })
        self.assertEqual(self.plan.total_real_available, 1000)
        self.assertEqual(self.plan.projected_balance, 1000)

    def test_existing_bank_position_does_not_flag_itself_as_duplicate(self):
        journal = self.env["account.journal"].search([
            ("type", "in", ("bank", "cash")),
            ("company_id", "=", self.company.id),
        ], limit=1)
        if not journal:
            self.skipTest("La compañía de prueba no tiene un diario bancario o de efectivo.")
        position = self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": journal.id,
            "real_balance": 100,
        })
        editable_position = self.env["cashflow.bank.position"].new({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": journal.id,
            "real_balance": 100,
        }, origin=position)

        warning = editable_position._onchange_prevent_duplicate_source()

        self.assertFalse(warning)
        self.assertEqual(editable_position.journal_id, journal)

    def test_new_bank_position_does_not_compare_against_virtual_rows(self):
        journal = self.env["account.journal"].search([
            ("type", "in", ("bank", "cash")),
            ("company_id", "=", self.company.id),
        ], limit=1)
        if not journal:
            self.skipTest("La compañía de prueba no tiene un diario bancario o de efectivo.")
        new_position = self.env["cashflow.bank.position"].new({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": journal.id,
            "real_balance": 100,
        })

        warning = new_position._onchange_prevent_duplicate_source()

        self.assertFalse(warning)
        self.assertEqual(new_position.journal_id, journal)

    def test_new_bank_position_warns_for_a_persisted_duplicate(self):
        journal = self.env["account.journal"].search([
            ("type", "in", ("bank", "cash")),
            ("company_id", "=", self.company.id),
        ], limit=1)
        if not journal:
            self.skipTest("La compañía de prueba no tiene un diario bancario o de efectivo.")
        self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": journal.id,
            "real_balance": 100,
        })
        duplicate = self.env["cashflow.bank.position"].new({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": journal.id,
            "real_balance": 200,
        })

        warning = duplicate._onchange_prevent_duplicate_source()

        self.assertEqual(warning["warning"]["title"], "Diario ya agregado")
        self.assertFalse(duplicate.journal_id)

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
        with self.assertRaises(ValidationError):
            self.env["cashflow.manual.income"].create({
                "plan_id": self.plan.id, "name": "Inválido",
                "period": "week_1", "amount": 0,
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
        self.assertEqual(expense.classification, "other")
        self.assertEqual(self.plan.payable_week_1, 250)

    def test_manual_expense_classification_is_required_and_selectable(self):
        expense = self.env["cashflow.manual.expense"].create({
            "plan_id": self.plan.id,
            "name": "Planilla quincenal",
            "classification": "payroll",
            "period": "week_2",
            "amount": 1000,
            "recurring": True,
        })
        self.assertEqual(expense.classification, "payroll")

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

    def test_list_header_actions_accept_odoo_web_arguments(self):
        snapshots = self.env["cashflow.portfolio.snapshot"]
        refresh_action = snapshots.action_refresh_current_company([])
        self.assertEqual(refresh_action["tag"], "reload")
        with self.assertRaises(UserError):
            snapshots.action_print_current_company([])
