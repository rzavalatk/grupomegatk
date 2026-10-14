from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResCompanyLenkaInvestmentAccounting(models.Model):
    _inherit = 'res.company'

    lenka_investment_journal_id = fields.Many2one('account.journal', string='Lenka: Diario de inversiones')
    lenka_investor_liability_account_id = fields.Many2one('account.account', string='Lenka: Obligacion con inversionistas')
    lenka_passive_interest_expense_account_id = fields.Many2one('account.account', string='Lenka: Gasto por intereses pasivos')
    lenka_passive_interest_tax_payable_account_id = fields.Many2one('account.account', string='Lenka: Retencion por pagar sobre intereses pasivos')


class ResConfigSettingsLenkaInvestmentAccounting(models.TransientModel):
    _inherit = 'res.config.settings'

    lenka_investment_journal_id = fields.Many2one(related='company_id.lenka_investment_journal_id', readonly=False)
    lenka_investor_liability_account_id = fields.Many2one(related='company_id.lenka_investor_liability_account_id', readonly=False)
    lenka_passive_interest_expense_account_id = fields.Many2one(related='company_id.lenka_passive_interest_expense_account_id', readonly=False)
    lenka_passive_interest_tax_payable_account_id = fields.Many2one(related='company_id.lenka_passive_interest_tax_payable_account_id', readonly=False)


class LenkaInvestmentAccounting(models.Model):
    _inherit = 'lenka.investment'

    receipt_move_id = fields.Many2one('account.move', string='Partida de recepcion', readonly=True, copy=False, ondelete='restrict')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if any(vals.get(key) for key in ('receipt_move_id',)):
                raise ValidationError(_('Genere las partidas mediante las acciones contables de Lenka.'))
            for key in ('receipt_move_id',):
                vals[key] = False
        return super().create(vals_list)

    def write(self, vals):
        for key in ('receipt_move_id',):
            if key in vals and any(rec[key].id != vals[key] for rec in self):
                raise ValidationError(_('No puede reemplazar ni desvincular las partidas contables de Lenka.'))
        return super().write(vals)

    def action_create_receipt_move(self):
        for rec in self:
            if rec.state not in ('active', 'matured', 'closed'):
                raise ValidationError(_('La inversion debe estar activa antes de contabilizar la recepcion.'))
            if rec.receipt_move_id:
                continue
            company = rec.company_id
            journal = company.lenka_investment_journal_id
            liability = company.lenka_investor_liability_account_id
            if not journal or not liability:
                raise ValidationError(_('Configure el diario de inversiones y la cuenta de obligacion con inversionistas.'))
            if journal.company_id != company:
                raise ValidationError(_('El diario de inversiones debe pertenecer a la misma empresa.'))
            liquidity = journal.default_account_id
            if not liquidity:
                raise ValidationError(_('El diario de inversiones debe tener una cuenta contable por defecto.'))
            amount_company = rec.currency_id._convert(rec.principal_amount, company.currency_id, company, rec.start_date)
            lines = [
                (0, 0, {
                    'name': _('Deposito recibido - %s') % rec.name,
                    'partner_id': rec.partner_id.id,
                    'account_id': liquidity.id,
                    'debit': amount_company,
                    'credit': 0.0,
                    'currency_id': rec.currency_id.id,
                    'amount_currency': rec.principal_amount,
                }),
                (0, 0, {
                    'name': _('Obligacion con inversionista - %s') % rec.name,
                    'partner_id': rec.partner_id.id,
                    'account_id': liability.id,
                    'debit': 0.0,
                    'credit': amount_company,
                    'currency_id': rec.currency_id.id,
                    'amount_currency': -rec.principal_amount,
                }),
            ]
            move = self.env['account.move'].with_company(company).create({
                'move_type': 'entry',
                'date': rec.start_date,
                'journal_id': journal.id,
                'ref': '%s - Recepcion deposito' % rec.name,
                'line_ids': lines,
            })
            super(LenkaInvestmentAccounting, rec).write({'receipt_move_id': move.id})
        return True


class LenkaInvestmentInterestAccounting(models.Model):
    _inherit = 'lenka.investment.interest'

    move_id = fields.Many2one('account.move', string='Partida contable', readonly=True, copy=False, ondelete='restrict')
    adjustment_move_id = fields.Many2one('account.move', string='Partida de ajuste', readonly=True, copy=False, ondelete='restrict')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if any(vals.get(key) for key in ('move_id', 'adjustment_move_id')):
                raise ValidationError(_('Genere las partidas mediante las acciones contables de Lenka.'))
            for key in ('move_id', 'adjustment_move_id'):
                vals[key] = False
        return super().create(vals_list)

    def write(self, vals):
        for key in ('move_id', 'adjustment_move_id'):
            if key in vals and any(rec[key].id != vals[key] for rec in self):
                raise ValidationError(_('No puede reemplazar ni desvincular las partidas contables de Lenka.'))
        return super().write(vals)

    def action_create_account_move(self):
        for rec in self:
            if rec.state not in ('accrued', 'paid'):
                raise ValidationError(_('El interes debe estar devengado antes de contabilizarse.'))
            if rec.move_id:
                continue
            investment = rec.investment_id
            company = investment.company_id
            journal = company.lenka_investment_journal_id
            liability = company.lenka_investor_liability_account_id
            expense = company.lenka_passive_interest_expense_account_id
            tax_payable = company.lenka_passive_interest_tax_payable_account_id
            if not journal or not liability or not expense:
                raise ValidationError(_('Configure diario, obligacion con inversionistas y gasto de intereses pasivos.'))
            if rec.tax_amount and not tax_payable:
                raise ValidationError(_('Configure la cuenta de retencion por pagar sobre intereses pasivos.'))
            if journal.company_id != company:
                raise ValidationError(_('El diario de inversiones debe pertenecer a la misma empresa.'))
            gross_company = investment.currency_id._convert(rec.amount, company.currency_id, company, rec.period_date)
            net_company = investment.currency_id._convert(rec.net_amount, company.currency_id, company, rec.period_date)
            tax_company = investment.currency_id._convert(rec.tax_amount, company.currency_id, company, rec.period_date)
            lines = [
                (0, 0, {
                    'name': _('Gasto interes pasivo - %s') % investment.name,
                    'partner_id': investment.partner_id.id,
                    'account_id': expense.id,
                    'debit': gross_company,
                    'credit': 0.0,
                    'currency_id': investment.currency_id.id,
                    'amount_currency': rec.amount,
                }),
                (0, 0, {
                    'name': _('Interes neto por pagar / capitalizar - %s') % investment.name,
                    'partner_id': investment.partner_id.id,
                    'account_id': liability.id,
                    'debit': 0.0,
                    'credit': net_company,
                    'currency_id': investment.currency_id.id,
                    'amount_currency': -rec.net_amount,
                }),
            ]
            if rec.tax_amount:
                lines.append((0, 0, {
                    'name': _('Retencion sobre intereses pasivos - %s') % investment.name,
                    'partner_id': investment.partner_id.id,
                    'account_id': tax_payable.id,
                    'debit': 0.0,
                    'credit': tax_company,
                    'currency_id': investment.currency_id.id,
                    'amount_currency': -rec.tax_amount,
                }))
            move = self.env['account.move'].with_company(company).create({
                'move_type': 'entry',
                'date': rec.period_date,
                'journal_id': journal.id,
                'ref': '%s - Interes pasivo' % investment.name,
                'line_ids': lines,
            })
            super(LenkaInvestmentInterestAccounting, rec).write({'move_id': move.id})
        return True


class LenkaInvestmentWithdrawalAccounting(models.Model):
    _inherit = 'lenka.investment.withdrawal'

    move_id = fields.Many2one('account.move', string='Partida contable', readonly=True, copy=False, ondelete='restrict')
    adjustment_move_id = fields.Many2one('account.move', string='Ajuste por retiro anticipado', readonly=True, copy=False, ondelete='restrict')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if any(vals.get(key) for key in ('move_id', 'adjustment_move_id')):
                raise ValidationError(_('Genere las partidas mediante las acciones contables de Lenka.'))
            for key in ('move_id', 'adjustment_move_id'):
                vals[key] = False
        return super().create(vals_list)

    def write(self, vals):
        for key in ('move_id', 'adjustment_move_id'):
            if key in vals and any(rec[key].id != vals[key] for rec in self):
                raise ValidationError(_('No puede reemplazar ni desvincular las partidas contables de Lenka.'))
        return super().write(vals)

    def action_create_early_withdrawal_adjustment(self):
        for rec in self:
            if rec.state != 'posted':
                raise ValidationError(_('Aplique el retiro antes de preparar su ajuste contable.'))
            if not rec.early_withdrawal:
                continue
            investment = rec.investment_id
            previous = investment.withdrawal_ids.filtered(
                lambda w: w.state == 'posted' and w.early_withdrawal and
                (w.date, w.id) < (rec.date, rec.id)
            )
            if previous:
                # Los retiros posteriores ya usan la tasa reducida; no revierten
                # nuevamente los intereses historicos del primer retiro.
                continue
            company = investment.company_id
            journal = company.lenka_investment_journal_id
            liability = company.lenka_investor_liability_account_id
            expense = company.lenka_passive_interest_expense_account_id
            if not journal or not liability or not expense:
                raise ValidationError(_('Configure diario, obligacion con inversionistas y gasto de intereses pasivos.'))
            if journal.company_id != company:
                raise ValidationError(_('El diario de inversiones debe pertenecer a la misma empresa.'))
            if rec.adjustment_move_id:
                continue

            contractual_interest = sum(
                investment.interest_line_ids.filtered(
                    lambda l: l.period_date <= rec.date and l.move_id
                ).mapped('amount')
            )
            # Compare gross with gross: withholding is a separate liability,
            # not an additional reduction of the contractual interest expense.
            recalculated_interest = rec.gross_interest_amount
            difference = contractual_interest - recalculated_interest
            if difference <= 0:
                continue

            amount_company = investment.currency_id._convert(difference, company.currency_id, company, rec.date)
            move = self.env['account.move'].with_company(company).create({
                'move_type': 'entry',
                'date': rec.date,
                'journal_id': journal.id,
                'ref': '%s - Ajuste retiro anticipado' % investment.name,
                'line_ids': [
                    (0, 0, {
                        'name': _('Disminucion obligacion por tasa penalizada - %s') % investment.name,
                        'partner_id': investment.partner_id.id,
                        'account_id': liability.id,
                        'debit': amount_company,
                        'credit': 0.0,
                        'currency_id': investment.currency_id.id,
                        'amount_currency': difference,
                    }),
                    (0, 0, {
                        'name': _('Reversion gasto interes pasivo - %s') % investment.name,
                        'partner_id': investment.partner_id.id,
                        'account_id': expense.id,
                        'debit': 0.0,
                        'credit': amount_company,
                        'currency_id': investment.currency_id.id,
                        'amount_currency': -difference,
                    }),
                ],
            })
            super(LenkaInvestmentWithdrawalAccounting, rec).write({'adjustment_move_id': move.id})
        return True

    def action_create_account_move(self):
        for rec in self:
            if rec.state != 'posted':
                raise ValidationError(_('El retiro debe estar aplicado antes de contabilizarse.'))
            if rec.early_withdrawal:
                rec.action_create_early_withdrawal_adjustment()
            if rec.move_id:
                continue
            investment = rec.investment_id
            company = investment.company_id
            journal = company.lenka_investment_journal_id
            liability = company.lenka_investor_liability_account_id
            if not journal or not liability:
                raise ValidationError(_('Configure el diario de inversiones y la cuenta de obligacion con inversionistas.'))
            if journal.company_id != company:
                raise ValidationError(_('El diario de inversiones debe pertenecer a la misma empresa.'))
            liquidity = journal.default_account_id
            if not liquidity:
                raise ValidationError(_('El diario de inversiones debe tener una cuenta contable por defecto.'))
            amount = rec.total_amount
            # La obligacion contable se reduce por capital + interes neto pagado.
            # La retencion sobre intereses queda separada en su cuenta por pagar.
            amount_company = investment.currency_id._convert(amount, company.currency_id, company, rec.date)
            move = self.env['account.move'].with_company(company).create({
                'move_type': 'entry',
                'date': rec.date,
                'journal_id': journal.id,
                'ref': '%s - Retiro inversionista' % investment.name,
                'line_ids': [
                    (0, 0, {
                        'name': _('Disminucion obligacion inversionista - %s') % investment.name,
                        'partner_id': investment.partner_id.id,
                        'account_id': liability.id,
                        'debit': amount_company,
                        'credit': 0.0,
                        'currency_id': investment.currency_id.id,
                        'amount_currency': amount,
                    }),
                    (0, 0, {
                        'name': _('Pago a inversionista - %s') % investment.name,
                        'partner_id': investment.partner_id.id,
                        'account_id': liquidity.id,
                        'debit': 0.0,
                        'credit': amount_company,
                        'currency_id': investment.currency_id.id,
                        'amount_currency': -amount,
                    }),
                ],
            })
            super(LenkaInvestmentWithdrawalAccounting, rec).write({'move_id': move.id})
        return True
