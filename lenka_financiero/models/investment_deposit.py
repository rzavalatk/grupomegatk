from math import isfinite

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LenkaInvestmentDeposit(models.Model):
    _name = 'lenka.investment.deposit'
    _description = 'Deposito adicional de inversionista Lenka'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _check_company_auto = True

    name = fields.Char(default='Nuevo', readonly=True, copy=False)
    investment_id = fields.Many2one('lenka.investment', string='Cuenta del inversionista', required=True, ondelete='restrict', index=True)
    company_id = fields.Many2one(related='investment_id.company_id', store=True, index=True)
    partner_id = fields.Many2one(related='investment_id.partner_id', store=True)
    currency_id = fields.Many2one(related='investment_id.currency_id', store=True)
    date = fields.Date(string='Fecha del deposito', required=True, default=fields.Date.context_today, tracking=True)
    amount = fields.Monetary(string='Importe recibido', required=True, tracking=True)
    journal_id = fields.Many2one('account.journal', string='Banco / caja receptora', required=True, check_company=True,
                                 domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
    reference = fields.Char(string='Referencia bancaria / comprobante', required=True, tracking=True)
    move_id = fields.Many2one('account.move', string='Partida de recepcion', readonly=True, copy=False, ondelete='restrict')
    accounting_state = fields.Selection(related='move_id.state', string='Estado contable')
    state = fields.Selection([('draft', 'Borrador'), ('posted', 'Confirmado'), ('cancelled', 'Anulado')], default='draft', copy=False, tracking=True)
    notes = fields.Text(string='Observaciones')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('state', 'draft') != 'draft' or vals.get('move_id'):
                raise ValidationError(_('Cree el deposito en borrador y utilice Confirmar deposito.'))
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('lenka.investment.deposit') or 'Nuevo'
        records = super().create(vals_list)
        records.mapped('investment_id').check_access('write')
        return records

    def write(self, vals):
        if {'state', 'move_id'}.intersection(vals):
            raise ValidationError(_('Utilice las acciones del deposito para confirmar o anular; la partida no puede reemplazarse.'))
        if {'investment_id', 'date', 'amount', 'journal_id', 'reference'}.intersection(vals) and any(rec.state != 'draft' for rec in self):
            raise ValidationError(_('No puede modificar un deposito confirmado o anulado.'))
        result = super().write(vals)
        if 'investment_id' in vals:
            self.mapped('investment_id').check_access('write')
        return result

    def unlink(self):
        if any(rec.state != 'draft' or rec.move_id for rec in self):
            raise ValidationError(_('Solo puede eliminar depositos en borrador sin partida.'))
        return super().unlink()

    @api.constrains('amount', 'reference', 'journal_id', 'investment_id')
    def _check_values(self):
        for rec in self:
            if not isfinite(rec.amount) or rec.amount <= 0 or rec.currency_id.is_zero(rec.amount):
                raise ValidationError(_('El importe del deposito debe ser mayor que cero.'))
            if not (rec.reference or '').strip():
                raise ValidationError(_('Indique la referencia del deposito.'))
            if rec.journal_id.company_id != rec.company_id or rec.journal_id.type not in ('bank', 'cash'):
                raise ValidationError(_('Seleccione un banco o caja de la misma empresa que la cuenta.'))

    def _validate_accounting(self):
        self.ensure_one()
        company = self.company_id
        bank = self.journal_id.default_account_id
        liability = company.lenka_investor_liability_account_id
        if not bank or not liability:
            raise ValidationError(_('Configure la cuenta del banco / caja y la obligacion con inversionistas en esta empresa.'))
        if company not in bank.company_ids or company not in liability.company_ids:
            raise ValidationError(_('Las cuentas contables deben pertenecer a la empresa del inversionista.'))
        if bank.account_type != 'asset_cash' or liability.account_type not in ('liability_current', 'liability_non_current') or bank == liability:
            raise ValidationError(_('La recepcion requiere una cuenta de liquidez y una obligacion con inversionistas de pasivo.'))
        if bank.deprecated or liability.deprecated:
            raise ValidationError(_('No puede recibir depositos en cuentas contables obsoletas.'))
        currency = self.currency_id
        if self.journal_id.currency_id and self.journal_id.currency_id != currency:
            raise ValidationError(_('La moneda del banco debe coincidir con la moneda del deposito.'))
        for account in (bank, liability):
            if account.currency_id and account.currency_id != currency:
                raise ValidationError(_('La moneda de la cuenta contable no coincide con el deposito.'))
        return bank, liability

    def action_post(self):
        self.check_access('write')
        self.mapped('investment_id')._lock_investment_movements()
        self.invalidate_recordset()
        for rec in self:
            if rec.state != 'draft':
                continue
            investment = rec.investment_id
            if investment.state != 'active' or investment.interest_schedule != 'month_end':
                raise ValidationError(_('El deposito adicional requiere una cuenta activa con cierre a fin de mes.'))
            if rec.date < investment.start_date or (investment.maturity_date and rec.date >= investment.maturity_date):
                raise ValidationError(_('La fecha debe estar dentro de la vigencia de la cuenta; no cambia su vencimiento.'))
            if rec.date > fields.Date.context_today(rec):
                raise ValidationError(_('No se puede confirmar un deposito con fecha futura.'))
            if investment.interest_line_ids.filtered(lambda l: l.state != 'cancelled' and l.period_date >= rec.date):
                raise ValidationError(_('La fecha del deposito pertenece a un periodo de intereses ya calculado. Revise el cierre antes de registrar movimientos retroactivos.'))
            if investment.withdrawal_ids.filtered(lambda w: w.state == 'posted' and w.date > rec.date):
                raise ValidationError(_('No puede confirmar un deposito anterior a un retiro ya aplicado.'))
            if self.search_count([('investment_id', '=', investment.id), ('journal_id', '=', rec.journal_id.id),
                                  ('reference', '=', rec.reference.strip()), ('state', '=', 'posted'), ('id', '!=', rec.id)]):
                raise ValidationError(_('Esta referencia ya fue confirmada en la cuenta y banco seleccionados.'))
            bank, liability = rec._validate_accounting()
            company = rec.company_id
            amount = rec.currency_id.round(rec.amount)
            converted = rec.currency_id._convert(amount, company.currency_id, company, rec.date)
            if company.currency_id.is_zero(converted):
                raise ValidationError(_('El importe convertido no puede ser cero.'))
            move = self.env['account.move'].with_company(company).create({
                'move_type': 'entry', 'date': rec.date, 'journal_id': rec.journal_id.id,
                'ref': '%s - %s' % (rec.name, rec.reference.strip()),
                'line_ids': [(0, 0, {
                    'name': _('Deposito adicional - %s') % investment.name,
                    'partner_id': rec.partner_id.id, 'account_id': account.id,
                    'debit': converted if debit else 0, 'credit': 0 if debit else converted,
                    'currency_id': rec.currency_id.id, 'amount_currency': amount if debit else -amount,
                }) for account, debit in ((bank, True), (liability, False))],
            })
            super(LenkaInvestmentDeposit, rec).write({
                'state': 'posted', 'move_id': move.id, 'reference': rec.reference.strip(), 'amount': amount,
            })
        return True

    def _validate_move(self):
        """A draft may be reviewed; it must still match before publication."""
        for rec in self:
            move = rec.move_id
            bank, liability = rec._validate_accounting()
            expected = rec.currency_id._convert(rec.amount, rec.company_id.currency_id, rec.company_id, rec.date)
            if move.company_id != rec.company_id or move.journal_id != rec.journal_id or move.date != rec.date or move.move_type != 'entry' or len(move.line_ids) != 2:
                raise ValidationError(_('La partida no coincide con el deposito Lenka confirmado.'))
            for account, sign in ((bank, 1), (liability, -1)):
                lines = move.line_ids.filtered(lambda l: l.account_id == account)
                if len(lines) != 1 or lines.partner_id != rec.partner_id or lines.currency_id != rec.currency_id or not rec.currency_id.is_zero(lines.amount_currency - sign * rec.amount) or not rec.company_id.currency_id.is_zero(lines.balance - sign * expected):
                    raise ValidationError(_('La partida debe conservar el banco, inversionista, moneda e importe del deposito Lenka.'))

    def action_cancel(self):
        self.check_access('write')
        self.mapped('investment_id')._lock_investment_movements()
        self.invalidate_recordset()
        for rec in self:
            if rec.state == 'cancelled':
                continue
            if rec.move_id.state == 'posted':
                raise ValidationError(_('El deposito esta contabilizado. Requiere regularizacion contable; no se anula automaticamente.'))
            investment = rec.investment_id
            if rec.state == 'posted' and (
                investment.interest_line_ids.filtered(lambda l: l.state != 'cancelled' and l.period_date >= rec.date) or
                investment.withdrawal_ids.filtered(lambda w: w.state == 'posted' and w.date >= rec.date)
            ):
                raise ValidationError(_('Existen intereses o retiros posteriores; revise esos movimientos antes de anular el deposito.'))
            super(LenkaInvestmentDeposit, rec).write({'state': 'cancelled'})
            if rec.move_id and rec.move_id.state == 'draft':
                rec.move_id.button_cancel()
        return True


class AccountMoveInvestmentDeposit(models.Model):
    _inherit = 'account.move'

    def _check_lenka_deposit_unlinked(self):
        if self and self.env['lenka.investment.deposit'].sudo().search_count([
            ('move_id', 'in', self.ids), ('state', '=', 'posted'), ('move_id.state', '=', 'posted'),
        ]):
            raise ValidationError(_('La partida respalda un deposito Lenka confirmado. Requiere regularizacion antes de modificar o revertir su contabilidad.'))

    def write(self, vals):
        if {'state', 'line_ids', 'date', 'company_id', 'journal_id', 'move_type', 'reversed_entry_id'}.intersection(vals):
            self._check_lenka_deposit_unlinked()
        result = super().write(vals)
        if vals.get('state') == 'posted':
            deposits = self.env['lenka.investment.deposit'].sudo().search([('move_id', 'in', self.ids)])
            if deposits.filtered(lambda d: d.state != 'posted'):
                raise ValidationError(_('No puede publicar la partida de un deposito anulado.'))
            deposits._validate_move()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        self.browse([v['reversed_entry_id'] for v in vals_list if v.get('reversed_entry_id')])._check_lenka_deposit_unlinked()
        return super().create(vals_list)

    def unlink(self):
        self._check_lenka_deposit_unlinked()
        return super().unlink()
