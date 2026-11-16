from datetime import date

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import tagged, new_test_user
from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from ..hooks import _start_coverage
from ..models.context import origin


@tagged('post_install', '-at_install')
class TestInvoiceAudit(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Synthetic CI database only. Never override production company identifiers.
        while not cls.env['res.company'].browse(9).exists():
            company = cls.env['res.company'].create({
                'name': 'Synthetic scope %s' % cls.env['res.company'].search_count([]),
                'country_id': cls.env.company.country_id.id,
                'currency_id': cls.env.company.currency_id.id,
            })
            if company.id > 9:
                raise AssertionError('Tests require a fresh synthetic database with company IDs 8 and 9 available')
        cls.company8, cls.company9 = cls.env['res.company'].browse([8, 9])
        cls._use_chart_template(cls.company8)
        cls._use_chart_template(cls.company9)
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=[8, 9, cls.env.company.id]))
        cls.data8 = cls.collect_company_accounting_data(cls.company8)
        cls.data9 = cls.collect_company_accounting_data(cls.company9)
        cls.partner = cls.env['res.partner'].create({'name': 'Synthetic audit customer'})
        cls.partner.with_company(cls.company8).write({
            'property_account_receivable_id': cls.data8['default_account_receivable'].id,
            'property_account_payable_id': cls.data8['default_account_payable'].id,
        })
        cls.partner.with_company(cls.company9).write({
            'property_account_receivable_id': cls.data9['default_account_receivable'].id,
            'property_account_payable_id': cls.data9['default_account_payable'].id,
        })
        cls.actor = new_test_user(cls.env, login='synthetic_audit_actor',
                                 groups='account.group_account_manager',
                                 company_id=8, company_ids=[Command.set([8, 9])])
        cls.reader = new_test_user(cls.env, login='synthetic_audit_reader',
                                  groups='account.group_account_readonly,sentinel_invoice_audit.group_audit_reader',
                                  company_id=8, company_ids=[Command.set([8])])
        cls.other = new_test_user(cls.env, login='synthetic_without_audit_role',
                                 groups='base.group_user', company_id=8, company_ids=[Command.set([8])])
        _start_coverage(cls.env)

    def _invoice(self, company=None):
        company = company or self.company8
        data = self.data8 if company == self.company8 else self.data9
        return self.env['account.move'].with_company(company).create({
            'partner_id': self.partner.id, 'move_type': 'out_invoice',
            'journal_id': data['default_journal_sale'].id, 'invoice_date': date(2026, 11, 14),
            'invoice_payment_term_id': self.pay_terms_b.id,
            'invoice_line_ids': [Command.create({
                'name': 'Synthetic invoice only', 'account_id': data['default_account_revenue'].id,
                'quantity': 1, 'price_unit': 100, 'tax_ids': [Command.clear()],
            })],
        })

    def _events(self, invoice, **filters):
        domain = [('invoice_res_id', '=', invoice.id)] + [(name, '=', value) for name, value in filters.items()]
        return self.env['sentinel.invoice.audit.event'].sudo().search(domain, order='id')

    def _payment(self, amount=70):
        outstanding = self.env['account.account'].with_company(self.company8).create({
            'name': 'Synthetic outstanding', 'code': 'SENTINEL.01',
            'account_type': 'asset_current', 'reconcile': True,
            'company_ids': [Command.set([8])],
        })
        bank = self.data8['default_journal_bank']
        payment = self.env['account.payment'].with_company(self.company8).create({
            'partner_id': self.partner.id, 'partner_type': 'customer', 'payment_type': 'inbound',
            'amount': amount, 'date': date(2026, 11, 14), 'journal_id': bank.id,
            'payment_method_line_id': bank.inbound_payment_method_line_ids[:1].id,
            'outstanding_account_id': outstanding.id,
        })
        payment.action_post()
        return payment

    def _partial(self, invoice, payment, amount):
        debit = invoice.line_ids.filtered(lambda line: line.account_id.account_type == 'asset_receivable')[:1]
        credit = payment.move_id.line_ids.filtered(lambda line: line.account_id.account_type == 'asset_receivable')[:1]
        return self.env['account.partial.reconcile'].create({
            'debit_move_id': debit.id, 'credit_move_id': credit.id, 'amount': amount,
            'debit_amount_currency': amount, 'credit_amount_currency': amount,
        })

    def test_posting_actor_and_terms_are_contemporaneous(self):
        invoice = self._invoice()
        invoice.with_user(self.actor).with_context(allowed_company_ids=[8, 9]).action_post()
        posted = self._events(invoice, event_type='posted', source_model='account.move')
        self.assertTrue(posted)
        self.assertEqual(posted[-1].actor_res_id, self.actor.id)
        self.assertEqual(posted[-1].invoice_refs[0]['payment_term_id'], self.pay_terms_b.id)
        previous = posted[-1].invoice_refs
        invoice.button_draft()
        invoice.write({'invoice_payment_term_id': self.pay_terms_a.id})
        self.assertEqual(posted[-1].invoice_refs, previous)
        self.assertEqual(posted[-1].timezone, 'UTC')
        self.assertTrue(posted[-1].event_uid)

    def test_reverted_changes_reset_cancel_and_deletion_survive(self):
        invoice = self._invoice()
        invoice.action_post()
        invoice.with_user(self.actor).with_context(allowed_company_ids=[8, 9]).write({'ref': 'changed then reverted'})
        invoice.with_user(self.actor).with_context(allowed_company_ids=[8, 9]).write({'ref': False})
        invoice.button_draft()
        invoice.button_cancel()
        events = self._events(invoice, source_model='account.move')
        ref_changes = [change for event in events for change in (event.changes or []) if change['field'] == 'ref']
        self.assertTrue(any(change['new'] == 'changed then reverted' for change in ref_changes))
        self.assertTrue(any(change['old'] == 'changed then reverted' for change in ref_changes))
        self.assertIn('reset_to_draft', events.mapped('event_type'))
        self.assertIn('cancelled', events.mapped('event_type'))
        invoice.button_draft()
        invoice_id = invoice.id
        invoice.with_context(force_delete=True).unlink()
        deleted = self.env['sentinel.invoice.audit.event'].sudo().search([
            ('invoice_res_id', '=', invoice_id), ('source_model', '=', 'account.move'), ('operation', '=', 'unlink'),
        ])
        self.assertTrue(deleted)
        self.assertEqual(deleted[-1].before_snapshot['fields']['id'], invoice_id)

    def test_unapplication_keeps_deleted_relation_and_later_application(self):
        invoice = self._invoice()
        # Immediate term produces a single receivable line for this test.
        invoice.invoice_payment_term_id = self.pay_terms_a
        invoice.action_post()
        payment = self._payment(70)
        partial = self._partial(invoice, payment, 70)
        old_id, debit, credit = partial.id, partial.debit_move_id.id, partial.credit_move_id.id
        partial.with_user(self.actor).with_context(allowed_company_ids=[8, 9]).unlink()
        removed = self._events(invoice, event_type='payment_unapplication')[-1]
        self.assertEqual(removed.actor_res_id, self.actor.id)
        self.assertEqual(removed.reconciliation['partial_reconcile_id'], old_id)
        self.assertEqual(removed.reconciliation['amount'], 70)

        self.assertEqual(removed.reconciliation['debit_line']['id'], debit)
        self.assertEqual(removed.reconciliation['credit_line']['id'], credit)
        self.assertIn(payment.id, [p['id'] for p in removed.payment_refs])
        reapplied = self._partial(invoice, payment, 40)
        applied = self._events(invoice, event_type='payment_application')[-1]
        self.assertEqual(applied.reconciliation['amount'], 40)
        self.assertNotEqual(applied.reconciliation['partial_reconcile_id'], old_id)
        self.assertEqual(applied.reconciliation['partial_reconcile_id'], reapplied.id)
        self.assertEqual(removed.reconciliation['amount'], 70)

    def test_full_reconciliation_is_logged_without_double_counting(self):
        invoice = self._invoice()
        invoice.invoice_payment_term_id = self.pay_terms_a
        invoice.action_post()
        payment = self._payment(100)
        partial = self._partial(invoice, payment, 100)
        full = self.env['account.full.reconcile'].create({
            'partial_reconcile_ids': [Command.set(partial.ids)],
            'reconciled_line_ids': [Command.set((partial.debit_move_id | partial.credit_move_id).ids)],
        })
        self.assertTrue(self._events(invoice, source_model='account.full.reconcile', operation='create'))
        full.unlink()
        removed = self._events(invoice, source_model='account.full.reconcile', operation='unlink')[-1]
        self.assertFalse(removed.reconciliation['amount_is_canonical'])
        self.assertEqual(removed.reconciliation['partial_reconcile_ids'], partial.ids)

    def test_audit_reader_cannot_write_and_company_scope_is_enforced(self):
        invoice8, invoice9 = self._invoice(), self._invoice(self.company9)
        model = self.env['sentinel.invoice.audit.event'].with_user(self.reader).with_context(allowed_company_ids=[8])
        found = model.search([])
        self.assertIn(invoice8.id, found.mapped('invoice_res_id'))
        self.assertNotIn(invoice9.id, found.mapped('invoice_res_id'))
        for method, args in [('create', [{}]), ('write', [{}]), ('unlink', [])]:
            with self.assertRaises(AccessError):
                getattr(found[:1] if method != 'create' else model, method)(*args)
        with self.assertRaises(AccessError):
            self.env['sentinel.invoice.audit.event'].with_user(self.other).search([])
        with self.assertRaises(AccessError):
            model.with_context(sentinel_internal_append=True, sudo=True).create({})
        with self.assertRaises(AccessError):
            invoice8.with_user(self.reader).with_context(allowed_company_ids=[8]).action_post()

    def test_auditor_role_blocks_preexisting_accounting_admin_write_grants(self):
        invoice = self._invoice()
        old_groups = self.actor.groups_id
        self.actor.write({'groups_id': [Command.link(self.env.ref('sentinel_invoice_audit.group_audit_reader').id)]})
        self.assertTrue(old_groups <= self.actor.groups_id)
        actor = self.actor.with_context(allowed_company_ids=[8, 9])
        with self.assertRaises(AccessError):
            invoice.with_user(actor).action_post()
        for model in ['account.move', 'account.move.line', 'account.payment',
                      'account.partial.reconcile', 'account.full.reconcile']:
            records = self.env[model].with_user(actor).with_context(allowed_company_ids=[8, 9])
            for operation, args in [('create', [{}]), ('write', [{}]), ('unlink', [])]:
                with self.assertRaises(AccessError):
                    getattr(records, operation)(*args)
            with self.assertRaises(AccessError):
                records.sudo().with_context(skip_audit=True).create({})
        self.assertTrue(invoice.with_user(actor).with_context(allowed_company_ids=[8, 9]).read(['name']))

    def test_scheduled_origin_and_spoofed_rpc_context(self):
        invoice = self._invoice()
        invoice.with_user(self.actor).with_context(allowed_company_ids=[8, 9]).with_context(sentinel_origin='scheduled_job', skip_audit=True).write({'ref': 'not a cron'})
        event = self._events(invoice, source_model='account.move')[-1]
        self.assertNotEqual(event.execution_kind, 'scheduled_job')
        with origin('scheduled_job', self.actor.id, {'cron_id': 123}):
            invoice.with_user(self.actor).with_context(allowed_company_ids=[8, 9]).write({'ref': 'actual server origin'})
        event = self._events(invoice, source_model='account.move')[-1]
        self.assertEqual(event.execution_kind, 'scheduled_job')
        self.assertEqual(event.origin_evidence['cron_id'], 123)

    def test_failed_transaction_does_not_leave_committed_audit(self):
        invoice = self._invoice()
        count = len(self._events(invoice))
        with self.assertRaisesRegex(ValueError, 'synthetic rollback'):
            with self.env.cr.savepoint():
                invoice.ref = 'rolled back'
                raise ValueError('synthetic rollback')
        self.assertEqual(len(self._events(invoice)), count)

    def test_native_cron_entrypoint_proves_scheduled_execution(self):
        invoice = self._invoice()
        cron = self.env['ir.cron'].create({
            'name': 'Synthetic audit cron', 'active': False, 'user_id': self.actor.id,
            'model_id': self.env['ir.model']._get('account.move').id, 'state': 'code',
            'code': "env['account.move'].browse(%s).write({'ref': 'real cron entrypoint'})" % invoice.id,
        })
        cron.with_user(self.actor).with_context(allowed_company_ids=[8, 9])._callback(
            'Synthetic audit cron', cron.ir_actions_server_id.id)
        event = self._events(invoice, source_model='account.move')[-1]
        self.assertEqual(event.execution_kind, 'scheduled_job')
        self.assertEqual(event.actor_res_id, self.actor.id)
        self.assertEqual(event.origin_evidence['cron_id'], cron.id)

    def test_native_automation_entrypoint_proves_automatic_execution(self):
        invoice = self._invoice()
        model_id = self.env['ir.model']._get('account.move').id
        automation = self.env['base.automation'].create({
            'name': 'Synthetic inactive automation', 'active': False,
            'model_id': model_id, 'trigger': 'on_create_or_write',
            'action_server_ids': [Command.create({
                'name': 'Synthetic audit action', 'model_id': model_id,
                'state': 'code', 'code': "record.write({'ref': 'real automation entrypoint'})",
            })],
        })
        automation.with_user(self.actor).with_context(allowed_company_ids=[8, 9])._process(
            invoice.with_user(self.actor).with_context(allowed_company_ids=[8, 9]))
        event = self._events(invoice, source_model='account.move')[-1]
        self.assertEqual(event.execution_kind, 'automation')
        self.assertEqual(event.actor_res_id, self.actor.id)
        self.assertIn(automation.id, event.origin_evidence['automation_ids'])

    def test_native_chatter_projection_does_not_mark_notifications_read(self):
        invoice = self._invoice()
        message = invoice.message_post(body='Synthetic historical content')
        self.env['mail.tracking.value'].sudo().create({
            'mail_message_id': message.id,
            'field_id': self.env['ir.model.fields']._get('account.move', 'invoice_payment_term_id').id,
            'old_value_integer': self.pay_terms_a.id, 'old_value_char': self.pay_terms_a.name,
            'new_value_integer': self.pay_terms_b.id, 'new_value_char': self.pay_terms_b.name,
        })
        invoice9 = self._invoice(self.company9)
        foreign = invoice9.message_post(body='OTHER COMPANY MUST NOT LEAK')
        model = self.env['sentinel.invoice.audit.message'].with_user(self.reader).with_context(allowed_company_ids=[8])
        rows = model.search_read([('invoice_res_id', '=', invoice.id)], ['id', 'body', 'tracking_details', 'attribution'])
        self.assertTrue(any('Synthetic historical content' in row['body'] for row in rows))
        tracked = next(row for row in rows if row['id'] == message.id)['tracking_details']['values']
        self.assertEqual(tracked[0]['fieldName'], 'invoice_payment_term_id')
        self.assertEqual(tracked[0]['oldValue']['value'], self.pay_terms_a.name)
        self.assertEqual(tracked[0]['newValue']['value'], self.pay_terms_b.name)
        with self.assertRaises(AccessError):
            self.env['mail.tracking.value'].with_user(self.reader).with_context(allowed_company_ids=[8]).search([])
        self.assertTrue(all(row['attribution']['executor_proven'] is False for row in rows))
        self.assertFalse(model.search([('id', '=', foreign.id)]))
        with self.assertRaises(AccessError):
            model.browse(foreign.id).read(['body'])
        with self.assertRaises(AccessError):
            model.browse(rows[0]['id']).write({'body': 'forbidden'})

    def test_audit_respects_native_invoice_record_rules(self):
        invoice = self._invoice()
        event = self._events(invoice, source_model='account.move')[-1]
        self.env['ir.rule'].create({
            'name': 'Synthetic native invoice restriction',
            'model_id': self.env['ir.model']._get('account.move').id,
            'domain_force': "[('id', '!=', %s)] if user.login == 'synthetic_audit_reader' else []" % invoice.id,
        })
        model = self.env['sentinel.invoice.audit.event'].with_user(self.reader).with_context(allowed_company_ids=[8])
        self.assertFalse(model.search([('invoice_res_id', '=', invoice.id)]))
        with self.assertRaises(AccessError):
            model.browse(event.id).read(['before_snapshot'])

    def test_coverage_has_real_start_and_no_backfilled_claim(self):
        coverage = self.env['sentinel.invoice.audit.coverage'].sudo().search([('company_id', '=', 8)])
        self.assertTrue(coverage.capture_started_at)
        self.assertEqual(coverage.policy['historical_completeness'], 'not_proven_before_capture_start')
        self.assertIn('raw SQL changes', coverage.policy['excluded'])
        with self.assertRaises(AccessError):
            coverage.sudo().write({'capture_started_at': '2026-11-01 00:00:00'})
