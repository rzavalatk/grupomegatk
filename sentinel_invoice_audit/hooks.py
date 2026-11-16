from datetime import datetime, timezone

from odoo import Command

from .models.context import internal_append
from .models.event import SCOPE


def _start_coverage(env):
    now = datetime.now(timezone.utc)
    model = env['sentinel.invoice.audit.coverage'].sudo()
    for company in env['res.company'].sudo().browse(SCOPE).exists():
        if not model.search_count([('company_id', '=', company.id)]):
            with internal_append():
                model.create({
                    'company_id': company.id,
                    'capture_started_at': now.replace(tzinfo=None),
                    'capture_started_at_iso': now.isoformat(),
                    'version': '18.0.1.0.0',
                    'policy': {
                        'source': 'ORM transactional capture',
                        'historical_completeness': 'not_proven_before_capture_start',
                        'models': ['account.move', 'account.move.line', 'account.payment',
                                   'account.partial.reconcile', 'account.full.reconcile'],
                        'excluded': ['raw SQL changes', 'binary fields', 'secret-like fields',
                                     'group-restricted fields', 'non-stored computed fields'],
                        'manual_action_proof': 'HTTP or API does not prove a human action',
                    },
                })


def post_init_hook(env):
    _start_coverage(env)
    # A read-only role; no implied accounting, user-management or Settings groups.
    auditor = env['res.users'].sudo().search([
        ('id', '=', 533), ('login', '=', 'analisis.codex@megatk.com'),
    ])
    if auditor:
        auditor.write({'groups_id': [Command.link(env.ref('sentinel_invoice_audit.group_audit_reader').id)]})
