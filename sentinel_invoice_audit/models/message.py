"""Pure-read invoice chatter projection with native parent and field access checks."""
from odoo import api, fields, models, tools
from odoo.osv import expression

from .capture import SECRET


class AuditMessage(models.Model):
    _name = 'sentinel.invoice.audit.message'
    _description = 'Read-only native invoice messages and tracked changes'
    _auto = False
    _order = 'id'
    _rec_name = 'invoice_name'

    source_message_id = fields.Integer(readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)
    invoice_res_id = fields.Integer(readonly=True)
    invoice_name = fields.Char(readonly=True)
    message_date = fields.Datetime(readonly=True)
    created_at = fields.Datetime(readonly=True)
    creator_uid = fields.Integer(readonly=True)
    author_partner_id = fields.Integer(readonly=True)
    message_type = fields.Char(readonly=True)
    subtype_res_id = fields.Integer(readonly=True)
    body = fields.Html(readonly=True)
    tracking_details = fields.Json(compute='_compute_tracking_details')
    attribution = fields.Json(compute='_compute_tracking_details')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE VIEW sentinel_invoice_audit_message AS
            SELECT message.id, message.id AS source_message_id,
                   invoice.company_id, invoice.id AS invoice_res_id,
                   invoice.name AS invoice_name, message.date AS message_date,
                   message.create_date AS created_at, message.create_uid AS creator_uid,
                   message.author_id AS author_partner_id, message.message_type,
                   message.subtype_id AS subtype_res_id, message.body
            FROM mail_message message
            JOIN account_move invoice ON message.model = 'account.move' AND message.res_id = invoice.id
            WHERE invoice.company_id IN (8,9)
        ''')

    def _search(self, domain, offset=0, limit=None, order=None):
        invoice_query = self.env['account.move']._search([('company_id', 'in', [8, 9])])
        message_query = self.env['mail.message']._search([('model', '=', 'account.move')])
        domain = expression.AND([domain, [('invoice_res_id', 'in', invoice_query),
                                          ('source_message_id', 'in', message_query)]])
        return super()._search(domain, offset=offset, limit=limit, order=order)

    def check_access(self, operation):
        result = super().check_access(operation)
        if operation == 'read' and self.ids:
            # No ORM field read here: that would recursively call this access guard.
            self.env.cr.execute('''SELECT invoice_res_id, source_message_id
                                   FROM sentinel_invoice_audit_message WHERE id IN %s''', (tuple(self.ids),))
            pairs = self.env.cr.fetchall()
            self.env['account.move'].browse([row[0] for row in pairs]).check_access('read')
            self.env['mail.message'].browse([row[1] for row in pairs]).check_access('read')
        return result

    @api.depends('source_message_id')
    def _compute_tracking_details(self):
        self.check_access('read')
        for row in self:
            message = self.env['mail.message'].browse(row.source_message_id)
            native = message.sudo().tracking_value_ids
            visible = native._filter_has_field_access(self.env)
            safe = visible.filtered(lambda tracking: tracking.field_id.model == 'account.move'
                                     and tracking.field_id.ttype != 'binary'
                                     and not SECRET.search(tracking.field_id.name))
            row.tracking_details = {
                'source': 'mail.tracking.value',
                'values': safe._tracking_value_format(),
                'withheld_count': len(native) - len(safe),
                'field_visibility_checked': True,
                'historical_completeness': 'not_proven',
                'note': 'Only changes originally tracked by Odoo; removed or restricted fields withheld.',
            }
            row.attribution = {
                'source': 'native_message_metadata',
                'creator_uid': message.create_uid.id,
                'author_partner_id': message.author_id.id,
                'executor_proven': False,
                'historical_payment_terms_at_posting': 'unknown_without_explicit_contemporaneous_evidence',
                'manual_or_automatic': 'unknown',
                'timezone': 'UTC',
            }
