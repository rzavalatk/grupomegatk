"""Recognize an existing capital entry; never create accounting or bank movements."""
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class LenkaDisbursementRefinance(models.Model):
    _inherit = 'lenka.disbursement'

    payment_method = fields.Selection(
        selection_add=[('refinance_entry', 'Refinanciamiento ya contabilizado')],
        ondelete={'refinance_entry': 'set default'})
    refinance_line_id = fields.Many2one(
        'account.move.line', string='Apunte de capital ya contabilizado',
        copy=False, ondelete='restrict', tracking=True,
        help='Seleccione el cargo a cartera del cliente nuevo, no el pago del cliente anterior.')
    refinance_move_id = fields.Many2one(
        related='refinance_line_id.move_id', string='Asiento existente', readonly=True)

    refinance_company_id = fields.Many2one(related='operation_id.company_id')
    refinance_partner_id = fields.Many2one(related='operation_id.partner_id')
    refinance_portfolio_account_id = fields.Many2one(related='operation_id.company_id.lenka_portfolio_account_id')

    @api.onchange('payment_method', 'refinance_line_id')
    def _onchange_refinance_line(self):
        if self.payment_method != 'refinance_entry':
            self.refinance_line_id = False
            return
        self.funding_line_id = False
        self.destination_type = 'client'
        self.destination_partner_id = self.operation_id.partner_id
        if self.refinance_line_id:
            self.amount = self.refinance_line_id.amount_currency
            self.date = self.refinance_line_id.move_id.date
            self.reference = self.refinance_line_id.move_id.name

    def init(self):
        # A line is consumed in full, once. Cancelled links retain their audit trail.
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS lenka_refinance_line_posted_unique
            ON lenka_disbursement (refinance_line_id)
            WHERE state = 'posted' AND refinance_line_id IS NOT NULL
        """)

    def _require_refinance_manager(self):
        if not self.env.user.has_group('lenka_financiero.group_lenka_manager'):
            raise AccessError(_('Solo un gerente de Lenka puede aplicar o anular un refinanciamiento contabilizado.'))

    @api.model_create_multi
    def create(self, vals_list):
        if any(v.get('refinance_line_id') or v.get('payment_method') == 'refinance_entry' for v in vals_list):
            self._require_refinance_manager()
        return super().create(vals_list)

    def write(self, vals):
        if 'refinance_line_id' in vals:
            self._require_refinance_manager()
            if any(r.state != 'draft' for r in self):
                raise ValidationError(_('No puede cambiar el apunte de una aplicacion registrada.'))
        if vals.get('payment_method') == 'refinance_entry':
            self._require_refinance_manager()
        return super().write(vals)

    @api.constrains('payment_method', 'refinance_line_id', 'funding_line_id', 'destination_type')
    def _check_refinance_fields(self):
        for rec in self:
            if rec.payment_method == 'refinance_entry':
                if not rec.refinance_line_id:
                    raise ValidationError(_('Seleccione el apunte de capital ya contabilizado.'))
                if rec.funding_line_id or rec.destination_type != 'client':
                    raise ValidationError(_('El refinanciamiento es una aplicacion interna al cliente, sin fuente de salida bancaria.'))
            elif rec.refinance_line_id:
                raise ValidationError(_('El apunte existente solo se utiliza con Refinanciamiento ya contabilizado.'))

    def _lock_operations(self):
        operations = self.mapped('operation_id').sorted('id')
        operations.check_access('read')
        operations.flush_recordset()
        if operations:
            self.env.cr.execute('SELECT id FROM lenka_financial_operation WHERE id IN %s ORDER BY id FOR UPDATE',
                                [tuple(operations.ids)])
        self.invalidate_recordset()
        # Force an MVCC version change so concurrent requests retry rather than
        # validating the ceiling from an older repeatable-read snapshot.
        if operations:
            self.env.cr.execute('UPDATE lenka_financial_operation SET write_date = write_date WHERE id IN %s',
                                [tuple(operations.ids)])
        operations.invalidate_recordset()
        self.env['lenka.disbursement'].invalidate_model()

    def _validate_refinance_entry(self, initial=False):
        self.ensure_one()
        line = self.refinance_line_id
        line.check_access('read')
        move = line.move_id
        move.check_access('read')
        operation = self.operation_id
        company = operation.company_id
        if not line or move.state != 'posted' or move.move_type != 'entry':
            raise ValidationError(_('Seleccione un apunte de un asiento de diario publicado.'))
        if move.reversed_entry_id or move.reversal_move_ids.filtered(lambda m: m.state == 'posted'):
            raise ValidationError(_('El asiento seleccionado es una reversion o ya fue revertido.'))
        if line.company_id != company or line.currency_id != operation.currency_id:
            raise ValidationError(_('El apunte debe tener la misma empresa y moneda del prestamo.'))
        if line.partner_id != operation.partner_id:
            raise ValidationError(_('El apunte debe pertenecer exactamente al cliente nuevo del prestamo.'))
        portfolio = company.lenka_portfolio_account_id
        if not portfolio or line.account_id != portfolio:
            raise ValidationError(_('El apunte debe cargar la cuenta de cartera configurada en Lenka. Revise la clasificacion contable antes de vincularlo.'))
        if portfolio.account_type not in ('asset_receivable', 'asset_current', 'asset_non_current'):
            raise ValidationError(_('La cuenta de cartera debe ser una cuenta de activo por cobrar.'))
        if (line.debit <= 0 or line.credit or line.amount_currency <= 0
                or operation.currency_id.compare_amounts(line.amount_currency, self.amount)):
            raise ValidationError(_('El importe debe coincidir con el cargo completo del apunte de capital. No se permiten aplicaciones parciales.'))
        if operation.operation_type != 'loan' or operation.is_quote:
            raise ValidationError(_('Esta aplicacion corresponde exclusivamente a prestamos.'))
        if self.destination_partner_id != operation.partner_id:
            raise ValidationError(_('El beneficiario debe ser el cliente nuevo del prestamo.'))
        if self.date != move.date:
            raise ValidationError(_('La fecha de aplicacion debe coincidir con la fecha contable del asiento existente.'))
        credits = move.line_ids.filtered(lambda l: l.credit > 0)
        if (not credits or any(l.account_id.account_type != 'asset_current' or l.account_id == portfolio for l in credits)
                or move.line_ids.filtered(lambda l: l != line and l.debit > 0)):
            raise ValidationError(_('La contrapartida debe ser una cuenta de intercambio de activo corriente, sin salida bancaria ni ingresos.'))
        if initial and portfolio.reconcile and operation.currency_id.compare_amounts(line.amount_residual_currency, self.amount):
            raise ValidationError(_('El cargo de capital ya tiene conciliaciones. Revise el saldo antes de aplicarlo al prestamo.'))
        # Elevated READ ONLY checks prevent reusing entries hidden by other record rules.
        if self.sudo().search_count([
            ('refinance_line_id', '=', line.id), ('state', '=', 'posted'), ('id', '!=', self.id),
        ]):
            raise ValidationError(_('Este apunte ya fue aplicado a un prestamo.'))
        if self.sudo().search_count([('move_id', '=', move.id)]):
            raise ValidationError(_('El asiento ya pertenece a un desembolso Lenka; no puede reutilizarse.'))
        if self.env['lenka.payment'].sudo().search_count([('move_id', '=', move.id)]):
            raise ValidationError(_('El asiento pertenece a un cobro Lenka; no es un traslado de capital.'))
        return True

    def action_post(self):
        self.check_access('write')
        # Serialize cash and internal applications against the same loan ceiling.
        self._lock_operations()
        for rec in self.filtered(lambda r: r.payment_method == 'refinance_entry' and r.state == 'draft'):
            rec._require_refinance_manager()
            move = rec.refinance_line_id.move_id
            move.check_access('read')
            move.flush_recordset(['state'])
            self.env.cr.execute('SELECT id FROM account_move WHERE id = %s FOR UPDATE', [move.id])
            self.env.cr.execute('UPDATE account_move SET write_date = write_date WHERE id = %s', [move.id])
            move.invalidate_recordset()
            rec.refinance_line_id.invalidate_recordset()
            rec._validate_refinance_entry(initial=True)
        return super().action_post()

    def action_cancel(self):
        self.check_access('write')
        self._lock_operations()
        for rec in self.filtered(lambda r: r.payment_method == 'refinance_entry'):
            rec._require_refinance_manager()
        # move_id is deliberately empty: the existing accounting entry is never changed.
        return super().action_cancel()

    def _prepare_disbursement_move(self):
        if self.payment_method == 'refinance_entry':
            raise ValidationError(_('El refinanciamiento ya esta contabilizado. No se creara otra cuenta por cobrar.'))
        return super()._prepare_disbursement_move()

    def action_create_account_move(self):
        if self.filtered(lambda r: r.payment_method == 'refinance_entry'):
            raise ValidationError(_('Use Ver asiento existente. Esta aplicacion no genera partidas contables.'))
        return super().action_create_account_move()

    def action_open_refinance_move(self):
        self.ensure_one()
        self.refinance_move_id.check_access('read')
        return {'type': 'ir.actions.act_window', 'res_model': 'account.move',
                'view_mode': 'form', 'res_id': self.refinance_move_id.id, 'target': 'current'}


class LenkaOperationRefinance(models.Model):
    _inherit = 'lenka.financial.operation'

    refinance_applied_amount = fields.Monetary(
        string='Refinanciamiento ya contabilizado', compute='_compute_refinance_applied')
    cash_disbursed_amount = fields.Monetary(
        string='Desembolsos con entrega de fondos', compute='_compute_refinance_applied')

    @api.depends('disbursement_ids.state', 'disbursement_ids.amount', 'disbursement_ids.payment_method')
    def _compute_refinance_applied(self):
        for rec in self:
            applied = rec.disbursement_ids.filtered(lambda d: d.state == 'posted')
            rec.refinance_applied_amount = sum(applied.filtered(lambda d: d.payment_method == 'refinance_entry').mapped('amount'))
            rec.cash_disbursed_amount = sum(applied.filtered(lambda d: d.payment_method != 'refinance_entry').mapped('amount'))

    def action_activate(self):
        self.mapped('disbursement_ids')._lock_operations()
        return super().action_activate()

    def write(self, vals):
        protected = {'partner_id', 'company_id', 'currency_id', 'operation_type', 'principal_amount', 'down_payment'}
        if protected.intersection(vals):
            if self.mapped('disbursement_ids').filtered(lambda d: d.payment_method == 'refinance_entry' and d.state == 'posted'):
                raise ValidationError(_('Anule primero la aplicacion interna antes de modificar la identidad o el monto del prestamo.'))
        if vals.get('state') == 'active':
            for rec in self:
                for disbursement in rec.disbursement_ids.filtered(lambda d: d.payment_method == 'refinance_entry' and d.state == 'posted'):
                    disbursement._validate_refinance_entry()
        return super().write(vals)


class AccountMoveRefinanceProtection(models.Model):
    _inherit = 'account.move'

    def _check_lenka_refinance_unlinked(self):
        self.flush_recordset(['state'])
        if self:
            self.env.cr.execute('SELECT id FROM account_move WHERE id IN %s ORDER BY id FOR UPDATE', [tuple(sorted(self.ids))])
        if self.env['lenka.disbursement'].sudo().search_count([
            ('refinance_line_id.move_id', 'in', self.ids), ('state', '=', 'posted'),
        ]):
            raise ValidationError(_('El asiento respalda un refinanciamiento Lenka aplicado. Anule la aplicacion antes de modificar o revertir su contabilidad.'))

    def write(self, vals):
        if {'state', 'line_ids', 'date', 'company_id', 'journal_id', 'move_type', 'reversed_entry_id'}.intersection(vals):
            self._check_lenka_refinance_unlinked()
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        originals = self.browse([v['reversed_entry_id'] for v in vals_list if v.get('reversed_entry_id')])
        originals._check_lenka_refinance_unlinked()
        return super().create(vals_list)


class AccountMoveLineRefinanceProtection(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        moves = self.env['account.move'].browse(list({v['move_id'] for v in vals_list if v.get('move_id')}))
        moves._check_lenka_refinance_unlinked()
        return super().create(vals_list)

    def write(self, vals):
        if {'move_id', 'account_id', 'partner_id', 'debit', 'credit', 'balance',
            'amount_currency', 'currency_id', 'date'}.intersection(vals):
            self.mapped('move_id')._check_lenka_refinance_unlinked()
        return super().write(vals)

    def unlink(self):
        self.mapped('move_id')._check_lenka_refinance_unlinked()
        return super().unlink()
