from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LenkaDisbursementSources(models.Model):
    _inherit = 'lenka.disbursement'

    disbursement_journal_id = fields.Many2one(
        'account.journal', string='Banco / diario de salida', tracking=True)

    @api.onchange('operation_id', 'payment_method')
    def _onchange_disbursement_journal(self):
        if self.payment_method != 'refinance_entry' and self.operation_id:
            self.disbursement_journal_id = self.operation_id.company_id.lenka_disbursement_journal_id

    def write(self, vals):
        if 'disbursement_journal_id' in vals and any(r.state != 'draft' for r in self):
            raise ValidationError(_('No puede cambiar el banco de un desembolso aplicado.'))
        return super().write(vals)

    def _disbursement_accounts(self):
        self.ensure_one()
        company = self.operation_id.company_id
        journal = self.disbursement_journal_id or company.lenka_disbursement_journal_id
        portfolio = company.lenka_portfolio_account_id
        if not journal or not portfolio or not journal.default_account_id:
            raise ValidationError(_('Seleccione el diario de salida con su cuenta contable y configure la cartera Lenka.'))
        journal.check_access('read')
        portfolio.check_access('read')
        if journal.company_id != company or company not in portfolio.company_ids:
            raise ValidationError(_('El diario y la cartera deben pertenecer a la empresa del prestamo.'))
        if journal.currency_id and journal.currency_id != self.currency_id:
            raise ValidationError(_('La moneda del diario debe coincidir con la moneda del desembolso.'))
        account = journal.default_account_id
        if self.payment_method == 'credit_card':
            if journal.type != 'general' or account.account_type != 'liability_current':
                raise ValidationError(_('Para tarjeta seleccione un diario general cuya cuenta por defecto sea la obligacion de tarjeta (pasivo corriente).'))
        elif self.disbursement_journal_id:
            if self.payment_method in ('check', 'transfer') and (journal.type != 'bank' or account.account_type != 'asset_cash'):
                raise ValidationError(_('Para cheque o transferencia seleccione un diario bancario con su cuenta de banco.'))
            if self.payment_method == 'cash' and (journal.type != 'cash' or account.account_type != 'asset_cash'):
                raise ValidationError(_('Para efectivo seleccione un diario de caja con su cuenta de efectivo.'))
        return journal, portfolio, account

    def action_post(self):
        for rec in self.filtered(lambda r: r.state == 'draft' and r.disbursement_journal_id and r.payment_method != 'refinance_entry'):
            rec._disbursement_accounts()
        return super().action_post()

    def _prepare_disbursement_move(self):
        self.ensure_one()
        if self.payment_method == 'refinance_entry':
            return super()._prepare_disbursement_move()
        journal, portfolio, account = self._disbursement_accounts()
        company = self.operation_id.company_id
        amount = self.currency_id._convert(self.amount, company.currency_id, company, self.date)
        reference = '%s - %s - %s' % (self.operation_id.name, self.name, self.reference or '')
        return {
            'move_type': 'entry', 'date': self.date, 'journal_id': journal.id, 'ref': reference,
            'line_ids': [(0, 0, {
                'name': _('Capital financiado - %s') % self.operation_id.name,
                'partner_id': self.operation_id.partner_id.id, 'account_id': portfolio.id,
                'debit': amount, 'credit': 0.0, 'currency_id': self.currency_id.id,
                'amount_currency': self.amount,
            }), (0, 0, {
                'name': '%s - %s' % (dict(self._fields['payment_method']._description_selection(self.env)).get(self.payment_method), self.reference or self.name),
                'partner_id': (self.destination_partner_id or self.operation_id.partner_id).id,
                'account_id': account.id, 'debit': 0.0, 'credit': amount,
                'currency_id': self.currency_id.id, 'amount_currency': -self.amount,
            })],
        }

    def action_create_account_move(self):
        self.check_access('write')
        self._lock_operations()
        return super().action_create_account_move()
