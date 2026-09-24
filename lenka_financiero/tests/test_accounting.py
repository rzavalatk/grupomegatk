from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestLenkaAccounting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente Contable Lenka'})
        cls.operation = cls.env['lenka.financial.operation'].create({
            'partner_id': cls.partner.id,
            'operation_type': 'loan',
            'principal_amount': 10000.0,
            'interest_rate': 3.0,
            'rate_period': 'monthly',
            'term_months': 12,
            'calculation_method': 'level',
            'is_quote': False,
            'state': 'approved',
        })
        cls.operation.action_generate_schedule()
        cls.operation.write({'contract_signed': True, 'state': 'contracted'})
        cls.env['lenka.funding.line'].create({
            'operation_id': cls.operation.id,
            'source_type': 'own',
            'reference': 'Fondeo contable de prueba',
            'amount': 10000.0,
            'cost_rate': 0.0,
            'cost_period': 'annual',
        })

    def test_disbursement_requires_accounting_configuration(self):
        disbursement = self.env['lenka.disbursement'].create({
            'operation_id': self.operation.id,
            'amount': 10000.0,
            'destination_type': 'client',
            'destination_partner_id': self.partner.id,
        })
        disbursement.action_post()
        with self.assertRaises(ValidationError):
            disbursement.action_create_account_move()

    def test_payment_requires_accounting_configuration(self):
        self.operation.state = 'active'
        payment = self.env['lenka.payment'].create({
            'operation_id': self.operation.id,
            'amount': 500.0,
            'payment_method': 'transfer',
        })
        payment.action_post()
        with self.assertRaises(ValidationError):
            payment.action_create_account_move()

    def test_existing_move_prevents_duplicate_creation(self):
        self._configure_accounting()
        self.operation.state = 'active'
        payment = self.env['lenka.payment'].create({
            'operation_id': self.operation.id,
            'amount': 500.0,
            'payment_method': 'transfer',
        })
        payment.action_post()
        payment.action_create_account_move()
        before = payment.move_id
        payment.action_create_account_move()
        self.assertEqual(payment.move_id, before)

    def _collection_with_draft_move(self):
        accounts = self.env['account.account'].create([
            {'name': 'Liquidez prueba Lenka', 'code': 'LNK9001', 'account_type': 'asset_current', 'company_ids': [(6, 0, [self.company.id])]},
            {'name': 'Cartera prueba Lenka', 'code': 'LNK9002', 'account_type': 'asset_current', 'company_ids': [(6, 0, [self.company.id])]},
            {'name': 'Intereses prueba Lenka', 'code': 'LNK9003', 'account_type': 'income', 'company_ids': [(6, 0, [self.company.id])]},
        ])
        journal = self.env['account.journal'].create({
            'name': 'Cobros prueba Lenka', 'code': 'LNKR', 'type': 'general',
            'company_id': self.company.id, 'default_account_id': accounts[0].id,
        })
        self.company.write({
            'lenka_collection_journal_id': journal.id,
            'lenka_portfolio_account_id': accounts[1].id,
            'lenka_interest_income_account_id': accounts[2].id,
            'lenka_late_fee_income_account_id': accounts[2].id,
        })
        self.operation.state = 'active'
        first = self.operation.schedule_line_ids.sorted('sequence')[0]
        payment = self.env['lenka.payment'].create({
            'operation_id': self.operation.id, 'payment_date': first.date,
            'amount': first.interest + 2000.0, 'payment_method': 'transfer',
        })
        payment.action_post()
        payment.action_create_account_move()
        return payment

    def test_cancel_collection_cancels_draft_move_and_restores_balance(self):
        payment = self._collection_with_draft_move()
        move = payment.move_id
        self.assertEqual(move.state, 'draft')
        payment.action_cancel()
        self.assertEqual(payment.state, 'cancelled')
        self.assertEqual(move.state, 'cancel')
        self.assertEqual(payment.move_id, move)
        self.assertAlmostEqual(self.operation.outstanding_capital, self.operation.financed_amount, places=2)
        payment.action_cancel()
        self.assertEqual(move.state, 'cancel')

    def test_cancelled_collection_move_cannot_be_reposted(self):
        payment = self._collection_with_draft_move()
        payment.action_cancel()
        payment.move_id.button_draft()
        with self.assertRaises(ValidationError):
            payment.move_id.action_post()
        self.assertEqual(payment.move_id.state, 'draft')
        self.assertEqual(payment.state, 'cancelled')

    def test_published_move_blocks_collection_cancellation(self):
        payment = self._collection_with_draft_move()
        payment.move_id.action_post()
        balance = self.operation.outstanding_capital
        with self.assertRaises(ValidationError):
            payment.action_cancel()
        self.assertEqual(payment.state, 'posted')
        self.assertEqual(payment.move_id.state, 'posted')
        self.assertAlmostEqual(self.operation.outstanding_capital, balance, places=2)

    def test_collection_move_link_cannot_be_changed(self):
        payment = self._collection_with_draft_move()
        replacement = payment.move_id.copy()
        for move_id in [False, replacement.id]:
            with self.subTest(move_id=move_id), self.assertRaises(ValidationError):
                payment.write({'move_id': move_id})
        with self.assertRaises(ValidationError):
            self.env['lenka.payment'].create({
                'operation_id': self.operation.id, 'amount': 100.0,
                'move_id': replacement.id,
            })

    def test_duplicate_collection_does_not_copy_account_move(self):
        payment = self._collection_with_draft_move()
        duplicate = payment.copy()
        self.assertEqual(duplicate.state, 'draft')
        self.assertFalse(duplicate.move_id)
        self.assertFalse(duplicate.allocation_line_ids)

    def test_unrelated_account_move_can_still_be_published(self):
        payment = self._collection_with_draft_move()
        unrelated = payment.move_id.copy()
        payment.action_cancel()
        unrelated.action_post()
        self.assertEqual(unrelated.state, 'posted')


    def _configure_accounting(self):
        journal = self.env['account.journal'].search([
            ('company_id', '=', self.company.id),
            ('type', '=', 'general'),
            ('default_account_id', '!=', False),
        ], limit=1)
        if not journal:
            journal = self.env['account.journal'].search([
                ('company_id', '=', self.company.id),
                ('default_account_id', '!=', False),
            ], limit=1)
        accounts = self.env['account.account'].search([
            ('company_ids', 'in', self.company.id),
        ], limit=5)
        if len(accounts) < 5:
            self.skipTest('La base de prueba no contiene suficientes cuentas contables.')
        self.company.write({
            'lenka_disbursement_journal_id': journal.id,
            'lenka_collection_journal_id': journal.id,
            'lenka_portfolio_account_id': accounts[0].id,
            'lenka_interest_income_account_id': accounts[1].id,
            'lenka_late_fee_income_account_id': accounts[2].id,
            'lenka_unapplied_account_id': accounts[3].id,
            'lenka_card_fee_expense_account_id': accounts[4].id,
        })
        return journal

    def test_disbursement_account_move_stays_draft(self):
        self._configure_accounting()
        disbursement = self.env['lenka.disbursement'].create({
            'operation_id': self.operation.id,
            'amount': 10000.0,
            'destination_type': 'client',
            'destination_partner_id': self.partner.id,
        })
        disbursement.action_post()
        disbursement.action_create_account_move()
        self.assertTrue(disbursement.move_id)
        self.assertEqual(disbursement.move_id.state, 'draft')

    def test_collection_account_move_stays_draft(self):
        self._configure_accounting()
        self.operation.state = 'active'
        first = self.operation.schedule_line_ids.sorted('sequence')[0]
        payment = self.env['lenka.payment'].create({
            'operation_id': self.operation.id,
            'payment_date': first.date,
            'amount': 500.0,
            'payment_method': 'transfer',
        })
        payment.action_post()
        payment.action_create_account_move()
        self.assertTrue(payment.move_id)
        self.assertEqual(payment.move_id.state, 'draft')

    def test_account_move_creation_is_idempotent(self):
        self._configure_accounting()
        self.operation.state = 'active'
        first = self.operation.schedule_line_ids.sorted('sequence')[0]
        payment = self.env['lenka.payment'].create({
            'operation_id': self.operation.id,
            'payment_date': first.date,
            'amount': 500.0,
            'payment_method': 'transfer',
        })
        payment.action_post()
        payment.action_create_account_move()
        first_move = payment.move_id
        payment.action_create_account_move()
        self.assertEqual(payment.move_id, first_move)


    def test_card_fee_is_booked_separately(self):
        self._configure_accounting()
        self.operation.state = 'active'
        first = self.operation.schedule_line_ids.sorted('sequence')[0]
        payment = self.env['lenka.payment'].create({
            'operation_id': self.operation.id,
            'payment_date': first.date,
            'amount': 1000.0,
            'payment_method': 'card',
            'card_fee_rate': 3.5,
        })
        payment.action_post()
        self.assertAlmostEqual(payment.card_fee_amount, 35.0, places=2)
        self.assertAlmostEqual(payment.net_bank_amount, 965.0, places=2)
        payment.action_create_account_move()
        move = payment.move_id
        fee_lines = move.line_ids.filtered(
            lambda line: line.account_id == self.company.lenka_card_fee_expense_account_id
        )
        self.assertEqual(len(fee_lines), 1)
        self.assertAlmostEqual(fee_lines.debit, 35.0, places=2)
        self.assertAlmostEqual(sum(move.line_ids.mapped('debit')), sum(move.line_ids.mapped('credit')), places=2)

    def test_card_fee_account_is_required_for_card_collection(self):
        self._configure_accounting()
        self.company.lenka_card_fee_expense_account_id = False
        self.operation.state = 'active'
        payment = self.env['lenka.payment'].create({
            'operation_id': self.operation.id,
            'amount': 1000.0,
            'payment_method': 'card',
            'card_fee_rate': 3.5,
        })
        payment.action_post()
        with self.assertRaises(ValidationError):
            payment.action_create_account_move()

    def _disbursement_with_draft_move(self):
        self._configure_accounting()
        disbursement = self.env['lenka.disbursement'].create({
            'operation_id': self.operation.id, 'amount': 10000.0,
            'destination_partner_id': self.partner.id,
        })
        disbursement.action_post()
        disbursement.action_create_account_move()
        return disbursement

    def test_cancel_disbursement_cancels_draft_move(self):
        disbursement = self._disbursement_with_draft_move()
        move = disbursement.move_id
        disbursement.action_cancel()
        self.assertEqual(disbursement.state, 'cancelled')
        self.assertEqual(move.state, 'cancel')
        self.assertEqual(self.operation.disbursed_amount, 0.0)
        disbursement.action_cancel()
        self.assertEqual(disbursement.move_id, move)

    def test_cancelled_disbursement_move_cannot_be_posted(self):
        disbursement = self._disbursement_with_draft_move()
        disbursement.action_cancel()
        disbursement.move_id.button_draft()
        with self.assertRaises(ValidationError):
            disbursement.move_id.action_post()
        self.assertEqual(disbursement.move_id.state, 'draft')

    def test_closed_operation_keeps_disbursement_and_move(self):
        disbursement = self._disbursement_with_draft_move()
        self.operation.state = 'done'
        with self.assertRaises(ValidationError):
            disbursement.action_cancel()
        self.assertEqual(disbursement.state, 'posted')
        self.assertEqual(disbursement.move_id.state, 'draft')

    def test_early_recalculation_keeps_accounted_interest_history(self):
        investment = self.env['lenka.investment'].create({
            'partner_id': self.partner.id, 'principal_amount': 10000.0,
            'passive_rate': 12.0, 'early_withdrawal_rate': 6.0,
            'start_date': '2025-01-15', 'term_months': 12,
        })
        investment.action_activate()
        from odoo import fields
        investment._generate_interest_until(fields.Date.to_date('2025-03-15'), 12.0)
        original = investment.interest_line_ids
        self._configure_investment_accounting()
        original[0].action_create_account_move()
        original_move = original[0].move_id
        with self.assertRaises(ValidationError):
            investment.action_recalculate_early_withdrawal(fields.Date.to_date('2025-03-15'))
        self.assertEqual(investment.interest_line_ids, original)
        self.assertEqual(original[0].move_id, original_move)

    def test_applied_disbursement_cannot_be_edited_or_deleted(self):
        disbursement = self._disbursement_with_draft_move()
        for vals in ({'amount': 5000.0}, {'date': '2025-01-01'},
                     {'funding_line_id': False}, {'destination_partner_id': False}):
            with self.assertRaises(ValidationError):
                disbursement.write(vals)
        with self.assertRaises(ValidationError):
            disbursement.unlink()
        self.assertEqual(self.operation.disbursed_amount, 10000.0)

    def test_disbursement_copy_is_unapplied_without_accounting(self):
        disbursement = self._disbursement_with_draft_move()
        duplicate = disbursement.copy()
        self.assertEqual(duplicate.state, 'draft')
        self.assertFalse(duplicate.move_id)
        self.assertNotEqual(duplicate.name, disbursement.name)
        self.assertEqual(self.operation.disbursed_amount, 10000.0)
        with self.assertRaises(ValidationError):
            duplicate.action_post()

    def test_disbursement_cannot_skip_validation_by_writing_state(self):
        model = self.env['lenka.disbursement']
        for state in ('posted', 'cancelled'):
            with self.assertRaises(ValidationError):
                model.create({'operation_id': self.operation.id, 'amount': 10000.0, 'state': state})
        draft = model.create({'operation_id': self.operation.id, 'amount': 10000.0})
        for state in ('posted', 'cancelled'):
            with self.assertRaises(ValidationError):
                draft.write({'state': state})
        draft.action_post()
        draft.action_post()
        self.assertEqual(self.operation.disbursed_amount, 10000.0)
        draft.action_cancel()
        with self.assertRaises(ValidationError):
            draft.write({'state': 'draft'})
        with self.assertRaises(ValidationError):
            draft.write({'amount': 5000.0})
        with self.assertRaises(ValidationError):
            draft.unlink()

    def test_disbursement_move_cannot_be_detached_or_injected(self):
        disbursement = self._disbursement_with_draft_move()
        with self.assertRaises(ValidationError):
            disbursement.move_id = False
        with self.assertRaises(ValidationError):
            self.env['lenka.disbursement'].create({
                'operation_id': self.operation.id, 'amount': 1000.0,
                'move_id': disbursement.move_id.id,
            })
        original = disbursement.move_id
        disbursement.action_create_account_move()
        self.assertEqual(disbursement.move_id, original)

    def test_mixed_disbursement_edit_does_not_change_draft(self):
        posted = self._disbursement_with_draft_move()
        draft = posted.copy()
        with self.assertRaises(ValidationError):
            (draft | posted).write({'amount': 5000.0})
        self.assertEqual(draft.amount, 10000.0)

    def test_draft_disbursement_can_be_corrected_and_deleted(self):
        draft = self.env['lenka.disbursement'].create({
            'operation_id': self.operation.id, 'amount': 1000.0,
        })
        draft.amount = 2000.0
        self.assertEqual(draft.amount, 2000.0)
        draft.unlink()
        self.assertFalse(draft.exists())

    def _configure_investment_accounting(self):
        accounts = self.env['account.account'].create([
            {'name': 'Liquidez inversiones prueba', 'code': 'LNI901', 'account_type': 'asset_current', 'company_ids': [(6, 0, self.company.ids)]},
            {'name': 'Obligacion inversiones prueba', 'code': 'LNI902', 'account_type': 'liability_current', 'company_ids': [(6, 0, self.company.ids)]},
            {'name': 'Intereses inversiones prueba', 'code': 'LNI903', 'account_type': 'expense', 'company_ids': [(6, 0, self.company.ids)]},
            {'name': 'Retenciones inversiones prueba', 'code': 'LNI904', 'account_type': 'liability_current', 'company_ids': [(6, 0, self.company.ids)]},
        ])
        journal = self.env['account.journal'].create({
            'name': 'Inversiones prueba historial', 'code': 'LNIH', 'type': 'general',
            'company_id': self.company.id, 'default_account_id': accounts[0].id,
        })
        self.company.write({
            'lenka_investment_journal_id': journal.id,
            'lenka_investor_liability_account_id': accounts[1].id,
            'lenka_passive_interest_expense_account_id': accounts[2].id,
            'lenka_passive_interest_tax_payable_account_id': accounts[3].id,
        })

    def _investment_accounting_history(self):
        from odoo import fields
        self._configure_investment_accounting()
        investment = self.env['lenka.investment'].create({
            'partner_id': self.partner.id, 'principal_amount': 10000.0,
            'passive_rate': 1.0, 'early_withdrawal_rate': .5, 'rate_period': 'monthly',
            'start_date': '2025-01-15', 'maturity_date': '2025-02-15',
        })
        investment.action_activate()
        investment.action_create_receipt_move()
        investment._generate_interest_until(fields.Date.to_date('2025-02-15'), 1.0)
        interest = investment.interest_line_ids
        interest.action_create_account_move()
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id, 'date': '2025-02-15', 'principal_amount': 2000.0,
        })
        withdrawal.action_post()
        withdrawal.action_create_account_move()
        return investment, interest, withdrawal

    def test_investment_accounting_links_cannot_be_detached(self):
        investment, interest, withdrawal = self._investment_accounting_history()
        for record, field in ((investment, 'receipt_move_id'), (interest, 'move_id'), (withdrawal, 'move_id')):
            original = record[field]
            with self.assertRaises(ValidationError):
                record.write({field: False})
            self.assertEqual(record[field], original)
        for record in (interest, withdrawal):
            with self.assertRaises(ValidationError):
                record.adjustment_move_id = investment.receipt_move_id

    def test_investment_accounting_links_cannot_be_injected_on_create(self):
        investment, interest, withdrawal = self._investment_accounting_history()
        with self.assertRaises(ValidationError):
            investment.copy({'receipt_move_id': investment.receipt_move_id.id})
        with self.assertRaises(ValidationError):
            interest.copy({'move_id': interest.move_id.id})
        with self.assertRaises(ValidationError):
            withdrawal.copy({'move_id': withdrawal.move_id.id})

    def test_investment_accounting_generation_is_idempotent(self):
        investment, interest, withdrawal = self._investment_accounting_history()
        originals = (investment.receipt_move_id, interest.move_id, withdrawal.move_id)
        investment.action_create_receipt_move()
        interest.action_create_account_move()
        withdrawal.action_create_account_move()
        self.assertEqual(originals, (investment.receipt_move_id, interest.move_id, withdrawal.move_id))
        for move in originals:
            self.assertEqual(move.state, 'draft')
            self.assertAlmostEqual(sum(move.line_ids.mapped('debit')), sum(move.line_ids.mapped('credit')))

    def test_accounted_interest_cannot_be_edited_or_removed(self):
        investment, interest, _ = self._investment_accounting_history()
        for vals in ({'amount': 200.0}, {'tax_rate': 20.0}, {'period_date': '2025-03-15'}, {'state': 'draft'}):
            with self.assertRaises(ValidationError):
                interest.write(vals)
        with self.assertRaises(ValidationError):
            interest.unlink()
        self.assertAlmostEqual(investment.paid_interest, 100.0)

    def test_investment_with_receipt_cannot_change_financial_terms(self):
        investment, _, _ = self._investment_accounting_history()
        for vals in ({'principal_amount': 20000.0}, {'passive_rate': 3.0}, {'rate_period': 'annual'},
                     {'maturity_date': '2025-01-20'}, {'early_withdrawal_rate': 1.0}):
            with self.assertRaises(ValidationError):
                investment.write(vals)
        with self.assertRaises(ValidationError):
            investment.unlink()
        investment.notes = 'Observacion permitida para seguimiento'
        self.assertTrue(investment.notes)

    def test_copy_of_used_investment_is_new_draft_without_history(self):
        investment, _, _ = self._investment_accounting_history()
        duplicate = investment.copy()
        self.assertEqual(duplicate.state, 'draft')
        self.assertFalse(duplicate.receipt_move_id)
        self.assertFalse(duplicate.interest_line_ids)
        self.assertFalse(duplicate.withdrawal_ids)
        duplicate.principal_amount = 15000.0
        self.assertAlmostEqual(duplicate.outstanding_principal, 15000.0)

    def test_early_settlement_accounting_does_not_reverse_withholding(self):
        self._configure_investment_accounting()
        self.env['ir.config_parameter'].sudo().set_param('lenka_financiero.passive_interest_tax_rate', '10')
        investment = self.env['lenka.investment'].create({
            'partner_id': self.partner.id, 'principal_amount': 100000.0,
            'passive_rate': 1.5, 'early_withdrawal_rate': 1.0,
            'rate_period': 'monthly', 'start_date': '2025-01-15',
            'maturity_date': '2026-01-15',
        })
        investment.action_activate()
        investment.action_create_receipt_move()
        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id, 'date': '2025-01-25',
            'principal_amount': 100000.0,
        })
        withdrawal.action_post()
        investment.interest_line_ids.action_create_account_move()
        withdrawal.action_create_account_move()
        withdrawal.action_create_account_move()
        self.assertFalse(withdrawal.adjustment_move_id)
        moves = investment.receipt_move_id | investment.interest_line_ids.move_id | withdrawal.move_id
        self.assertEqual(len(moves), 3)
        lines = moves.line_ids
        liability = lines.filtered(lambda l: l.account_id == self.company.lenka_investor_liability_account_id)
        tax = lines.filtered(lambda l: l.account_id == self.company.lenka_passive_interest_tax_payable_account_id)
        expense = lines.filtered(lambda l: l.account_id == self.company.lenka_passive_interest_expense_account_id)
        self.assertAlmostEqual(sum(liability.mapped('balance')), 0.0, places=2)
        self.assertAlmostEqual(sum(tax.mapped('balance')), -33.33, places=2)
        self.assertAlmostEqual(sum(expense.mapped('balance')), 333.33, places=2)
