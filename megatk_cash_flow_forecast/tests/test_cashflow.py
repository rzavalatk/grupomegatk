from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestCashflowForecast(TransactionCase):
    def setUp(self):
        super().setUp()
        # Staging uses a copy of the operational database.  Never delete or
        # reuse its real cash-flow plan in a test: create an isolated company
        # so balances and projections always start at zero.
        self.company = self.env["res.company"].create({
            "name": "Empresa aislada para pruebas de flujo",
        })
        self.plan = self.env["cashflow.plan"].with_company(self.company).create({
            "company_id": self.company.id,
        })
        self.partner = self.env["res.partner"].create({"name": "Cliente de prueba flujo"})

    def _account(self, code, account_type, currency=False):
        return self.env["account.account"].create({
            "name": f"Cuenta de prueba {code}",
            "code": code,
            "account_type": account_type,
            "company_ids": [(6, 0, [self.company.id])],
            "currency_id": currency.id if currency else False,
        })

    def _bank_journal(self, default_account, code="CFB"):
        return self.env["account.journal"].create({
            "name": f"Cheques de prueba {code}",
            "code": code,
            "type": "bank",
            "company_id": self.company.id,
            "default_account_id": default_account.id,
        })

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
        liquidity_account = self._account("CF1001", "asset_cash")
        card_account = self._account("CF2003", "liability_credit_card")
        self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "account_id": liquidity_account.id,
            "real_balance": 1000000,
        })
        card_position = self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "credit_card",
            "account_id": card_account.id,
            "real_balance": 0,
        })
        for values in (
            {
                "name": "Efectivo recibido de tarjeta",
                "income_type": "credit_card_draw",
                "liability_position_id": card_position.id,
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
        self.assertEqual(card_position.projected_debt, 100000)

    def test_credit_card_and_loan_do_not_reduce_available_cash(self):
        liquidity_account = self._account("CF1002", "asset_cash")
        liability_account = self._account("CF2001", "liability_credit_card")
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
        account = self._account("CF1003", "asset_cash")
        journal = self._bank_journal(account, "CF1")
        position = self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": journal.id,
            "account_id": account.id,
            "real_balance": 100,
        })
        editable_position = self.env["cashflow.bank.position"].new({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": journal.id,
            "account_id": account.id,
            "real_balance": 100,
        }, origin=position)

        warning = editable_position._onchange_prevent_duplicate_source()

        self.assertFalse(warning)
        self.assertEqual(editable_position.journal_id, journal)

    def test_same_journal_accepts_multiple_specific_accounts(self):
        first_account = self._account("CF1004", "asset_cash")
        second_account = self._account("CF1005", "asset_cash")
        journal = self._bank_journal(first_account, "CF2")
        first_position = self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": journal.id,
            "account_id": first_account.id,
            "real_balance": 100,
        })
        second_position = self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": journal.id,
            "account_id": second_account.id,
            "real_balance": 200,
        })

        self.assertEqual(first_position.journal_id, second_position.journal_id)
        self.assertEqual(len(self.plan.bank_position_ids), 2)
        self.assertEqual(self.plan.total_real_available, 300)

    def test_each_bank_position_reads_only_its_selected_account(self):
        first_account = self._account("CF1008", "asset_cash")
        second_account = self._account("CF1009", "asset_cash")
        counterpart = self._account("CF2004", "liability_current")
        bank_journal = self._bank_journal(first_account, "CF4")
        general_journal = self.env["account.journal"].create({
            "name": "Diario general de prueba flujo",
            "code": "CFG",
            "type": "general",
            "company_id": self.company.id,
        })
        move = self.env["account.move"].create({
            "company_id": self.company.id,
            "journal_id": general_journal.id,
            "date": "2026-09-29",
            "line_ids": [
                (0, 0, {"name": "Banco uno", "account_id": first_account.id, "debit": 100}),
                (0, 0, {"name": "Banco dos", "account_id": second_account.id, "debit": 200}),
                (0, 0, {"name": "Contrapartida", "account_id": counterpart.id, "credit": 300}),
            ],
        })
        move.action_post()
        first_position = self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": bank_journal.id,
            "account_id": first_account.id,
            "real_balance": 100,
        })
        second_position = self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": bank_journal.id,
            "account_id": second_account.id,
            "real_balance": 200,
        })

        self.assertEqual(first_position.accounting_balance, 100)
        self.assertEqual(second_position.accounting_balance, 200)

    def test_changing_the_journal_never_replaces_the_selected_account(self):
        first_account = self._account("CF1011", "asset_cash")
        second_account = self._account("CF1012", "asset_cash")
        first_journal = self._bank_journal(first_account, "CF5")
        second_journal = self._bank_journal(second_account, "CF6")
        position = self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": first_journal.id,
            "account_id": first_account.id,
            "real_balance": 0,
        })

        position.write({"journal_id": second_journal.id})

        self.assertEqual(position.account_id, first_account)

    def test_journal_alone_cannot_define_the_ledger_balance(self):
        account = self._account("CF1013", "asset_cash")
        journal = self._bank_journal(account, "CF7")

        with self.assertRaises(ValidationError):
            self.env["cashflow.bank.position"].create({
                "plan_id": self.plan.id,
                "position_type": "liquidity",
                "journal_id": journal.id,
                "real_balance": 0,
            })

    def test_ledger_balance_respects_the_selected_cutoff_date(self):
        bank_account = self._account("CF1010", "asset_cash")
        counterpart = self._account("CF2010", "liability_current")
        journal = self.env["account.journal"].create({
            "name": "Diario corte flujo",
            "code": "CFC",
            "type": "general",
            "company_id": self.company.id,
        })
        move = self.env["account.move"].create({
            "company_id": self.company.id,
            "journal_id": journal.id,
            "date": "2026-09-29",
            "line_ids": [
                (0, 0, {"name": "Banco", "account_id": bank_account.id, "debit": 100}),
                (0, 0, {"name": "Contrapartida", "account_id": counterpart.id, "credit": 100}),
            ],
        })
        move.action_post()
        position = self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "account_id": bank_account.id,
            "rate_date": "2026-09-28",
            "real_balance": 0,
        })

        self.assertEqual(position.accounting_balance, 0)
        position.rate_date = "2026-09-29"
        self.assertEqual(position.accounting_balance, 100)

    def test_new_bank_position_warns_only_for_a_persisted_account(self):
        account = self._account("CF1006", "asset_cash")
        journal = self._bank_journal(account, "CF3")
        self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": journal.id,
            "account_id": account.id,
            "real_balance": 100,
        })
        duplicate = self.env["cashflow.bank.position"].new({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "journal_id": journal.id,
            "account_id": account.id,
            "real_balance": 200,
        })

        warning = duplicate._onchange_prevent_duplicate_source()

        self.assertEqual(warning["warning"]["title"], "Cuenta ya agregada")
        self.assertFalse(duplicate.account_id)
        self.assertEqual(duplicate.journal_id, journal)

    def test_account_currency_is_converted_for_the_company_flow(self):
        usd = self.env.ref("base.USD")
        liquidity_account = self._account("CF1007", "asset_cash", currency=usd)
        position = self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "liquidity",
            "account_id": liquidity_account.id,
            "real_balance": 100,
        })

        expected = usd._convert(
            100, self.company.currency_id, self.company, position.rate_date
        )
        self.assertEqual(position.currency_id, usd)
        self.assertAlmostEqual(position.real_balance_company, expected, places=2)
        self.assertAlmostEqual(self.plan.total_real_available, expected, places=2)

    def test_direct_credit_card_supplier_payment_affects_debt_not_cash(self):
        card_account = self._account("CF2002", "liability_credit_card")
        card_position = self.env["cashflow.bank.position"].create({
            "plan_id": self.plan.id,
            "position_type": "credit_card",
            "account_id": card_account.id,
            "real_balance": 400,
        })
        self.env["cashflow.promise"].create({
            "plan_id": self.plan.id,
            "partner_id": self.partner.id,
            "direction": "payable",
            "payment_method": "credit_card",
            "funding_position_id": card_position.id,
            "period": "week_1",
            "amount": 100,
        })

        self.assertEqual(self.plan.payable_week_1, 0)
        self.assertEqual(self.plan.projected_week_1, 0)
        self.assertEqual(card_position.projected_debt, 500)

        self.env["cashflow.manual.expense"].create({
            "plan_id": self.plan.id,
            "name": "Pago de tarjeta",
            "classification": "credit_card_payment",
            "liability_position_id": card_position.id,
            "period": "week_2",
            "amount": 150,
        })
        self.assertEqual(self.plan.payable_week_2, 150)
        self.assertEqual(card_position.projected_debt, 350)

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

    def test_each_week_exposes_the_previous_projected_balance_as_opening(self):
        self.env["cashflow.manual.expense"].create({
            "plan_id": self.plan.id,
            "name": "Salida mayor que el disponible",
            "period": "week_1",
            "amount": 250,
        })
        self.env["cashflow.manual.income"].create({
            "plan_id": self.plan.id,
            "name": "Ingreso de semana dos",
            "income_type": "other",
            "period": "week_2",
            "amount": 50,
        })

        self.assertEqual(self.plan.opening_week_1, 0)
        self.assertEqual(self.plan.projected_week_1, -250)
        self.assertEqual(self.plan.opening_week_2, -250)
        self.assertEqual(self.plan.projected_week_2, -200)
        self.assertEqual(self.plan.opening_week_3, -200)
        self.assertEqual(self.plan.opening_pending, -200)

    def test_filtered_relations_do_not_mix_tabs(self):
        receivable = self.env["cashflow.promise"].create({
            "plan_id": self.plan.id,
            "partner_id": self.partner.id,
            "direction": "receivable",
            "period": "week_1",
            "amount": 100,
        })
        payable = self.env["cashflow.promise"].create({
            "plan_id": self.plan.id,
            "partner_id": self.partner.id,
            "direction": "payable",
            "period": "week_2",
            "amount": 200,
        })
        unique = self.env["cashflow.manual.expense"].create({
            "plan_id": self.plan.id,
            "name": "Pago único",
            "period": "week_1",
            "amount": 10,
            "recurring": False,
        })
        recurring = self.env["cashflow.manual.expense"].create({
            "plan_id": self.plan.id,
            "name": "Planilla",
            "reference": "Pago de planilla",
            "period": "week_2",
            "amount": 20,
            "recurring": True,
        })

        self.assertEqual(self.plan.receivable_promise_ids, receivable)
        self.assertEqual(self.plan.payable_promise_ids, payable)
        self.assertEqual(self.plan.unique_expense_ids, unique)
        self.assertEqual(self.plan.recurring_expense_ids, recurring)
        self.assertEqual(recurring.reference, "Pago de planilla")
        self.assertEqual(unique.payment_frequency, "unique")
        recurring.payment_frequency = "unique"
        recurring._inverse_payment_frequency()
        self.assertFalse(recurring.recurring)

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
