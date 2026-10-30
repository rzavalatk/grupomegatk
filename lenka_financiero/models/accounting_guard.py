"""Runtime guards for Lenka links; no account.move.line schema extension.

Like auditlog's registry hooks, these wrappers compose with the existing ORM
methods. They never change accounting constraints, tables or historical rows.
Every call resolves its guard from the current environment/registry.
"""
from odoo import api, models


PROTECTED_FIELDS = frozenset({
    'move_id', 'account_id', 'partner_id', 'debit', 'credit', 'balance',
    'amount_currency', 'currency_id', 'date',
})


def _has_guard(method):
    pending, seen = [method], set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if getattr(current, '_lenka_line_guard', False):
            return True
        for attr in ('origin', '__wrapped__'):
            parent = getattr(current, attr, None)
            if parent is not None:
                pending.append(parent)
    return False


def _wrap_create(original):
    @api.model_create_multi
    def create(records, vals_list, **kwargs):
        moves = records.env['account.move'].browse(list({
            vals['move_id'] for vals in vals_list if vals.get('move_id')
        }))
        records.env['lenka.accounting.guard']._check_line_moves(moves)
        return original(records, vals_list, **kwargs)
    create._lenka_line_guard = True
    create.origin = original
    return create


def _wrap_write(original):
    def write(records, vals, **kwargs):
        if PROTECTED_FIELDS.intersection(vals):
            moves = records.mapped('move_id')
            if vals.get('move_id'):
                moves |= records.env['account.move'].browse(vals['move_id'])
            records.env['lenka.accounting.guard']._check_line_moves(moves)
        return original(records, vals, **kwargs)
    write._lenka_line_guard = True
    write.origin = original
    return write


def _wrap_unlink(original):
    def unlink(records, **kwargs):
        records.env['lenka.accounting.guard']._check_line_moves(records.mapped('move_id'))
        return original(records, **kwargs)
    unlink._lenka_line_guard = True
    unlink.origin = original
    return unlink


class LenkaAccountingGuard(models.AbstractModel):
    _name = 'lenka.accounting.guard'
    _description = 'Proteccion de apuntes vinculados a Lenka'

    def _register_hook(self):
        result = super()._register_hook()
        line_class = type(self.env['account.move.line'])
        for name, factory in (
            ('create', _wrap_create), ('write', _wrap_write), ('unlink', _wrap_unlink),
        ):
            original = getattr(line_class, name)
            if not _has_guard(original):
                setattr(line_class, name, factory(original))
        return result

    def _check_line_moves(self, moves):
        if not moves:
            return
        # Preserve the original row locking before checking links, so applying
        # a refinance cannot race an accounting edit. The helper only reads
        # link metadata and rejects linked entries; it never changes any move.
        moves._check_lenka_refinance_unlinked()
