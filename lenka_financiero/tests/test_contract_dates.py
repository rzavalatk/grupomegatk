"""Synthetic data only: administrative calendar corrections preserve financial history."""
import base64

from odoo import Command, fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestContractDates(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.email = 'calendar-company@example.invalid'
        groups = ('base.group_user,lenka_financiero.group_lenka_manager,'
                  'lenka_financiero.group_lenka_sole_authorizer,account.group_account_manager')
        cls.authorizer = new_test_user(cls.env, login='fictitious_calendar_luis', groups=groups,
                                       email='calendar-luis@example.invalid')
        cls.other = new_test_user(cls.env, login='fictitious_calendar_other', groups=groups,
                                  email='calendar-other@example.invalid')
        cls.operator = new_test_user(cls.env, login='fictitious_calendar_operator',
                                     groups='base.group_user,lenka_financiero.group_lenka_manager',
                                     email='calendar-operator@example.invalid')
        cls.company.write({'lenka_sole_signature_approver_id': cls.authorizer.id,
                           'lenka_sole_signature_requester_id': cls.operator.id})
        cls.client = cls.env['res.partner'].create({'name': 'FICTITIOUS calendar borrower'})
        cls.portfolio, cls.clearing = cls.env['account.account'].create([
            {'name': 'FICTITIOUS calendar ' + name, 'code': code, 'account_type': kind,
             'reconcile': True, 'company_ids': [Command.set(cls.company.ids)]}
            for name, code, kind in [('capital', 'LCD1', 'asset_receivable'),
                                     ('clearing', 'LCD2', 'asset_current')]])
        cls.journal = cls.env['account.journal'].create({
            'name': 'FICTITIOUS calendar journal', 'code': 'LCD', 'type': 'general',
            'company_id': cls.company.id, 'default_account_id': cls.clearing.id})
        cls.company.write({'lenka_portfolio_account_id': cls.portfolio.id,
                           'lenka_disbursement_journal_id': cls.journal.id})
        cls.template = cls.env['lenka.contract.template'].create({
            'name': 'FICTITIOUS calendar contract', 'company_id': cls.company.id,
            'document_type': 'contract', 'operation_type': 'all', 'body_html': '<p>FICTITIOUS signed original</p>'})

    def _contracted(self):
        op = self.env['lenka.financial.operation'].with_user(self.operator).create({
            'partner_id': self.client.id, 'company_id': self.company.id, 'operation_type': 'loan',
            'principal_amount': 12000, 'interest_rate': 3, 'rate_period': 'monthly',
            'term_months': 24, 'interest_only_months': 12, 'calculation_method': 'interest_then_level',
            'security_mode': 'sole_signature', 'is_quote': False, 'state': 'review',
            'date': '2026-11-16', 'first_payment_date': '2026-10-14',
            'approval_notes': 'FICTITIOUS calendar correction fixture', 'late_fee_rate': 2,
        })
        op.action_request_sole_signature()
        op = op.with_user(self.authorizer)
        op.action_approve()
        doc = self.env['lenka.generated.document'].create({
            'name': 'FICTITIOUS signed original', 'operation_id': op.id, 'template_id': self.template.id})
        doc.action_render()
        attachment = self.env['ir.attachment'].create({
            'name': 'fictitious-contract.txt', 'type': 'binary',
            'datas': base64.b64encode(b'FICTITIOUS original signature fixture, no real customer'),
            'res_model': doc._name, 'res_id': doc.id})
        doc.attachment_id = attachment
        doc.action_mark_signed()
        op.contract_date = '2026-10-14'
        op.action_mark_contracted()
        funding = self.env['lenka.funding.line'].create({
            'operation_id': op.id, 'source_type': 'own', 'amount': 12000})
        disb = self.env['lenka.disbursement'].create({
            'operation_id': op.id, 'amount': 12000, 'date': '2026-10-14',
            'payment_method': 'other', 'funding_line_id': funding.id,
            'disbursement_journal_id': self.journal.id, 'destination_partner_id': self.client.id})
        disb.action_post()
        disb.action_create_account_move()
        disb.move_id.action_post()
        return op

    def _wizard(self, op, **changes):
        vals = {'operation_id': op.id, 'fingerprint': op._contract_dates_fingerprint(),
                'operation_date': '2026-10-14', 'contract_date': '2026-10-14',
                'first_payment_date': '2026-11-14', 'confirmed': True,
                'reason': 'FICTITIOUS correction of captured calendar'}
        vals.update(changes)
        return self.env['lenka.contract.date.wizard'].with_user(op.env.user).create(vals)

    def test_calendar_shift_preserves_amounts_approval_moves_and_signed_file(self):
        op = self._contracted()
        plan_fields = ['sequence', 'capital', 'interest', 'payment', 'opening_balance', 'closing_balance']
        before = op.schedule_line_ids.read(plan_fields)
        approval = op.read(['approved_by', 'approval_date', 'sole_signature_status', 'contract_signed', 'state'])
        docs = op.generated_document_ids.read(['state', 'signed_date', 'attachment_id', 'rendered_html'])
        attachment = op.generated_document_ids.attachment_id.datas
        move = op.disbursement_ids.move_id
        accounting = move.line_ids.read(['debit', 'credit', 'account_id', 'partner_id', 'date', 'date_maturity'])
        count = self.env['account.move'].search_count([])
        self._wizard(op).action_apply()
        self.assertEqual(op.date, fields.Date.to_date('2026-10-14'))
        self.assertEqual(op.first_payment_date, fields.Date.to_date('2026-11-14'))
        self.assertEqual(op.level_payment_start_date, fields.Date.to_date('2027-11-14'))
        self.assertEqual(op.schedule_line_ids.sorted('sequence')[-1].date, fields.Date.to_date('2028-10-14'))
        self.assertEqual(before, op.schedule_line_ids.read(plan_fields))
        self.assertEqual(approval, op.read(['approved_by', 'approval_date', 'sole_signature_status', 'contract_signed', 'state']))
        self.assertEqual(docs, op.generated_document_ids.read(['state', 'signed_date', 'attachment_id', 'rendered_html']))
        self.assertEqual(attachment, op.generated_document_ids.attachment_id.datas)
        self.assertEqual(accounting, move.line_ids.read(['debit', 'credit', 'account_id', 'partner_id', 'date', 'date_maturity']))
        self.assertEqual(count, self.env['account.move'].search_count([]))
        self.assertEqual(move.state, 'posted')
        self.assertTrue(op.message_ids.filtered(lambda m: 'FICTITIOUS correction' in str(m.body)))

    def test_direct_edits_and_forged_rpc_context_still_denied(self):
        op = self._contracted()
        for key, value in [('first_payment_date', '2026-11-14'), ('date', '2026-10-14'), ('principal_amount', 8000)]:
            with self.assertRaises(ValidationError), self.cr.savepoint():
                op.with_context(_lenka_contract_date_token=True, _lenka_contract_date_operation=op.id).write({key: value})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.schedule_line_ids[:1].with_context(_lenka_contract_date_token=True).write({'date': '2026-11-14'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            op.action_generate_schedule()

    def test_other_authorizer_and_operator_denied(self):
        op = self._contracted()
        for user in (self.other, self.operator):
            with self.assertRaises(AccessError), self.cr.savepoint():
                self._wizard(op.with_user(user)).action_apply()

    def test_confirmation_and_reason_required(self):
        op = self._contracted()
        for changes in ({'confirmed': False}, {'reason': '   '}):
            with self.assertRaises(ValidationError), self.cr.savepoint():
                self._wizard(op, **changes).action_apply()
        self.assertEqual(op.first_payment_date, fields.Date.to_date('2026-10-14'))

    def test_stale_preview_cannot_overwrite_later_change(self):
        op = self._contracted()
        wizard = self._wizard(op)
        op.contract_date = '2026-10-13'
        with self.assertRaisesRegex(ValidationError, 'cambio'), self.cr.savepoint():
            wizard.action_apply()
        self.assertEqual(op.first_payment_date, fields.Date.to_date('2026-10-14'))

    def test_any_collection_prevents_correction(self):
        op = self._contracted()
        self.env['lenka.payment'].create({'operation_id': op.id, 'amount': 10})
        with self.assertRaisesRegex(ValidationError, 'cobros'), self.cr.savepoint():
            self._wizard(op).action_apply()

    def test_paid_or_late_fee_line_prevents_correction(self):
        op = self._contracted()
        for key in ('capital_paid', 'interest_paid', 'late_fee_paid', 'late_fee_due'):
            with self.cr.savepoint():
                line = op.schedule_line_ids[:1]
                line.write({key: 1})
                with self.assertRaises(ValidationError):
                    self._wizard(op).action_apply()
                line.write({key: 0})

    def test_active_operation_prevents_correction(self):
        op = self._contracted()
        op.action_activate()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self._wizard(op).action_apply()

    def test_dates_cannot_contradict_existing_disbursement(self):
        op = self._contracted()
        with self.assertRaisesRegex(ValidationError, 'desembolso'), self.cr.savepoint():
            self._wizard(op, contract_date='2026-10-15').action_apply()

    def test_first_due_must_follow_contract(self):
        op = self._contracted()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self._wizard(op, first_payment_date='2026-10-14').action_apply()

    def test_missing_or_inconsistent_plan_denied(self):
        op = self._contracted()
        # Emulate a malformed stored historical row inside the isolated test only.
        self.cr.execute('UPDATE lenka_amortization_line SET date = %s WHERE id = %s',
                        ['2026-10-15', op.schedule_line_ids[:1].id])
        op.schedule_line_ids.invalidate_recordset()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self._wizard(op).action_apply()

    def test_default_preview_uses_current_data(self):
        op = self._contracted()
        vals = self.env['lenka.contract.date.wizard'].with_user(self.authorizer).with_context(
            default_operation_id=op.id).default_get([
                'operation_id', 'fingerprint', 'operation_date', 'contract_date', 'first_payment_date'])
        self.assertEqual(vals['fingerprint'], op._contract_dates_fingerprint())
        self.assertEqual(vals['contract_date'], fields.Date.to_date('2026-10-14'))
        wizard = self._wizard(op)
        self.assertEqual(wizard.last_payment_date, fields.Date.to_date('2028-10-14'))
        self.assertEqual(wizard.level_payment_start_date, fields.Date.to_date('2027-11-14'))

    def test_no_op_and_repeated_correction_do_not_add_history(self):
        op = self._contracted()
        wizard = self._wizard(op)
        wizard.action_apply()
        messages = op.message_ids
        with self.assertRaises(ValidationError), self.cr.savepoint():
            wizard.action_apply()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self._wizard(op).action_apply()
        self.assertEqual(messages, op.message_ids)

    def test_failure_rolls_back_header_and_every_schedule_date(self):
        from unittest.mock import patch
        op = self._contracted()
        before = op._contract_dates_snapshot()
        model = type(self.env['lenka.amortization.line'])
        original = model.write
        def fail_on_second(lines, vals):
            if set(vals) == {'date'} and 2 in lines.mapped('sequence'):
                raise ValidationError('FICTITIOUS failure halfway through calendar')
            return original(lines, vals)
        with patch.object(model, 'write', fail_on_second):
            with self.assertRaises(ValidationError):
                self._wizard(op).action_apply()
        self.assertEqual(before, op._contract_dates_snapshot())

    def test_company_access_is_required(self):
        op = self._contracted()
        other_company = self.env['res.company'].create({'name': 'FICTITIOUS separate calendar company'})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self._wizard(op.with_context(allowed_company_ids=other_company.ids)).action_apply()
