from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LenkaFundingCost(models.Model):
    _name = 'lenka.funding.cost'
    _description = 'Costo Real de Fondeo Lenka'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(default='Nuevo', readonly=True, copy=False)
    funding_line_id = fields.Many2one('lenka.funding.line', string='Fuente de fondeo', required=True, ondelete='restrict')
    operation_id = fields.Many2one(related='funding_line_id.operation_id', store=True, string='Operacion')
    company_id = fields.Many2one(related='operation_id.company_id', store=True)
    currency_id = fields.Many2one(related='operation_id.currency_id', store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    cost_type = fields.Selection([
        ('interest', 'Interes'),
        ('bank_fee', 'Comision bancaria'),
        ('card_interest', 'Interes / cargo de tarjeta empresarial'),
        ('investor_interest', 'Interes pagado a inversionista'),
        ('third_party_cost', 'Costo de fondos de terceros'),
        ('other', 'Otro costo financiero'),
    ], string='Tipo de costo', required=True, default='interest')
    partner_id = fields.Many2one('res.partner', string='Banco / Inversionista / Tercero')
    amount = fields.Monetary(string='Costo real', required=True, tracking=True)
    reference = fields.Char(string='Referencia')
    notes = fields.Text()
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('posted', 'Aplicado'),
        ('cancelled', 'Anulado'),
    ], default='draft', tracking=True)
    move_id = fields.Many2one('account.move', string='Partida contable', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('lenka.funding.cost') or 'Nuevo'
        return super().create(vals_list)

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('El costo de fondeo debe ser mayor que cero.'))

    def action_post(self):
        for rec in self:
            if rec.state != 'draft':
                continue
            if rec.funding_line_id.operation_id.state not in ('approved', 'contracted', 'active', 'done'):
                raise ValidationError(_('La operacion debe estar aprobada, contratada o activa para registrar costos de fondeo.'))
            rec.state = 'posted'
        return True

    def action_cancel(self):
        for rec in self:
            if rec.move_id:
                raise ValidationError(_('No puede anularse un costo de fondeo que ya tiene partida contable.'))
            rec.state = 'cancelled'
        return True


class LenkaFundingLineActualCost(models.Model):
    _inherit = 'lenka.funding.line'

    cost_ids = fields.One2many('lenka.funding.cost', 'funding_line_id', string='Costos reales')
    actual_cost = fields.Monetary(
        string='Costo real acumulado',
        compute='_compute_actual_cost',
        currency_field='currency_id',
    )

    @api.depends('cost_ids.state', 'cost_ids.amount')
    def _compute_actual_cost(self):
        for line in self:
            line.actual_cost = sum(line.cost_ids.filtered(lambda c: c.state == 'posted').mapped('amount'))


class LenkaFinancialOperationActualFundingCost(models.Model):
    _inherit = 'lenka.financial.operation'

    funding_cost_ids = fields.One2many(
        'lenka.funding.cost',
        'operation_id',
        string='Costos reales de fondeo',
        readonly=True,
    )
    realized_funding_cost = fields.Monetary(
        string='Costo real de fondeo',
        compute='_compute_realized_funding_cost',
        currency_field='currency_id',
    )
    realized_net_financial_margin = fields.Monetary(
        string='Margen financiero neto realizado',
        compute='_compute_realized_funding_cost',
        currency_field='currency_id',
    )

    @api.depends(
        'funding_cost_ids.state',
        'funding_cost_ids.amount',
        'realized_interest_income',
        'realized_late_income',
        'realized_card_fees',
    )
    def _compute_realized_funding_cost(self):
        for rec in self:
            costs = rec.funding_cost_ids.filtered(lambda c: c.state == 'posted')
            rec.realized_funding_cost = sum(costs.mapped('amount'))
            rec.realized_net_financial_margin = (
                rec.realized_interest_income
                + rec.realized_late_income
                - rec.realized_card_fees
                - rec.realized_funding_cost
            )


class LenkaFundingCostAccounting(models.Model):
    _inherit = 'lenka.funding.cost'

    journal_id = fields.Many2one('account.journal', string='Diario de pago / costo')

    def action_create_account_move(self):
        for rec in self:
            if rec.state != 'posted':
                raise ValidationError(_('El costo de fondeo debe estar aplicado antes de crear la partida contable.'))
            if rec.move_id:
                continue
            company = rec.company_id
            journal = rec.journal_id
            expense = company.lenka_funding_cost_expense_account_id
            if not journal or not expense:
                raise ValidationError(_('Configure el diario del costo y la cuenta de gasto por costo de fondeo.'))
            if journal.company_id != company:
                raise ValidationError(_('El diario debe pertenecer a la misma empresa de la operacion.'))
            counterpart = journal.default_account_id
            if not counterpart:
                raise ValidationError(_('El diario seleccionado debe tener una cuenta contable por defecto.'))

            amount_company = rec.currency_id._convert(rec.amount, company.currency_id, company, rec.date)
            move = self.env['account.move'].with_company(company).create({
                'move_type': 'entry',
                'date': rec.date,
                'journal_id': journal.id,
                'ref': '%s - %s' % (rec.operation_id.name, rec.name),
                'line_ids': [
                    (0, 0, {
                        'name': _('Costo de fondeo - %s') % rec.name,
                        'partner_id': rec.partner_id.id if rec.partner_id else False,
                        'account_id': expense.id,
                        'debit': amount_company,
                        'credit': 0.0,
                        'currency_id': rec.currency_id.id,
                        'amount_currency': rec.amount,
                    }),
                    (0, 0, {
                        'name': _('Pago / obligacion costo de fondeo - %s') % rec.name,
                        'partner_id': rec.partner_id.id if rec.partner_id else False,
                        'account_id': counterpart.id,
                        'debit': 0.0,
                        'credit': amount_company,
                        'currency_id': rec.currency_id.id,
                        'amount_currency': -rec.amount,
                    }),
                ],
            })
            rec.move_id = move.id
        return True

    def action_open_account_move(self):
        self.ensure_one()
        if not self.move_id:
            raise ValidationError(_('Este costo de fondeo aun no tiene borrador contable.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Borrador contable'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.move_id.id,
            'target': 'current',
        }
