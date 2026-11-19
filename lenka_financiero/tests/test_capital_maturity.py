"""Only fictitious contracts and accounting entries in the isolated test database."""
from odoo import Command, fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestCapitalMaturity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.write({'groups_id': [Command.link(cls.env.ref('lenka_financiero.group_lenka_manager').id)]})
        cls.company = cls.env.company
        cls.client = cls.env['res.partner'].create({'name': 'FICTITIOUS maturity borrower'})
        cls.portfolio, cls.clearing = cls.env['account.account'].create([
            {'name': 'FICTITIOUS ' + name, 'code': code, 'account_type': kind,
             'reconcile': True, 'company_ids': [Command.set(cls.company.ids)]}
            for name, code, kind in [('capital', 'LMAT1', 'asset_receivable'),
                                     ('clearing', 'LMAT2', 'asset_current')]])
        cls.journal = cls.env['account.journal'].create({
            'name': 'FICTITIOUS maturity journal', 'code': 'LMAT', 'type': 'general',
            'company_id': cls.company.id, 'default_account_id': cls.clearing.id})
        cls.company.write({'lenka_portfolio_account_id': cls.portfolio.id,
                           'lenka_disbursement_journal_id': cls.journal.id})

    def _disbursement(self, **extra):
        op = self.env['lenka.financial.operation'].create({
            'partner_id': self.client.id, 'company_id': self.company.id,
            'operation_type': 'loan', 'principal_amount': 10000, 'interest_rate': 3,
            'term_months': 24, 'calculation_method': 'interest_only', 'is_quote': False,
            'date': '2026-01-15', 'first_payment_date': '2026-02-15', 'state': 'contracted'})
        op.action_generate_schedule()
        self.env['lenka.funding.line'].create({'operation_id': op.id, 'source_type': 'own', 'amount': 10000})
        vals = {'operation_id': op.id, 'amount': 10000, 'date': '2026-01-15',
                'payment_method': 'other', 'disbursement_journal_id': self.journal.id,
                'destination_partner_id': self.client.id}
        vals.update(extra)
        disb = self.env['lenka.disbursement'].create(vals)
        disb.action_post()
        return disb

    def _line(self, disb):
        return disb.move_id.line_ids.filtered(lambda l: l.account_id == self.portfolio)

    def _wizard(self, disb, due='2028-01-15', confirmed=True):
        return self.env['lenka.capital.maturity.wizard'].create({
            'disbursement_id': disb.id, 'due_date': due,
            'reason': 'FICTITIOUS contract: capital at maturity', 'confirmed': confirmed})

    def test_new_draft_uses_explicit_due_date_without_new_bank_movement(self):
        disb = self._disbursement(capital_due_date='2028-01-15')
        before = self.env['account.move'].search_count([])
        disb.action_create_account_move()
        self.assertEqual(self._line(disb).date_maturity, fields.Date.to_date('2028-01-15'))
        self.assertEqual(disb.move_id.state, 'draft')
        self.assertEqual(disb.move_id.journal_id, self.journal)
        self.assertEqual(disb.move_id.line_ids.filtered(lambda l: l.credit).account_id, self.clearing)
        disb.action_create_account_move()
        self.assertEqual(self.env['account.move'].search_count([]), before + 1)

    def test_suggestion_is_last_plan_date_not_two_years_from_today(self):
        disb = self._disbursement()
        self.assertEqual(disb.capital_plan_due_date, fields.Date.to_date('2028-01-15'))
        defaults = self.env['lenka.capital.maturity.wizard'].with_context(
            default_disbursement_id=disb.id).default_get(['disbursement_id', 'due_date'])
        self.assertEqual(fields.Date.to_date(defaults['due_date']), disb.capital_plan_due_date)
        self.assertFalse(disb.capital_due_date)

    def test_existing_posted_entry_only_changes_due_date_and_audits(self):
        disb = self._disbursement()
        disb.action_create_account_move()
        disb.move_id.action_post()
        columns = ['account_id', 'partner_id', 'debit', 'credit', 'balance', 'amount_currency',
                   'currency_id', 'date', 'move_id']
        before = disb.move_id.line_ids.read(columns)
        schedule = disb.operation_id.schedule_line_ids.read(['date', 'capital', 'interest', 'payment'])
        move = disb.move_id
        total = self.env['account.move'].search_count([])
        self._wizard(disb).action_apply()
        self.assertEqual(self._line(disb).date_maturity, fields.Date.to_date('2028-01-15'))
        self.assertEqual(disb.move_id, move)
        self.assertEqual(move.state, 'posted')
        self.assertEqual(move.line_ids.read(columns), before)
        self.assertEqual(disb.operation_id.schedule_line_ids.read(['date', 'capital', 'interest', 'payment']), schedule)
        self.assertEqual(self.env['account.move'].search_count([]), total)
        self.assertTrue(disb.message_ids.filtered(lambda m: 'FICTITIOUS contract' in str(m.body)))

    def test_no_existing_entry_only_saves_date_until_accounting_requested(self):
        disb = self._disbursement()
        before = self.env['account.move'].search_count([])
        self._wizard(disb).action_apply()
        self.assertFalse(disb.move_id)
        self.assertEqual(self.env['account.move'].search_count([]), before)
        disb.action_create_account_move()
        self.assertEqual(self._line(disb).date_maturity, disb.capital_due_date)

    def test_unselected_existing_date_is_preserved(self):
        disb = self._disbursement()
        disb.action_create_account_move()
        before = self._line(disb).date_maturity
        disb.action_create_account_move()
        self.assertFalse(disb.capital_due_date)
        self.assertEqual(self._line(disb).date_maturity, before)

    def test_requires_confirmation_reason_and_valid_date(self):
        disb = self._disbursement()
        with self.assertRaises(ValidationError):
            self._wizard(disb, confirmed=False).action_apply()
        with self.assertRaises(ValidationError):
            disb._apply_capital_maturity('2028-01-15', ' ')
        with self.assertRaises(ValidationError):
            self._wizard(disb, due='2026-01-14').action_apply()
        self.assertFalse(disb.capital_due_date)

    def test_existing_entry_requires_explicit_action_not_direct_field_write(self):
        disb = self._disbursement()
        disb.action_create_account_move()
        with self.assertRaises(ValidationError):
            disb.capital_due_date = '2028-01-15'

    def test_reconciled_capital_is_rejected_without_changing_dates(self):
        disb = self._disbursement()
        disb.action_create_account_move()
        disb.move_id.action_post()
        payment = self.env['account.move'].create({
            'journal_id': self.journal.id, 'date': '2026-02-15', 'line_ids': [
                Command.create({'account_id': self.portfolio.id, 'partner_id': self.client.id, 'credit': 10}),
                Command.create({'account_id': self.clearing.id, 'debit': 10})]})
        payment.action_post()
        (self._line(disb) | payment.line_ids.filtered(lambda l: l.account_id == self.portfolio)).reconcile()
        before = self._line(disb).date_maturity
        with self.assertRaises(ValidationError):
            self._wizard(disb).action_apply()
        self.assertEqual(self._line(disb).date_maturity, before)
        self.assertFalse(disb.capital_due_date)

    def test_wrong_partner_and_shared_amount_are_rejected(self):
        disb = self._disbursement()
        disb.action_create_account_move()
        self._line(disb).partner_id = self.env['res.partner'].create({'name': 'FICTITIOUS other borrower'})
        with self.assertRaises(ValidationError):
            self._wizard(disb).action_apply()
        self._line(disb).partner_id = self.client
        with self.assertRaises(ValidationError):
            disb._capital_maturity_lines(self.env['account.move'].create({
                'journal_id': self.journal.id, 'date': disb.date, 'line_ids': [
                    Command.create({'account_id': self.portfolio.id, 'partner_id': self.client.id,
                                    'debit': 20000, 'currency_id': disb.currency_id.id, 'amount_currency': 20000}),
                    Command.create({'account_id': self.clearing.id, 'credit': 20000})]}))

    def test_manager_and_accounting_write_permissions_are_not_elevated(self):
        disb = self._disbursement()
        user = new_test_user(self.env, login='fictitious_maturity_operator',
                             groups='lenka_financiero.group_lenka_user', company_id=self.company.id)
        with self.assertRaises(AccessError):
            disb.with_user(user).action_open_capital_maturity()
        manager = new_test_user(self.env, login='fictitious_maturity_manager',
                                groups='lenka_financiero.group_lenka_manager', company_id=self.company.id)
        disb.action_create_account_move()
        with self.assertRaises(AccessError):
            disb.with_user(manager)._apply_capital_maturity('2028-01-15', 'FICTITIOUS permission check')
        self.assertFalse(disb.capital_due_date)

    def test_applied_refinance_updates_existing_receivable_without_creating_entry(self):
        disb = self._disbursement()
        disb.action_create_account_move()
        disb.move_id.action_post()
        # Independent fictitious transfer, not an existing disbursement's move.
        move = self.env['account.move'].create({
            'journal_id': self.journal.id, 'date': disb.date, 'line_ids': [
                Command.create({'account_id': self.portfolio.id, 'partner_id': self.client.id,
                                'debit': 500, 'currency_id': disb.currency_id.id, 'amount_currency': 500}),
                Command.create({'account_id': self.clearing.id, 'credit': 500})]})
        move.action_post()
        other = self._disbursement(amount=9500)
        line = move.line_ids.filtered(lambda l: l.debit)
        refi = self.env['lenka.disbursement'].create({
            'operation_id': other.operation_id.id, 'payment_method': 'refinance_entry',
            'refinance_line_id': line.id, 'amount': 500, 'date': move.date,
            'destination_partner_id': self.client.id})
        refi.action_post()
        count = self.env['account.move'].search_count([])
        self._wizard(refi).action_apply()
        self.assertEqual(line.date_maturity, fields.Date.to_date('2028-01-15'))
        self.assertFalse(refi.move_id)
        self.assertEqual(self.env['account.move'].search_count([]), count)

    def test_cancelled_disbursement_cannot_retime_existing_capital(self):
        disb = self._disbursement()
        disb.action_cancel()
        with self.assertRaises(ValidationError):
            self._wizard(disb).action_apply()

    def test_reversed_entry_cannot_retime_old_receivable(self):
        disb = self._disbursement()
        disb.action_create_account_move()
        disb.move_id.action_post()
        reversal = disb.move_id._reverse_moves(default_values_list=[{'date': '2026-02-15'}])
        if reversal.state == 'draft':
            reversal.action_post()
        with self.assertRaises(ValidationError):
            self._wizard(disb).action_apply()
