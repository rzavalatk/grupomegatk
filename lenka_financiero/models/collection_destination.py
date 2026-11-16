"""Per-payment receipt destination. Upgrades never account historical payments."""
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LenkaCollectionDestination(models.Model):
    _inherit = 'lenka.payment'

    company_id = fields.Many2one(related='operation_id.company_id', store=True, index=True)
    collection_destination = fields.Selection([
        ('bank', 'Banco'), ('cash', 'Caja'), ('clearing', 'Intercambio interno'),
    ], string='Destino del cobro', copy=False, tracking=True)
    collection_journal_id = fields.Many2one(
        'account.journal', string='Banco / diario receptor', copy=False, tracking=True)
    collection_account_id = fields.Many2one(
        related='collection_journal_id.default_account_id', string='Cuenta receptora', readonly=True)
    collection_bridge_journal_id = fields.Many2one(
        related='company_id.lenka_refinance_clearing_journal_id', readonly=True)
    collection_accounting_state = fields.Selection(related='move_id.state', string='Estado contable')

    def write(self, vals):
        if {'collection_destination', 'collection_journal_id'}.intersection(vals):
            if any(rec.move_id or rec.state == 'cancelled' for rec in self):
                raise ValidationError(_('El destino no puede cambiar cuando el cobro tiene partida o esta anulado.'))
        return super().write(vals)

    def _lock_collection_operations(self):
        self.check_access('write')
        operations = self.mapped('operation_id')
        operations.check_access('read')
        operations.flush_recordset()
        if operations:
            self.env.cr.execute('SELECT id FROM lenka_financial_operation WHERE id IN %s ORDER BY id FOR UPDATE', [tuple(operations.ids)])
            self.env.cr.execute('UPDATE lenka_financial_operation SET write_date = write_date WHERE id IN %s', [tuple(operations.ids)])
        operations.invalidate_recordset()
        self.invalidate_recordset()
        self.env['lenka.payment'].invalidate_model()
        self.env['lenka.amortization.line'].invalidate_model()

    def _validate_collection_destination(self):
        self.ensure_one()
        journal = self.collection_journal_id
        company = self.company_id
        if not self.collection_destination or not journal:
            raise ValidationError(_('Seleccione Destino del cobro y Banco / diario receptor.'))
        journal.check_access('read')
        account = journal.default_account_id
        if journal.company_id != company or not account or company not in account.company_ids:
            raise ValidationError(_('El diario y su cuenta receptora deben pertenecer a la empresa del prestamo.'))
        account.check_access('read')
        if account.deprecated:
            raise ValidationError(_('La cuenta receptora esta obsoleta.'))
        if self.collection_destination == 'clearing':
            designated = journal == company.lenka_refinance_clearing_journal_id
            if (journal.bank_account_id or journal.type not in ('general', 'bank')
                    or (journal.type == 'bank' and not designated)
                    or (account.account_type != 'asset_current'
                        and not (designated and account.account_type == 'asset_cash'))):
                raise ValidationError(_('Intercambio requiere un diario general con cuenta puente de activo corriente, o el puente interno designado de esta empresa, sin cuenta bancaria real.'))
            if self.env['account.journal'].sudo().search_count([
                ('company_id', '=', company.id), ('default_account_id', '=', account.id),
                ('bank_account_id', '!=', False),
            ]):
                raise ValidationError(_('La cuenta seleccionada esta vinculada a un banco real; no puede tratarse como intercambio interno.'))
        elif (journal.type != self.collection_destination
              or account.account_type != 'asset_cash'
              or journal == company.lenka_refinance_clearing_journal_id):
            raise ValidationError(_('Seleccione un banco o caja real del tipo indicado; el puente interno no representa un ingreso bancario.'))
        if account in (company.lenka_portfolio_account_id | company.lenka_interest_income_account_id
                       | company.lenka_late_fee_income_account_id | company.lenka_unapplied_account_id):
            raise ValidationError(_('La cuenta receptora debe ser distinta de cartera, ingresos y anticipos.'))
        for currency in (journal.currency_id, account.currency_id):
            if currency and currency != self.currency_id:
                raise ValidationError(_('La moneda del banco o cuenta receptora debe coincidir con la del cobro.'))
        return journal, account

    def action_apply_and_prepare_collection(self):
        # No accounting sudo. A failure rolls back allocations and the draft,
        # even if an integration catches the exception outside this action.
        with self.env.cr.savepoint():
            self._lock_collection_operations()
            for rec in self:
                rec._validate_collection_destination()
            self.action_post()
            self.action_create_account_move()
        return True

    def action_prepare_collection(self):
        """Prepare an old applied payment without allocating it a second time."""
        with self.env.cr.savepoint():
            self._lock_collection_operations()
            for rec in self.filtered(lambda payment: not payment.move_id):
                rec._validate_collection_destination()
            self.action_create_account_move()
        return True

    def _validate_collection_move(self):
        self.ensure_one()
        move = self.move_id
        expected = self._prepare_collection_move()
        if (self.state != 'posted' or move.company_id != self.company_id
                or move.journal_id.id != expected['journal_id'] or move.date != self.payment_date
                or move.move_type != 'entry' or len(move.line_ids) != len(expected['line_ids'])):
            raise ValidationError(_('La partida no coincide con el cobro Lenka aplicado.'))
        remaining = move.line_ids
        for command in expected['line_ids']:
            vals = command[2]
            candidates = remaining.filtered(lambda line: (
                line.account_id.id == vals['account_id'] and line.partner_id.id == vals['partner_id']
                and line.currency_id.id == vals['currency_id']
                and self.company_id.currency_id.is_zero(line.debit - vals['debit'])
                and self.company_id.currency_id.is_zero(line.credit - vals['credit'])
                and self.currency_id.is_zero(line.amount_currency - vals['amount_currency'])))
            if not candidates:
                raise ValidationError(_('La partida debe conservar destino, cliente, moneda y distribucion del cobro Lenka.'))
            remaining -= candidates[:1]


class AccountMoveCollectionDestination(models.Model):
    _inherit = 'account.move'

    def _get_last_sequence_domain(self, relaxed=False):
        where, params = super()._get_last_sequence_domain(relaxed=relaxed)
        return where + ' AND name NOT LIKE %(lenka_collection_prefix)s', dict(
            params, lenka_collection_prefix='LENKA-COB-%')

    def _check_lenka_target_collection_unlinked(self):
        if self and self.env['lenka.payment'].sudo().search_count([
            ('move_id', 'in', self.ids), ('move_id.state', '=', 'posted'),
            ('collection_destination', '!=', False),
        ]):
            raise ValidationError(_('La partida respalda un cobro Lenka contabilizado. Requiere regularizacion contable antes de modificarla.'))

    def write(self, vals):
        if {'state', 'line_ids', 'date', 'journal_id', 'company_id', 'move_type', 'reversed_entry_id'}.intersection(vals):
            self._check_lenka_target_collection_unlinked()
        if vals.get('state') == 'posted':
            for payment in self.env['lenka.payment'].sudo().search([
                ('move_id', 'in', self.ids), ('collection_destination', '!=', False),
            ]):
                payment._validate_collection_move()
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        self.browse([v['reversed_entry_id'] for v in vals_list if v.get('reversed_entry_id')])._check_lenka_target_collection_unlinked()
        return super().create(vals_list)

    def unlink(self):
        self._check_lenka_target_collection_unlinked()
        return super().unlink()
