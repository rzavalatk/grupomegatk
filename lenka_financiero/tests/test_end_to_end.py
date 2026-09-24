from odoo import fields
from odoo.tests.common import TransactionCase


class TestLenkaEndToEnd(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.client = cls.env['res.partner'].create({
            'name': 'Cliente E2E Lenka',
            'email': 'cliente.e2e@lenka.test',
        })
        cls.guarantor = cls.env['res.partner'].create({
            'name': 'Aval E2E Lenka',
            'email': 'aval.e2e@lenka.test',
        })
        cls.investor = cls.env['res.partner'].create({
            'name': 'Inversionista E2E Lenka',
            'email': 'inversionista.e2e@lenka.test',
        })

    def _configure_accounts(self):
        journal = self.env['account.journal'].search([
            ('company_id', '=', self.company.id),
            ('default_account_id', '!=', False),
        ], limit=1)
        accounts = self.env['account.account'].search([
            ('company_ids', 'in', self.company.id),
        ], limit=6)
        if not journal or len(accounts) < 6:
            self.skipTest('Base de prueba sin configuracion contable suficiente.')

        self.company.write({
            'lenka_disbursement_journal_id': journal.id,
            'lenka_collection_journal_id': journal.id,
            'lenka_investment_journal_id': journal.id,
            'lenka_portfolio_account_id': accounts[0].id,
            'lenka_interest_income_account_id': accounts[1].id,
            'lenka_late_fee_income_account_id': accounts[2].id,
            'lenka_unapplied_account_id': accounts[3].id,
            'lenka_investor_liability_account_id': accounts[4].id,
            'lenka_passive_interest_expense_account_id': accounts[5].id,
        })

    def test_full_credit_lifecycle_to_draft_accounting(self):
        self._configure_accounts()

        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.client.id,
            'guarantor_ids': [(6, 0, [self.guarantor.id])],
            'operation_type': 'financing',
            'principal_amount': 100000.0,
            'down_payment': 10000.0,
            'interest_rate': 3.0,
            'rate_period': 'monthly',
            'term_months': 12,
            'calculation_method': 'level',
            'is_quote': True,
        })

        operation.action_generate_schedule()
        self.assertEqual(len(operation.schedule_line_ids), 12)
        self.assertAlmostEqual(operation.financed_amount, 90000.0, places=2)

        operation.action_convert_to_application()
        self.assertFalse(operation.is_quote)
        self.assertEqual(operation.state, 'review')

        operation.action_approve()
        self.assertEqual(operation.state, 'approved')
        self.assertTrue(operation.approved_by)

        template = self.env['lenka.contract.template'].create({
            'name': 'Contrato E2E Financiamiento',
            'company_id': self.company.id,
            'document_type': 'contract',
            'operation_type': 'financing',
            'body_html': '<p>{{CLIENTE}} - {{MONTO_FINANCIADO}} - {{TASA}}</p>',
        })
        operation.action_generate_contract_documents()
        # Odoo.sh loads demo templates as well as the template created here.
        # Check this fixture's document without depending on demo data being absent.
        document = operation.generated_document_ids.filtered(lambda d: d.template_id == template)
        self.assertEqual(len(document), 1)
        self.assertEqual(document.template_id, template)
        self.assertEqual(document.state, 'generated')
        self.assertIn(self.client.name, document.rendered_html)

        document.attachment_id = self.env['ir.attachment'].create({
            'name': 'contrato-e2e-firmado.pdf',
            'datas': 'RklSTUFETw==',
            'res_model': 'lenka.generated.document',
            'res_id': document.id,
        })
        document.action_mark_signed()
        self.assertTrue(operation.contract_signed)

        operation.action_mark_contracted()
        self.assertEqual(operation.state, 'contracted')

        funding = self.env['lenka.funding.line'].create({
            'operation_id': operation.id,
            'source_type': 'own',
            'reference': 'Fondeo E2E',
            'amount': 90000.0,
            'cost_rate': 0.0,
            'cost_period': 'annual',
        })

        disbursement = self.env['lenka.disbursement'].create({
            'operation_id': operation.id,
            'amount': 90000.0,
            'destination_type': 'client',
            'destination_partner_id': self.client.id,
            'payment_method': 'transfer',
            'funding_line_id': funding.id,
        })
        disbursement.action_post()
        self.assertEqual(disbursement.state, 'posted')
        self.assertAlmostEqual(operation.pending_disbursement, 0.0, places=2)

        disbursement.action_create_account_move()
        self.assertTrue(disbursement.move_id)
        self.assertEqual(disbursement.move_id.state, 'draft')

        operation.action_activate()
        self.assertEqual(operation.state, 'active')

        first = operation.schedule_line_ids.sorted('sequence')[0]
        first.late_fee_due = 500.0
        payment = self.env['lenka.payment'].create({
            'operation_id': operation.id,
            'payment_date': first.date,
            'amount': 5000.0,
            'payment_method': 'cash',
        })
        payment.action_post()

        self.assertEqual(payment.state, 'posted')
        self.assertAlmostEqual(payment.late_fee_amount, 500.0, places=2)
        self.assertGreater(payment.interest_amount, 0.0)
        self.assertGreaterEqual(payment.capital_amount, 0.0)

        payment.action_create_account_move()
        self.assertTrue(payment.move_id)
        self.assertEqual(payment.move_id.state, 'draft')

    def test_fixed_investment_to_early_withdrawal_and_draft_accounting(self):
        self._configure_accounts()

        today = fields.Date.context_today(self.env.user)
        start = fields.Date.add(today, months=-3)

        investment = self.env['lenka.investment'].create({
            'partner_id': self.investor.id,
            'investment_type': 'fixed',
            'principal_amount': 100000.0,
            'passive_rate': 1.5,
            'early_withdrawal_rate': 1.0,
            'rate_period': 'monthly',
            'start_date': start,
            'term_months': 12,
            'capitalization': 'monthly',
        })
        investment.action_activate()
        self.assertEqual(investment.state, 'active')

        investment.action_generate_monthly_interest()
        self.assertTrue(investment.interest_line_ids)
        preferential_total = sum(investment.interest_line_ids.mapped('amount'))
        self.assertGreater(preferential_total, 0.0)

        investment.action_create_receipt_move()
        self.assertTrue(investment.receipt_move_id)
        self.assertEqual(investment.receipt_move_id.state, 'draft')

        withdrawal = self.env['lenka.investment.withdrawal'].create({
            'investment_id': investment.id,
            'principal_amount': 20000.0,
            'date': today,
        })
        withdrawal.action_post()

        self.assertTrue(withdrawal.early_withdrawal)
        self.assertAlmostEqual(withdrawal.effective_rate, 1.0, places=4)
        self.assertLess(withdrawal.accrued_interest_amount, preferential_total)
        self.assertEqual(withdrawal.state, 'posted')

        withdrawal.action_create_account_move()
        self.assertTrue(withdrawal.move_id)
        self.assertEqual(withdrawal.move_id.state, 'draft')


    def test_disbursement_cannot_exceed_selected_funding_source(self):
        from odoo.exceptions import ValidationError
        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.client.id,
            'operation_type': 'loan',
            'principal_amount': 100000.0,
            'interest_rate': 2.0,
            'rate_period': 'monthly',
            'term_months': 12,
            'calculation_method': 'level',
            'is_quote': False,
            'state': 'contracted',
            'contract_signed': True,
        })
        operation.action_generate_schedule()
        source_a = self.env['lenka.funding.line'].create({
            'operation_id': operation.id,
            'source_type': 'own',
            'amount': 60000.0,
            'cost_rate': 0.0,
            'cost_period': 'annual',
        })
        self.env['lenka.funding.line'].create({
            'operation_id': operation.id,
            'source_type': 'bank_loan',
            'partner_id': self.investor.id,
            'amount': 40000.0,
            'cost_rate': 15.0,
            'cost_period': 'annual',
        })
        disbursement = self.env['lenka.disbursement'].create({
            'operation_id': operation.id,
            'amount': 70000.0,
            'funding_line_id': source_a.id,
            'destination_type': 'client',
            'destination_partner_id': self.client.id,
            'payment_method': 'transfer',
        })
        with self.assertRaises(ValidationError):
            disbursement.action_post()


    def test_active_operation_disbursement_cannot_be_cancelled(self):
        from odoo.exceptions import ValidationError
        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.client.id,
            'operation_type': 'loan',
            'principal_amount': 50000.0,
            'interest_rate': 2.0,
            'rate_period': 'monthly',
            'term_months': 6,
            'calculation_method': 'level',
            'is_quote': False,
            'state': 'contracted',
            'contract_signed': True,
        })
        operation.action_generate_schedule()
        funding = self.env['lenka.funding.line'].create({
            'operation_id': operation.id,
            'source_type': 'own',
            'amount': 50000.0,
            'cost_rate': 0.0,
            'cost_period': 'annual',
        })
        disbursement = self.env['lenka.disbursement'].create({
            'operation_id': operation.id,
            'amount': 50000.0,
            'funding_line_id': funding.id,
            'destination_type': 'client',
            'destination_partner_id': self.client.id,
            'payment_method': 'transfer',
        })
        disbursement.action_post()
        operation.action_activate()
        with self.assertRaises(ValidationError):
            disbursement.action_cancel()


    def test_approval_requires_guarantor_or_guarantee(self):
        from odoo.exceptions import ValidationError
        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.client.id,
            'operation_type': 'loan',
            'principal_amount': 25000.0,
            'interest_rate': 2.0,
            'rate_period': 'monthly',
            'term_months': 6,
            'calculation_method': 'level',
            'is_quote': False,
            'state': 'review',
        })
        operation.action_generate_schedule()
        with self.assertRaises(ValidationError):
            operation.action_approve()

    def test_mark_contracted_requires_signed_attachment(self):
        from odoo.exceptions import ValidationError
        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.client.id,
            'guarantor_ids': [(6, 0, [self.guarantor.id])],
            'operation_type': 'loan',
            'principal_amount': 25000.0,
            'interest_rate': 2.0,
            'rate_period': 'monthly',
            'term_months': 6,
            'calculation_method': 'level',
            'is_quote': False,
            'state': 'review',
        })
        operation.action_generate_schedule()
        operation.action_approve()
        template = self.env['lenka.contract.template'].create({
            'name': 'Contrato sin evidencia adjunta',
            'company_id': self.company.id,
            'document_type': 'contract',
            'operation_type': 'loan',
            'body_html': '<p>{{CLIENTE}}</p>',
        })
        operation.action_generate_contract_documents()
        document = operation.generated_document_ids.filtered(lambda d: d.template_id == template)[:1]
        self.assertTrue(document)
        document.write({'state': 'signed'})
        operation.write({'contract_signed': True})
        with self.assertRaises(ValidationError):
            operation.action_mark_contracted()


    def test_schedule_cannot_be_replaced_after_disbursement(self):
        from odoo.exceptions import ValidationError
        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.client.id,
            'guarantor_ids': [(6, 0, [self.guarantor.id])],
            'operation_type': 'loan',
            'principal_amount': 30000.0,
            'interest_rate': 2.0,
            'rate_period': 'monthly',
            'term_months': 6,
            'calculation_method': 'level',
            'is_quote': False,
            'state': 'contracted',
        })
        operation.action_generate_schedule()
        self.env['lenka.funding.line'].create({
            'operation_id': operation.id, 'source_type': 'own', 'amount': 30000.0,
        })
        self.env['lenka.disbursement'].create({
            'operation_id': operation.id,
            'amount': 30000.0,
        }).action_post()
        with self.assertRaises(ValidationError):
            operation.action_generate_schedule()
