from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestLenkaBanks(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.write({'groups_id': [Command.link(cls.env.ref(x).id) for x in [
            'lenka_financiero.group_lenka_manager', 'banks.banks_check_manager']]})
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({'name': 'Beneficiario prueba bancos'})
        accounts = cls.env['account.account'].create([
            {'name': name, 'code': code, 'account_type': typ, 'company_ids': [Command.set(cls.company.ids)]}
            for name, code, typ in [('Cartera bancos prueba', 'LB001', 'asset_receivable'),
                                    ('Banco A prueba', 'LB002', 'asset_cash'),
                                    ('Banco B prueba', 'LB003', 'asset_cash'),
                                    ('Tarjeta prueba', 'LB004', 'liability_current')]])
        cls.portfolio = accounts[0]
        cls.journals = cls.env['account.journal'].create([
            {'name': 'Banco A prueba', 'code': 'LBA', 'type': 'bank', 'default_account_id': accounts[1].id},
            {'name': 'Banco B prueba', 'code': 'LBB', 'type': 'bank', 'default_account_id': accounts[2].id},
            {'name': 'Tarjeta prueba', 'code': 'LBT', 'type': 'general', 'default_account_id': accounts[3].id},
        ])
        cls.company.write({'lenka_portfolio_account_id': cls.portfolio.id,
                           'lenka_disbursement_journal_id': cls.journals[0].id})
        cls.sequence = cls.env['ir.sequence'].create({
            'name': 'Chequera A prueba', 'code': 'check', 'move_type': 'check',
            'journal_id': cls.journals[0].id, 'company_id': cls.company.id,
            'prefix': 'CK-A-', 'padding': 4, 'number_next': 667,
        })
        cls.env['ir.sequence'].create({
            'name': 'Chequera B prueba', 'code': 'check', 'move_type': 'check',
            'journal_id': cls.journals[1].id, 'company_id': cls.company.id,
            'prefix': 'CK-B-', 'padding': 4, 'number_next': 1,
        })

    def _operation(self):
        operation = self.env['lenka.financial.operation'].create({
            'partner_id': self.partner.id, 'operation_type': 'loan', 'principal_amount': 300000,
            'interest_rate': 3.5, 'term_months': 18, 'state': 'contracted', 'is_quote': False,
        })
        self.env['lenka.funding.line'].create({'operation_id': operation.id, 'source_type': 'own', 'amount': 300000})
        return operation

    def _disbursement(self, operation, amount, journal=None, method='check'):
        return self.env['lenka.disbursement'].create({
            'operation_id': operation.id, 'amount': amount, 'payment_method': method,
            'disbursement_journal_id': (journal or self.journals[0]).id,
            'destination_partner_id': self.partner.id,
        })

    def test_two_checks_native_sequence_and_single_cxc_each(self):
        operation = self._operation()
        checks = self._disbursement(operation, 150000) | self._disbursement(operation, 150000)
        checks.action_post()
        before = self.env['account.move'].search_count([])
        checks.action_create_account_move()
        self.assertEqual(self.env['account.move'].search_count([]), before + 2)
        self.assertEqual(set(checks.mapped('bank_check_ids.number')), {'CK-A-0667', 'CK-A-0668'})
        self.assertEqual(checks.mapped('bank_check_ids.move_id'), checks.mapped('move_id'))
        checks.action_create_account_move()
        self.assertEqual(self.env['account.move'].search_count([]), before + 2)
        checks.mapped('move_id').action_post()
        self.assertEqual(operation.pending_disbursement, 0)
        self.assertEqual(sum(checks.mapped('move_id.line_ids').filtered(
            lambda l: l.account_id == self.portfolio).mapped('balance')), 300000)
        self.assertEqual(self.sequence.number_next_actual, 669)
        with self.assertRaises(ValidationError):
            checks[0].bank_check_ids.action_validate()
        with self.assertRaises(ValidationError):
            checks[0].bank_check_ids.generate_asiento()
        with self.assertRaises(ValidationError):
            checks[0].move_id.button_draft()

    def test_mixed_bank_transfer_and_card(self):
        operation = self._operation()
        first = self._disbursement(operation, 100000, self.journals[0], 'transfer')
        second = self._disbursement(operation, 100000, self.journals[1], 'transfer')
        third = self._disbursement(operation, 100000, self.journals[2], 'credit_card')
        records = first | second | third
        records.action_post()
        records.action_create_account_move()
        for disbursement in records:
            self.assertEqual(disbursement.move_id.journal_id, disbursement.disbursement_journal_id)
            credit = disbursement.move_id.line_ids.filtered(lambda l: l.credit)
            self.assertEqual(credit.account_id, disbursement.disbursement_journal_id.default_account_id)
        self.assertEqual(operation.pending_disbursement, 0)

    def _historical(self):
        operation = self._operation()
        disbursement = self._disbursement(operation, 300000)
        disbursement.action_post()
        move = self.env['account.move'].create(disbursement._prepare_disbursement_move())
        disbursement._link_disbursement_move(move)
        move.action_post()
        self.sequence.number_next_actual = 677
        wizard = self.env['lenka.historical.check.wizard'].create({
            'disbursement_id': disbursement.id,
            'line_ids': [Command.create({'check_number': str(n), 'amount': 150000}) for n in (667, 668)],
        })
        return disbursement, wizard

    def test_historical_667_668_no_accounting_or_sequence_change(self):
        disbursement, wizard = self._historical()
        before = self.env['account.move'].search_count([])
        balances = disbursement.move_id.line_ids.mapped('balance')
        wizard.action_register()
        self.assertEqual(self.env['account.move'].search_count([]), before)
        self.assertEqual(disbursement.move_id.line_ids.mapped('balance'), balances)
        self.assertEqual(disbursement.move_id.state, 'posted')
        self.assertEqual(self.sequence.number_next_actual, 677)
        self.assertEqual(set(disbursement.bank_check_ids.mapped('number')), {'CK-A-0667', 'CK-A-0668'})
        self.assertEqual(sum(disbursement.bank_check_ids.mapped('total')), 300000)
        self.assertTrue(all(disbursement.bank_check_ids.mapped('lenka_historical')))
        with self.assertRaises(ValidationError):
            wizard.action_register()
        with self.assertRaises(ValidationError):
            disbursement.bank_check_ids.action_anulate_cheque()
        self.assertTrue(disbursement.move_id.exists())

    def test_historical_total_and_duplicate_number_rejected_atomically(self):
        disbursement, wizard = self._historical()
        wizard.line_ids[0].amount = 1
        with self.assertRaises(ValidationError), self.cr.savepoint():
            wizard.action_register()
        self.assertFalse(disbursement.bank_check_ids)
        wizard.line_ids[0].amount = 150000
        wizard.line_ids[1].check_number = '667'
        with self.assertRaises(ValidationError), self.cr.savepoint():
            wizard.action_register()
        self.assertFalse(disbursement.bank_check_ids)

    def test_card_rejects_bank_journal(self):
        disbursement = self._disbursement(self._operation(), 150000, method='credit_card')
        with self.assertRaises(ValidationError):
            disbursement.action_post()

    def test_method_change_preserves_selected_bank(self):
        disbursement = self._disbursement(self._operation(), 150000, self.journals[1], 'transfer')
        disbursement.payment_method = 'check'
        disbursement._onchange_disbursement_journal()
        self.assertEqual(disbursement.disbursement_journal_id, self.journals[1])

    def test_runtime_guard_protects_posted_check_lines(self):
        disbursement = self._disbursement(self._operation(), 150000)
        disbursement.action_post()
        disbursement.action_create_account_move()
        disbursement.move_id.action_post()
        line = disbursement.move_id.line_ids[:1]
        with self.assertRaisesRegex(ValidationError, 'cheques'):
            line.write({'partner_id': False})
        with self.assertRaisesRegex(ValidationError, 'cheques'):
            line.with_context(check_move_validity=False).unlink()
        with self.assertRaisesRegex(ValidationError, 'cheques'):
            self.env['account.move.line'].create({
                'move_id': disbursement.move_id.id, 'account_id': self.portfolio.id,
                'partner_id': self.partner.id, 'debit': 1, 'credit': 0,
            })
