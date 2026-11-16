from odoo import api, fields, models, _
from odoo.exceptions import AccessError
from odoo.osv import expression

from .context import INTERNAL_APPEND

SCOPE = (8, 9)
SOURCES = ('account.move', 'account.move.line', 'account.payment',
           'account.partial.reconcile', 'account.full.reconcile')


class ImmutableAudit(models.AbstractModel):
    _name = 'sentinel.invoice.audit.immutable'
    _description = 'Append-only audit storage'

    @api.model_create_multi
    def create(self, vals_list):
        if not INTERNAL_APPEND.get():
            raise AccessError(_('Solo el registrador interno puede añadir eventos de auditoría.'))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(_('El historial de auditoría no se puede modificar.'))

    def unlink(self):
        raise AccessError(_('El historial de auditoría no se puede eliminar.'))


class AuditEvent(models.Model):
    _name = 'sentinel.invoice.audit.event'
    _inherit = 'sentinel.invoice.audit.immutable'
    _description = 'Sentinel invoice audit event'
    _order = 'id asc'
    _rec_name = 'event_uid'

    event_uid = fields.Char(required=True, index=True)
    source_event_uid = fields.Char(required=True, index=True)
    correlation_uid = fields.Char(required=True, index=True)
    company_id = fields.Many2one('res.company', required=True, index=True, ondelete='restrict')
    occurred_at = fields.Datetime(required=True, index=True)
    occurred_at_iso = fields.Char(required=True)
    timezone = fields.Char(required=True, default='UTC')
    actor_res_id = fields.Integer(required=True, index=True)
    actor_name = fields.Char(required=True)
    initiating_uid = fields.Integer()
    execution_kind = fields.Char(required=True)
    origin_evidence = fields.Json()
    elevated_execution = fields.Boolean()
    source_model = fields.Char(required=True, index=True)
    source_res_id = fields.Integer(required=True, index=True)
    operation = fields.Selection([('create', 'Create'), ('write', 'Write'), ('unlink', 'Unlink')], required=True, index=True)
    event_type = fields.Char(required=True, index=True)
    invoice_res_id = fields.Integer(index=True)
    invoice_name = fields.Char()
    invoice_refs = fields.Json()
    payment_refs = fields.Json()
    reconciliation = fields.Json()
    relationship_key = fields.Char(index=True)
    debit_line_res_id = fields.Integer(index=True)
    credit_line_res_id = fields.Integer(index=True)
    applied_amount = fields.Float()
    company_currency_res_id = fields.Integer()
    changes = fields.Json()
    before_snapshot = fields.Json()
    after_snapshot = fields.Json()
    capture_policy = fields.Json()
    _sql_constraints = [
        ('event_uid_unique', 'unique(event_uid)', 'Event UUID must be unique.'),
        ('scope_company', 'CHECK(company_id IN (8,9))', 'Only MEGATK and MEDITEK are audited.'),
    ]

    def _search(self, domain, offset=0, limit=None, order=None):
        source_domains = []
        for model in SOURCES:
            native = self.env[model]
            readable = native._search([])  # Native model ACL and record rules, without sudo.
            existing = native.sudo()._search([])
            source_domains.append(expression.AND([
                [('source_model', '=', model)],
                expression.OR([[('source_res_id', 'not in', existing)],
                               [('source_res_id', 'in', readable)]]),
            ]))
        invoices = self.env['account.move']
        invoice_domain = expression.OR([
            [('invoice_res_id', '=', 0)],
            [('invoice_res_id', 'not in', invoices.sudo()._search([]))],
            [('invoice_res_id', 'in', invoices._search([]))],
        ])
        return super()._search(expression.AND([domain, expression.OR(source_domains), invoice_domain]),
                               offset=offset, limit=limit, order=order)

    def check_access(self, operation):
        result = super().check_access(operation)
        if operation == 'read' and self.ids:
            self.env.cr.execute('''SELECT source_model, source_res_id, invoice_res_id
                                   FROM sentinel_invoice_audit_event WHERE id IN %s''', (tuple(self.ids),))
            for model, res_id, invoice_id in self.env.cr.fetchall():
                if model not in SOURCES:
                    raise AccessError(_('Origen de auditoría no autorizado.'))
                self.env[model].check_access('read')
                self.env[model].browse(res_id).exists().check_access('read')
                if invoice_id:
                    self.env['account.move'].browse(invoice_id).exists().check_access('read')
        return result


class AuditCoverage(models.Model):
    _name = 'sentinel.invoice.audit.coverage'
    _inherit = 'sentinel.invoice.audit.immutable'
    _description = 'Sentinel audit capture start marker'
    _order = 'id'

    company_id = fields.Many2one('res.company', required=True, index=True, ondelete='restrict')
    capture_started_at = fields.Datetime(required=True)
    capture_started_at_iso = fields.Char(required=True)
    version = fields.Char(required=True)
    policy = fields.Json(required=True)
    _sql_constraints = [
        ('company_unique', 'unique(company_id)', 'One immutable start marker per company.'),
        ('scope_company', 'CHECK(company_id IN (8,9))', 'Only MEGATK and MEDITEK are audited.'),
    ]
