from calendar import monthrange
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


_WITHDRAWAL_RESULTS = {'gross_interest_amount', 'interest_tax_amount',
                       'accrued_interest_amount', 'effective_rate'}

class LenkaInvestment(models.Model):
    _name = 'lenka.investment'
    _description = 'Inversion / Deposito Lenka'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(default='Nuevo', readonly=True, copy=False, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Inversionista / Depositante', required=True, tracking=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', required=True, default=lambda self: self.env.company.currency_id)
    investment_type = fields.Selection([
        ('fixed', 'Plazo fijo'), ('current', 'Cuenta corriente / a la vista'), ('other', 'Otro')
    ], string='Tipo', required=True, default='fixed', tracking=True)
    principal_amount = fields.Monetary(string='Capital recibido', required=True, tracking=True)
    passive_rate = fields.Float(string='Tasa contractual preferencial (%)', required=True, tracking=True)
    early_withdrawal_rate = fields.Float(string='Tasa por retiro anticipado (%)', default=0.0, tracking=True)
    current_rate = fields.Float(string='Tasa vigente (%)', compute='_compute_current_rate')
    rate_period = fields.Selection([('monthly', 'Mensual'), ('annual', 'Anual')], default='annual', required=True)
    start_date = fields.Date(string='Fecha de inicio', required=True, default=fields.Date.context_today)
    maturity_date = fields.Date(string='Vencimiento')
    term_months = fields.Integer(string='Plazo (meses)')
    capitalization = fields.Selection([
        ('monthly', 'Capitalizacion mensual'), ('maturity', 'Pago al vencimiento'), ('manual', 'Manual')
    ], string='Forma de reconocimiento', default='monthly', required=True)
    interest_schedule = fields.Selection([
        ('month_end', 'Fin de mes: dias reales del mes'),
        ('anniversary', 'Aniversario mensual historico (base 30)'),
    ], string='Cierre de intereses', default='month_end', required=True, readonly=True, copy=False)
    receiving_account = fields.Char(string='Cuenta receptora / referencia bancaria')
    contract_reference = fields.Char(string='Referencia de contrato')
    state = fields.Selection([
        ('draft', 'Borrador'), ('active', 'Activa'), ('matured', 'Vencida'),
        ('closed', 'Cerrada'), ('cancelled', 'Cancelada')
    ], default='draft', tracking=True, copy=False)
    interest_line_ids = fields.One2many('lenka.investment.interest', 'investment_id', string='Intereses')
    withdrawal_ids = fields.One2many('lenka.investment.withdrawal', 'investment_id', string='Retiros')
    deposit_ids = fields.One2many('lenka.investment.deposit', 'investment_id', string='Depositos adicionales')
    additional_deposits = fields.Monetary(string='Depositos adicionales', compute='_compute_totals')
    account_balance = fields.Monetary(string='Saldo de la cuenta', compute='_compute_totals')
    accrued_interest = fields.Monetary(string='Interes acumulado', compute='_compute_totals')
    paid_interest = fields.Monetary(string='Interes pagado', compute='_compute_totals')
    withheld_interest_tax = fields.Monetary(string='Impuesto retenido sobre intereses', compute='_compute_totals')
    withdrawn_principal = fields.Monetary(string='Capital retirado', compute='_compute_totals')
    outstanding_principal = fields.Monetary(string='Capital vigente', compute='_compute_totals')
    notes = fields.Text(string='Observaciones')
    terms_locked = fields.Boolean(compute='_compute_terms_locked')

    @api.depends('receipt_move_id', 'interest_line_ids.state', 'withdrawal_ids.state', 'deposit_ids.state')
    def _compute_terms_locked(self):
        for rec in self:
            rec.terms_locked = bool(rec.receipt_move_id or
                                    rec.interest_line_ids.filtered(lambda l: l.state in ('accrued', 'paid')) or
                                    rec.withdrawal_ids.filtered(lambda w: w.state == 'posted') or
                                    rec.deposit_ids.filtered(lambda d: d.state == 'posted'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('lenka.investment') or 'Nuevo'
        return super().create(vals_list)

    def write(self, vals):
        terms = {'partner_id', 'company_id', 'currency_id', 'principal_amount',
                 'investment_type', 'passive_rate', 'early_withdrawal_rate',
                 'rate_period', 'start_date', 'maturity_date', 'term_months', 'capitalization', 'interest_schedule'}
        if terms.intersection(vals):
            self._lock_investment_movements()
            for rec in self:
                if rec.terms_locked:
                    raise ValidationError(_('No puede cambiar las condiciones de una inversion con movimientos registrados. Conserve su historial y formalice una nueva operacion.'))
        return super().write(vals)

    def unlink(self):
        if any(rec.state != 'draft' or rec.receipt_move_id or rec.interest_line_ids or rec.withdrawal_ids or rec.deposit_ids for rec in self):
            raise ValidationError(_('Solo puede eliminar inversiones en borrador sin movimientos.'))
        return super().unlink()

    @api.constrains('principal_amount', 'passive_rate', 'early_withdrawal_rate', 'term_months', 'start_date', 'maturity_date')
    def _check_values(self):
        for rec in self:
            if rec.principal_amount <= 0:
                raise ValidationError(_('El capital recibido debe ser mayor que cero.'))
            if rec.passive_rate < 0 or rec.early_withdrawal_rate < 0:
                raise ValidationError(_('Las tasas no pueden ser negativas.'))
            if rec.term_months < 0:
                raise ValidationError(_('El plazo no puede ser negativo.'))
            if rec.maturity_date and rec.maturity_date < rec.start_date:
                raise ValidationError(_('El vencimiento no puede ser anterior a la fecha de inicio.'))

    @api.depends('principal_amount', 'interest_line_ids.amount', 'interest_line_ids.net_amount', 'interest_line_ids.tax_amount', 'interest_line_ids.state', 'withdrawal_ids.principal_amount', 'withdrawal_ids.state', 'deposit_ids.amount', 'deposit_ids.state')
    def _compute_totals(self):
        for rec in self:
            posted_interest = rec.interest_line_ids.filtered(lambda l: l.state in ('accrued', 'paid'))
            rec.accrued_interest = sum(posted_interest.mapped('amount'))
            rec.paid_interest = sum(rec.interest_line_ids.filtered(lambda l: l.state == 'paid').mapped('net_amount'))
            rec.withheld_interest_tax = sum(posted_interest.mapped('tax_amount'))
            rec.withdrawn_principal = sum(rec.withdrawal_ids.filtered(lambda w: w.state == 'posted').mapped('principal_amount'))
            rec.additional_deposits = sum(rec.deposit_ids.filtered(lambda d: d.state == 'posted').mapped('amount'))
            rec.outstanding_principal = max(rec.principal_amount + rec.additional_deposits - rec.withdrawn_principal, 0.0)
            rec.account_balance = rec.outstanding_principal + sum(posted_interest.filtered(lambda l: l.state != 'paid').mapped('net_amount'))

    def _monthly_rate_for(self, rate):
        self.ensure_one()
        return rate / 100.0 if self.rate_period == 'monthly' else rate / 1200.0

    def _monthly_rate(self):
        self.ensure_one()
        return self._monthly_rate_for(self.current_rate)

    @api.depends('passive_rate', 'withdrawal_ids.state', 'withdrawal_ids.early_withdrawal',
                 'withdrawal_ids.effective_rate', 'withdrawal_ids.date')
    def _compute_current_rate(self):
        for rec in self:
            early = rec.withdrawal_ids.filtered(lambda w: w.state == 'posted' and w.early_withdrawal).sorted('date')[:1]
            rec.current_rate = early.effective_rate if early else rec.passive_rate

    def action_activate(self):
        for rec in self:
            if rec.state != 'draft':
                continue
            if rec.investment_type == 'fixed' and rec.early_withdrawal_rate <= 0:
                raise ValidationError(_('Para una inversion a plazo fijo debe indicar la tasa aplicable por retiro anticipado.'))
            if rec.investment_type == 'fixed' and rec.early_withdrawal_rate > rec.passive_rate:
                raise ValidationError(_('La tasa por retiro anticipado no puede ser mayor que la tasa contractual preferencial.'))
            if rec.investment_type == 'fixed' and not (rec.maturity_date or rec.term_months):
                raise ValidationError(_('Para una inversion a plazo fijo debe indicar vencimiento o plazo.'))
            if not rec.maturity_date and rec.term_months:
                rec.maturity_date = fields.Date.add(rec.start_date, months=rec.term_months)
            rec.state = 'active'
        return True

    def _generate_interest_until(self, end_date, rate, replace=False, settle_partial=False):
        self.ensure_one()
        self._lock_investment_movements()
        if self.interest_schedule == 'anniversary':
            return self._generate_anniversary_interest_until(end_date, rate, replace, settle_partial)
        return self._generate_calendar_interest_until(end_date, rate, replace, settle_partial)

    def _lock_investment_movements(self):
        """Serialize deposits, withdrawals and accruals on their account."""
        self.check_access('write')
        self.flush_recordset()
        if not self:
            return
        self.env.cr.execute('SELECT id FROM lenka_investment WHERE id IN %s ORDER BY id FOR UPDATE', [tuple(self.ids)])
        # Bump the row version without changing values. PostgreSQL repeatable
        # read then retries a concurrent RPC instead of using stale child rows.
        self.env.cr.execute('UPDATE lenka_investment SET write_date = write_date WHERE id IN %s', [tuple(self.ids)])
        self.invalidate_recordset(['interest_line_ids', 'withdrawal_ids', 'deposit_ids', 'terms_locked',
                                  'outstanding_principal', 'additional_deposits', 'account_balance'])

    def action_register_deposit(self):
        self.ensure_one()
        self.check_access('write')
        if self.state != 'active':
            raise ValidationError(_('La cuenta debe estar activa para recibir depositos adicionales.'))
        return {
            'type': 'ir.actions.act_window', 'name': _('Registrar deposito adicional'),
            'res_model': 'lenka.investment.deposit', 'view_mode': 'form', 'target': 'current',
            'context': {'default_investment_id': self.id},
        }

    def _calendar_capital_at(self, day):
        """Opening-day deposits earn interest; withdrawals stop earning that day.

        Net interest compounds at month end. Existing anniversary lines retain
        their original recognition dates; upgrading never rewrites those rows.
        A withdrawal settles all prior interest, so its date resets compounding.
        """
        deposits = self.deposit_ids.filtered(lambda d: d.state == 'posted' and d.date <= day)
        withdrawals = self.withdrawal_ids.filtered(lambda w: w.state == 'posted' and w.date <= day)
        principal = self.principal_amount + sum(deposits.mapped('amount')) - sum(withdrawals.mapped('principal_amount'))
        last_withdrawal = max(withdrawals.mapped('date'), default=self.start_date)
        interest = self.interest_line_ids.filtered(
            lambda l: l.state in ('accrued', 'paid') and last_withdrawal <= l.period_date < day and
            (not withdrawals or l.period_date > last_withdrawal) and
            (not l.is_calendar_period or l.period_date.day == monthrange(l.period_date.year, l.period_date.month)[1])
        ) if self.capitalization == 'monthly' else self.env['lenka.investment.interest']
        return max(principal + self.currency_id.round(sum(interest.mapped('net_amount'))), 0.0)

    def _generate_calendar_interest_until(self, end_date, rate, replace=False, settle_partial=False):
        end_date = fields.Date.to_date(end_date)
        if replace:
            if self.interest_line_ids.filtered(lambda l: l.state != 'paid' and (l.move_id or l.adjustment_move_id)):
                raise ValidationError(_('Debe regularizar los asientos de intereses antes de recalcular el retiro anticipado.'))
            self.interest_line_ids.filtered(lambda l: l.state != 'paid').sudo().unlink()
        # Arrival day is included. A withdrawal or contractual maturity stops
        # accrual at the beginning of its date (half-open cashflow interval).
        limit = end_date - timedelta(days=1) if settle_partial else end_date
        if self.maturity_date:
            limit = min(limit, self.maturity_date - timedelta(days=1))
        existing = self.interest_line_ids.filtered(lambda l: l.state != 'cancelled')
        cursor = max(existing.mapped('period_date'), default=self.start_date - timedelta(days=1)) + timedelta(days=1)
        cursor = max(cursor, self.start_date)
        while cursor <= limit:
            denominator = monthrange(cursor.year, cursor.month)[1]
            month_end = cursor.replace(day=denominator)
            period_end = min(month_end, limit)
            if period_end < month_end and not settle_partial and not (
                self.maturity_date and period_end == self.maturity_date - timedelta(days=1)
            ):
                break
            boundaries = {cursor, period_end + timedelta(days=1)}
            boundaries.update(d.date for d in self.deposit_ids if d.state == 'posted' and cursor < d.date <= period_end)
            boundaries.update(w.date for w in self.withdrawal_ids if w.state == 'posted' and cursor < w.date <= period_end)
            dates = sorted(boundaries)
            weighted_capital = 0.0
            raw_interest = 0.0
            applied_rate = rate
            for first, stop in zip(dates, dates[1:]):
                early = self.withdrawal_ids.filtered(lambda w: w.state == 'posted' and w.early_withdrawal and w.date <= first).sorted('date')[:1]
                applied_rate = early.effective_rate if early else rate
                capital = self._calendar_capital_at(first)
                days = (stop - first).days
                weighted_capital += capital * days
                raw_interest += capital * self._monthly_rate_for(applied_rate) * days / denominator
            days = (period_end - cursor).days + 1
            self.env['lenka.investment.interest'].create({
                'investment_id': self.id, 'period_start_date': cursor, 'period_date': period_end,
                'calculation_days': days, 'day_count_basis': denominator, 'is_calendar_period': True,
                'is_prorated': days != denominator, 'base_amount': weighted_capital / days,
                'rate': applied_rate, 'amount': self.currency_id.round(raw_interest), 'state': 'accrued',
            })
            cursor = period_end + timedelta(days=1)
        return self._calendar_capital_at(max(cursor, self.start_date))

    def _generate_anniversary_interest_until(self, end_date, rate, replace=False, settle_partial=False):
        self.ensure_one()
        self.check_access('write')
        if replace:
            if self.interest_line_ids.filtered(lambda l: l.state != 'paid' and (l.move_id or l.adjustment_move_id)):
                raise ValidationError(_('Debe regularizar los asientos de intereses antes de recalcular el retiro anticipado.'))
            self.interest_line_ids.filtered(lambda l: l.state != 'paid').sudo().unlink()
        end_date = min(end_date, self.maturity_date) if self.maturity_date else end_date
        if end_date <= self.start_date:
            return self.principal_amount

        withdrawals = self.withdrawal_ids.filtered(lambda w: w.state == 'posted').sorted(key=lambda w: (w.date, w.id))
        existing = self.interest_line_ids.filtered(lambda l: l.state != 'cancelled')
        # Conservar el aniversario mensual original incluso al cruzar febrero.
        monthly_starts = {}
        period = 1
        previous_month = self.start_date
        monthly_end = fields.Date.add(self.start_date, months=period)
        while monthly_end <= end_date:
            monthly_starts[monthly_end] = previous_month
            previous_month = monthly_end
            period += 1
            monthly_end = fields.Date.add(self.start_date, months=period)
        boundaries = set(monthly_starts)
        boundaries.update(w.date for w in withdrawals if self.start_date < w.date <= end_date)
        boundaries.update(l.period_date for l in existing if self.start_date < l.period_date <= end_date)
        if settle_partial or end_date == self.maturity_date:
            boundaries.add(end_date)

        base = self.principal_amount
        uncapitalized = 0.0
        applied_rate = rate
        processed = self.env['lenka.investment.withdrawal']
        previous_date = self.start_date
        for current in sorted(boundaries):
            prior = withdrawals.filtered(lambda w: w.date <= previous_date)
            if prior - processed:
                # Todo el interes exigible se liquida en el retiro. Reiniciar
                # sobre el capital restante, sin capitalizar intereses pagados.
                base = max(self.principal_amount - sum(prior.mapped('principal_amount')), 0.0)
                uncapitalized = 0.0
                early = prior.filtered('early_withdrawal')[:1]
                if early:
                    applied_rate = early.effective_rate
                processed = prior
            line = existing.filtered(lambda l: l.period_date == current)[:1]
            if line:
                # No recalcular ni reemplazar la historia liquidada/contabilizada.
                base = line.base_amount
                amount = line.amount
            else:
                full_month = monthly_starts.get(current) == previous_date
                days = 30 if full_month else (current - previous_date).days
                amount = self.currency_id.round(base * self._monthly_rate_for(applied_rate) * days / 30.0)
                self.env['lenka.investment.interest'].create({
                    'investment_id': self.id,
                    'period_start_date': previous_date,
                    'period_date': current,
                    'calculation_days': days,
                    'is_prorated': not full_month,
                    'base_amount': base,
                    'rate': applied_rate,
                    'amount': amount,
                    'state': 'accrued',
                })
            uncapitalized += amount
            if current in monthly_starts and self.capitalization == 'monthly':
                base += uncapitalized
                uncapitalized = 0.0
            previous_date = current
        return base

    def action_generate_monthly_interest(self):
        for rec in self:
            if rec.state not in ('active', 'matured'):
                raise ValidationError(_('La inversion debe estar activa para generar intereses.'))
            end_date = min(fields.Date.context_today(rec), rec.maturity_date) if rec.maturity_date else fields.Date.context_today(rec)
            rec._generate_interest_until(end_date, rec.passive_rate, replace=False)
            if rec.maturity_date and fields.Date.context_today(rec) >= rec.maturity_date:
                rec.state = 'matured'
        return True

    def action_mark_matured(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state != 'active':
                continue
            if not rec.maturity_date or rec.maturity_date > today:
                continue
            rec.action_generate_monthly_interest()
            rec.state = 'matured'
        return True

    def action_recalculate_early_withdrawal(self, withdrawal_date):
        self.ensure_one()
        self.check_access('write')
        if not self.maturity_date or withdrawal_date >= self.maturity_date:
            return self.accrued_interest
        if self.early_withdrawal_rate <= 0:
            raise ValidationError(_('Configure la tasa aplicable por retiro anticipado.'))
        previous = self.withdrawal_ids.filtered(lambda w: w.state == 'posted' and w.early_withdrawal)
        if previous:
            if any(w.date > withdrawal_date for w in previous):
                raise ValidationError(_('No puede recalcular antes de un retiro ya aplicado.'))
            self._generate_interest_until(withdrawal_date, self.passive_rate, settle_partial=True)
            return sum(self.interest_line_ids.filtered(lambda l: l.state == 'accrued' and l.period_date <= withdrawal_date).mapped('amount'))
        paid_lines = self.interest_line_ids.filtered(lambda l: l.state == 'paid')
        if paid_lines:
            raise ValidationError(_('Existen intereses ya pagados. Debe regularizarse el ajuste contable antes de recalcular el retiro anticipado.'))
        self._generate_interest_until(withdrawal_date, self.early_withdrawal_rate, replace=True, settle_partial=True)
        return sum(self.interest_line_ids.filtered(lambda l: l.state == 'accrued' and l.period_date <= withdrawal_date).mapped('amount'))


class LenkaInvestmentInterest(models.Model):
    _name = 'lenka.investment.interest'
    _description = 'Interes Pasivo Lenka'
    _order = 'period_date, id'

    investment_id = fields.Many2one('lenka.investment', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='investment_id.currency_id')
    period_date = fields.Date(string='Fecha periodo', required=True)
    period_start_date = fields.Date(string='Inicio del tramo', readonly=True)
    calculation_days = fields.Integer(string='Dias de calculo', readonly=True)
    day_count_basis = fields.Integer(string='Dias del mes / divisor', readonly=True, default=30)
    is_calendar_period = fields.Boolean(string='Cierre calendario', readonly=True)
    is_prorated = fields.Boolean(string='Interes proporcional', readonly=True)
    base_amount = fields.Monetary(string='Base')
    rate = fields.Float(string='Tasa (%)')
    amount = fields.Monetary(string='Interes bruto', required=True)
    tax_rate = fields.Float(string='Impuesto sobre interes (%)', default=lambda self: self._default_tax_rate())
    tax_amount = fields.Monetary(string='Impuesto retenido', compute='_compute_tax', store=True)
    net_amount = fields.Monetary(string='Interes neto', compute='_compute_tax', store=True)
    state = fields.Selection([('draft', 'Borrador'), ('accrued', 'Devengado'), ('paid', 'Pagado'), ('cancelled', 'Anulado')], default='draft')
    payment_reference = fields.Char(string='Referencia de pago')
    financial_locked = fields.Boolean(compute='_compute_financial_locked')

    @api.depends('state', 'move_id', 'adjustment_move_id')
    def _compute_financial_locked(self):
        for rec in self:
            rec.financial_locked = bool(rec.state == 'paid' or rec.move_id or rec.adjustment_move_id)

    def write(self, vals):
        financial = {'investment_id', 'period_date', 'period_start_date', 'calculation_days',
                     'is_prorated', 'base_amount', 'rate', 'amount', 'tax_rate', 'day_count_basis', 'is_calendar_period'}
        if financial.intersection(vals) and any(rec.state == 'paid' or rec.move_id or rec.adjustment_move_id for rec in self):
            raise ValidationError(_('No puede modificar intereses pagados o vinculados a una partida contable.'))
        if 'state' in vals and any(rec.state == 'paid' and vals['state'] != 'paid' for rec in self):
            raise ValidationError(_('No puede reabrir intereses ya pagados.'))
        if vals.get('state') in ('draft', 'cancelled') and any(rec.move_id or rec.adjustment_move_id for rec in self):
            raise ValidationError(_('Debe regularizar la partida contable antes de cambiar el estado del interes.'))
        return super().write(vals)

    def unlink(self):
        if any(rec.state == 'paid' or rec.move_id or rec.adjustment_move_id for rec in self):
            raise ValidationError(_('No puede eliminar intereses pagados o contabilizados.'))
        return super().unlink()


    def _default_tax_rate(self):
        value = self.env['ir.config_parameter'].sudo().get_param('lenka_financiero.passive_interest_tax_rate', '0')
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @api.depends('amount', 'tax_rate')
    def _compute_tax(self):
        for rec in self:
            rate = min(max(rec.tax_rate or 0.0, 0.0), 100.0) / 100.0
            rec.tax_amount = rec.amount * rate
            rec.net_amount = rec.amount - rec.tax_amount

    @api.constrains('tax_rate')
    def _check_tax_rate(self):
        for rec in self:
            if rec.tax_rate < 0 or rec.tax_rate > 100:
                raise ValidationError(_('El impuesto sobre intereses debe estar entre 0% y 100%.'))

class LenkaInvestmentWithdrawal(models.Model):
    _name = 'lenka.investment.withdrawal'
    _description = 'Retiro de Inversion Lenka'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    investment_id = fields.Many2one('lenka.investment', required=True, ondelete='restrict', tracking=True)
    currency_id = fields.Many2one(related='investment_id.currency_id', store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    principal_amount = fields.Monetary(string='Capital a retirar', required=True)
    gross_interest_amount = fields.Monetary(string='Interes bruto reconocido', readonly=True, copy=False)
    interest_tax_amount = fields.Monetary(string='Retencion sobre interes', readonly=True, copy=False)
    accrued_interest_amount = fields.Monetary(string='Interes neto reconocido', readonly=True, copy=False)
    early_withdrawal = fields.Boolean(string='Retiro anticipado', compute='_compute_early_withdrawal', store=True)
    effective_rate = fields.Float(string='Tasa efectiva aplicada (%)', readonly=True, copy=False)
    total_amount = fields.Monetary(string='Total a pagar', compute='_compute_total', store=True)
    reference = fields.Char(string='Referencia')
    state = fields.Selection([('draft', 'Borrador'), ('posted', 'Aplicado'), ('cancelled', 'Anulado')], default='draft', tracking=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('state', 'draft') != 'draft' or any(vals.get(key) for key in _WITHDRAWAL_RESULTS):
                raise ValidationError(_('Cree el retiro en borrador y utilice Aplicar retiro para calcular sus intereses.'))
            vals['state'] = 'draft'
            for key in _WITHDRAWAL_RESULTS:
                vals[key] = 0.0
        return super().create(vals_list)

    def write(self, vals):
        if _WITHDRAWAL_RESULTS.intersection(vals):
            raise ValidationError(_('Los intereses y la tasa del retiro se calculan al aplicarlo.'))
        if 'state' in vals and any(rec.state != vals['state'] for rec in self):
            raise ValidationError(_('Utilice las acciones del retiro para cambiar su estado.'))
        if {'investment_id', 'date', 'principal_amount'}.intersection(vals) and any(rec.state != 'draft' for rec in self):
            raise ValidationError(_('No puede modificar un retiro aplicado ni su fecha o capital.'))
        return super().write(vals)

    def unlink(self):
        if any(rec.state != 'draft' or rec.move_id or rec.adjustment_move_id for rec in self):
            raise ValidationError(_('Solo puede eliminar retiros en borrador sin partidas contables.'))
        return super().unlink()

    @api.depends('date', 'investment_id.maturity_date')
    def _compute_early_withdrawal(self):
        for rec in self:
            rec.early_withdrawal = bool(rec.investment_id.maturity_date and rec.date < rec.investment_id.maturity_date)

    @api.depends('principal_amount', 'accrued_interest_amount')
    def _compute_total(self):
        for rec in self:
            rec.total_amount = rec.principal_amount + rec.accrued_interest_amount

    @api.constrains('principal_amount')
    def _check_values(self):
        for rec in self:
            if rec.principal_amount <= 0:
                raise ValidationError(_('El capital a retirar debe ser mayor que cero.'))

    def action_post(self):
        self.check_access('write')
        for rec in self:
            if rec.state != 'draft':
                continue
            investment = rec.investment_id
            investment._lock_investment_movements()
            rec.invalidate_recordset()
            if rec.state != 'draft':
                continue
            if investment.state not in ('active', 'matured'):
                raise ValidationError(_('La inversion debe estar activa o vencida para registrar un retiro.'))
            if rec.date < investment.start_date:
                raise ValidationError(_('La fecha del retiro no puede ser anterior al inicio de la inversion.'))
            if rec.date > fields.Date.context_today(rec):
                raise ValidationError(_('No se puede aplicar un retiro con fecha futura.'))
            if rec.principal_amount > investment.outstanding_principal + 0.01:
                raise ValidationError(_('El retiro excede el capital vigente.'))
            previous_withdrawals = investment.withdrawal_ids.filtered(lambda w: w.state == 'posted' and w.id != rec.id)
            if any(w.date > rec.date for w in previous_withdrawals):
                raise ValidationError(_('No puede aplicar un retiro anterior a otro retiro ya aplicado.'))
            if investment.deposit_ids.filtered(lambda d: d.state == 'posted' and d.date > rec.date):
                raise ValidationError(_('No puede aplicar un retiro anterior a un deposito ya confirmado.'))
            future_interest = investment.interest_line_ids.filtered(lambda l: l.state != 'cancelled' and l.period_date > rec.date)
            if future_interest.filtered(lambda l: l.state == 'paid' or l.move_id or l.adjustment_move_id):
                raise ValidationError(_('Existen intereses posteriores pagados o contabilizados. Regularicelos antes de aplicar este retiro.'))
            future_end = max(future_interest.mapped('period_date'), default=False)
            if rec.early_withdrawal:
                investment.action_recalculate_early_withdrawal(rec.date)
                unpaid_interest = investment.interest_line_ids.filtered(lambda l: l.state == 'accrued' and l.period_date <= rec.date)
                super(LenkaInvestmentWithdrawal, rec).write({
                    'gross_interest_amount': sum(unpaid_interest.mapped('amount')),
                    'interest_tax_amount': sum(unpaid_interest.mapped('tax_amount')),
                    'accrued_interest_amount': sum(unpaid_interest.mapped('net_amount')),
                    'effective_rate': investment.current_rate if previous_withdrawals else investment.early_withdrawal_rate,
                })
            else:
                investment._generate_interest_until(rec.date, investment.passive_rate, settle_partial=True)
                unpaid_interest = investment.interest_line_ids.filtered(lambda l: l.state == 'accrued' and l.period_date <= rec.date)
                super(LenkaInvestmentWithdrawal, rec).write({
                    'gross_interest_amount': sum(unpaid_interest.mapped('amount')),
                    'interest_tax_amount': sum(unpaid_interest.mapped('tax_amount')),
                    'accrued_interest_amount': sum(unpaid_interest.mapped('net_amount')),
                    'effective_rate': investment.current_rate,
                })
            if unpaid_interest:
                unpaid_interest.write({'state': 'paid'})
            super(LenkaInvestmentWithdrawal, rec).write({'state': 'posted'})
            # Rehacer solo proyecciones no pagadas ni contabilizadas posteriores
            # al retiro; la historia liquidada permanece intacta.
            if future_end:
                investment.interest_line_ids.filtered(lambda l: l.state != 'cancelled' and l.period_date > rec.date).sudo().unlink()
                if investment.outstanding_principal > 0.01:
                    investment._generate_interest_until(future_end, investment.passive_rate)
            if investment.outstanding_principal <= 0.01:
                investment.state = 'closed'
        return True
