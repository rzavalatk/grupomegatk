"""Transactional financial audit. Never elevate a financial create/write/unlink."""
from datetime import date, datetime, timezone
from hashlib import sha256
import re
from uuid import uuid4

from odoo import api, models, _
from odoo.exceptions import AccessError

from .context import ORIGIN, internal_append, operation
from .event import SCOPE

SECRET = re.compile(r'password|passwd|secret|token|api.?key|private.?key|cookie|session|credential', re.I)
IGNORED = {'write_date', 'write_uid', 'create_date', 'create_uid', '__last_update',
           'message_main_attachment_id', 'message_partner_ids', 'message_follower_ids',
           'message_ids', 'activity_ids', 'website_message_ids', 'access_url'}
TYPES = {'boolean', 'integer', 'float', 'monetary', 'char', 'text', 'date', 'datetime',
         'selection', 'many2one', 'many2many', 'one2many'}


def _deny_auditor_write(records):
    # Odoo ACL grants are additive. A read ACL alone cannot neutralize the
    # auditor's pre-existing accounting groups. No client context/sudo bypass.
    group = records.env.ref('sentinel_invoice_audit.group_audit_reader', raise_if_not_found=False)
    if group and group.id in records.env.user.sudo().groups_id.ids:
        raise AccessError(_('Auditor solo tiene lectura: no puede crear, modificar ni eliminar registros financieros.'))


def _value(value, field):
    if field.type == 'many2one':
        return {'id': value.id, 'name': value.display_name} if value else None
    if field.type in ('many2many', 'one2many'):
        return {'ids': value.ids}
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, str) and len(value) > 20000:
        return {'prefix': value[:20000], 'truncated': True, 'original_length': len(value)}
    return value


def _snapshot(record):
    record = record.sudo()
    values, excluded = {}, []
    for name, field in record._fields.items():
        if name in IGNORED or name.startswith(('message_', 'activity_')):
            continue
        if not field.store or field.type not in TYPES or field.groups or SECRET.search(name):
            excluded.append(name)
            continue
        values[name] = _value(record[name], field)
    return {'fields': values, 'excluded_fields': sorted(excluded)}


def _invoice_snapshot(invoice):
    term = invoice.invoice_payment_term_id
    definition = []
    for line in term.line_ids:
        definition.append({key: _value(line[key], line._fields[key]) for key in (
            'value', 'value_amount', 'nb_days', 'delay_type', 'days_next_month',
            'discount_percentage', 'discount_days',
        ) if key in line._fields})
    return {
        'id': invoice.id, 'name': invoice.name, 'company_id': invoice.company_id.id,
        'move_type': invoice.move_type, 'state': invoice.state,
        'payment_term_id': term.id or None, 'payment_term_name': term.name or None,
        'payment_term_definition': definition,
        'invoice_date': str(invoice.invoice_date) if invoice.invoice_date else None,
        'invoice_date_due': str(invoice.invoice_date_due) if invoice.invoice_date_due else None,
        'currency_id': invoice.currency_id.id,
        'amount_total': invoice.amount_total,
        'due_lines': [{'id': line.id, 'date_maturity': str(line.date_maturity) if line.date_maturity else None,
                       'balance': line.balance, 'amount_currency': line.amount_currency,
                       'currency_id': line.currency_id.id}
                      for line in invoice.line_ids if line.account_id.account_type in (
                          'asset_receivable', 'liability_payable')],
    }


def _line_snapshot(line):
    return {'id': line.id, 'move_id': line.move_id.id, 'move_name': line.move_id.name,
            'company_id': line.company_id.id, 'account_id': line.account_id.id,
            'partner_id': line.partner_id.id, 'balance': line.balance,
            'amount_currency': line.amount_currency, 'currency_id': line.currency_id.id}


def _relations(record):
    """Resolve and copy all references before a destructive operation."""
    record = record.sudo()
    env = record.env
    moves = env['account.move']
    payments = env['account.payment']
    reconciliation = None
    if record._name == 'account.move':
        moves = record
    elif record._name == 'account.move.line':
        moves = record.move_id
    elif record._name == 'account.payment':
        moves = record.move_id | record.invoice_ids
        payments = record
    elif record._name == 'account.partial.reconcile':
        lines = record.debit_move_id | record.credit_move_id
        moves = lines.move_id
        reconciliation = {
            'partial_reconcile_id': record.id,
            'full_reconcile_id': record.full_reconcile_id.id or None,
            'company_currency_id': record.company_currency_id.id,
            'amount': record.amount,
            'debit_amount_currency': record.debit_amount_currency,
            'credit_amount_currency': record.credit_amount_currency,
            'debit_currency_id': record.debit_currency_id.id,
            'credit_currency_id': record.credit_currency_id.id,
            'debit_line': _line_snapshot(record.debit_move_id),
            'credit_line': _line_snapshot(record.credit_move_id),
            'amount_is_canonical': True,
        }
    elif record._name == 'account.full.reconcile':
        lines = record.reconciled_line_ids
        moves = lines.move_id
        reconciliation = {
            'full_reconcile_id': record.id,
            'partial_reconcile_ids': record.partial_reconcile_ids.ids,
            'lines': [_line_snapshot(line) for line in lines],
            'amount_is_canonical': False,
            'note': 'Use partial reconcile events to count applied or removed amounts once.',
        }
    companies = moves.company_id.ids or (record.company_id.ids if 'company_id' in record._fields else [])
    if len(companies) != 1 or companies[0] not in SCOPE:
        return None
    company = companies[0]
    payments |= moves.origin_payment_id
    invoices = moves.filtered(lambda move: move.is_invoice(include_receipts=True))
    return {
        'company_id': company,
        'invoice_refs': [_invoice_snapshot(inv) for inv in invoices],
        'payment_refs': [{'id': pay.id, 'name': pay.name, 'company_id': pay.company_id.id,
                          'move_id': pay.move_id.id, 'amount': pay.amount,
                          'currency_id': pay.currency_id.id, 'state': pay.state}
                         for pay in payments if pay.company_id.id == company],
        'reconciliation': reconciliation,
    }


def _active(record, relation):
    return relation and record.env.registry.ready and bool(
        record.env['sentinel.invoice.audit.coverage'].sudo().search_count([
            ('company_id', '=', relation['company_id']),
        ], limit=1))


def _before(records):
    result = {}
    for record in records:
        relation = _relations(record)
        if _active(record, relation):
            result[record.id] = (_snapshot(record), relation)
    return result


def _provenance(env):
    server_origin = ORIGIN.get()
    if server_origin:
        return server_origin['kind'], server_origin['initiating_uid'], server_origin['evidence']
    # Do not call an HTTP request "manual". External clients can also use web endpoints.
    try:
        from odoo.http import request
        if request:
            initiating_uid = request.session.uid or env.uid
            return 'http_request_unclassified', initiating_uid, {'path': request.httprequest.path,
                                                                 'authenticated_session_uid': request.session.uid or None}
    except (RuntimeError, AttributeError):
        pass
    return 'unclassified', env.uid, {'source': 'No verified scheduler/automation/request origin'}


def _append(record, op, before, before_relation, correlation, requested_state=None):
    after_relation = _relations(record) if op != 'unlink' else None
    after = _snapshot(record) if op != 'unlink' else None
    relation = after_relation or before_relation
    if not relation or not _active(record, relation):
        return
    # A company transfer is recorded in the departing company without leaking destination values.
    destination_company = record.company_id.id if op != 'unlink' and 'company_id' in record._fields else None
    if before_relation and op != 'unlink' and (
        (after_relation and before_relation['company_id'] != after_relation['company_id'])
        or (destination_company and destination_company != before_relation['company_id'])
    ):
        relation = before_relation
        after = {'fields': {'company_id': {'id': destination_company or after_relation['company_id']}},
                 'excluded_fields': ['destination_company_snapshot']}
    old = (before or {}).get('fields', {})
    new = (after or {}).get('fields', {})
    changes = [{'field': key, 'old': old.get(key), 'new': new.get(key)}
               for key in sorted(set(old) | set(new)) if old.get(key) != new.get(key)]
    event_type = op
    if record._name == 'account.move':
        old_state, new_state = old.get('state'), new.get('state')
        if requested_state == 'posted' and new_state == 'posted' and old_state != 'posted':
            event_type = 'posted'
        elif requested_state == 'draft' and old_state == 'posted' and new_state == 'draft':
            event_type = 'reset_to_draft'
        elif requested_state == 'cancel' and new_state == 'cancel' and old_state != 'cancel':
            event_type = 'cancelled'
    if record._name == 'account.partial.reconcile':
        event_type = {'create': 'payment_application', 'unlink': 'payment_unapplication'}.get(op, op)
    now = datetime.now(timezone.utc)
    kind, initiator, evidence = _provenance(record.env)
    source_uid = str(uuid4())
    vals = {
        'source_event_uid': source_uid, 'correlation_uid': correlation,
        'company_id': relation['company_id'], 'occurred_at': now.replace(tzinfo=None),
        'occurred_at_iso': now.isoformat(), 'timezone': 'UTC',
        'actor_res_id': record.env.uid, 'actor_name': record.env.user.sudo().name,
        'initiating_uid': initiator, 'execution_kind': kind, 'origin_evidence': evidence,
        'elevated_execution': record.env.su,
        'source_model': record._name, 'source_res_id': record.id,
        'operation': op, 'event_type': event_type,
        'invoice_refs': relation['invoice_refs'], 'payment_refs': relation['payment_refs'],
        'reconciliation': relation['reconciliation'], 'changes': changes,
        'before_snapshot': before, 'after_snapshot': after,
        'capture_policy': {'version': '18.0.1.0.0', 'field_values': 'stored safe fields only',
                           'posting_terms': 'invoice_refs snapshot at posted event only',
                           'deleted_relations': 'captured before unlink',
                           'no_human_manual_inference': True},
    }
    if record._name == 'account.partial.reconcile' and relation['reconciliation']:
        rec = relation['reconciliation']
        debit, credit = rec['debit_line']['id'], rec['credit_line']['id']
        identity = '%s:%s:%s:%s:%s' % (relation['company_id'], debit, credit,
                                      rec['debit_currency_id'], rec['credit_currency_id'])
        vals.update(relationship_key=sha256(identity.encode()).hexdigest(),
                    debit_line_res_id=debit, credit_line_res_id=credit,
                    applied_amount=rec['amount'], company_currency_res_id=rec['company_currency_id'])
    invoices = relation['invoice_refs'] or [{'id': 0, 'name': None}]
    # Sudo is used exclusively for append-only audit rows, never the financial operation.
    with internal_append():
        record.env['sentinel.invoice.audit.event'].sudo().create([
            dict(vals, event_uid=str(uuid4()), invoice_res_id=inv['id'], invoice_name=inv['name'])
            for inv in invoices
        ])


def _create(records, vals_list, parent_create):
    _deny_auditor_write(records)
    with operation() as correlation:
        created = parent_create(vals_list)
        if records.env.registry.ready:
            for record, values in zip(created, vals_list):
                relation = _relations(record)
                if _active(record, relation):
                    _append(record, 'create', None, None, correlation, requested_state=values.get('state'))
        return created


def _write(records, vals, parent_write):
    _deny_auditor_write(records)
    with operation() as correlation:
        before = _before(records) if records.env.registry.ready else {}
        result = parent_write(vals)
        for record in records:
            snapshot, relation = before.get(record.id, (None, None))
            if snapshot is not None or _active(record, _relations(record)):
                _append(record, 'write', snapshot, relation, correlation, requested_state=vals.get('state'))
        return result


def _unlink(records, parent_unlink):
    _deny_auditor_write(records)
    with operation() as correlation:
        before = _before(records) if records.env.registry.ready else {}
        result = parent_unlink()
        for record in records:
            if record.id in before:
                snapshot, relation = before[record.id]
                _append(record, 'unlink', snapshot, relation, correlation)
        return result


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        return _create(self, vals_list, super().create)

    def write(self, vals):
        return _write(self, vals, super().write)

    def unlink(self):
        return _unlink(self, super().unlink)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        return _create(self, vals_list, super().create)

    def write(self, vals):
        return _write(self, vals, super().write)

    def unlink(self):
        return _unlink(self, super().unlink)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model_create_multi
    def create(self, vals_list):
        return _create(self, vals_list, super().create)

    def write(self, vals):
        return _write(self, vals, super().write)

    def unlink(self):
        return _unlink(self, super().unlink)


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    @api.model_create_multi
    def create(self, vals_list):
        return _create(self, vals_list, super().create)

    def write(self, vals):
        return _write(self, vals, super().write)

    def unlink(self):
        return _unlink(self, super().unlink)


class AccountFullReconcile(models.Model):
    _inherit = 'account.full.reconcile'

    @api.model_create_multi
    def create(self, vals_list):
        return _create(self, vals_list, super().create)

    def write(self, vals):
        return _write(self, vals, super().write)

    def unlink(self):
        return _unlink(self, super().unlink)
