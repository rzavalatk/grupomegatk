from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LenkaFinancialOperationProfitability(models.Model):
    _inherit = 'lenka.financial.operation'

    projected_interest_income = fields.Monetary(
        string='Interes proyectado',
        compute='_compute_profitability',
        currency_field='currency_id',
    )
    funding_total = fields.Monetary(
        string='Fondeo total',
        compute='_compute_profitability',
        currency_field='currency_id',
    )
    weighted_funding_monthly_rate = fields.Float(
        string='Costo mensual ponderado fondeo (%)',
        compute='_compute_profitability',
    )
    projected_funding_cost = fields.Monetary(
        string='Costo proyectado del fondeo',
        compute='_compute_profitability',
        currency_field='currency_id',
    )
    projected_financial_margin = fields.Monetary(
        string='Margen financiero proyectado',
        compute='_compute_profitability',
        currency_field='currency_id',
    )
    realized_interest_income = fields.Monetary(
        string='Interes cobrado',
        compute='_compute_profitability',
        currency_field='currency_id',
    )
    realized_late_income = fields.Monetary(
        string='Mora cobrada',
        compute='_compute_profitability',
        currency_field='currency_id',
    )
    realized_card_fees = fields.Monetary(
        string='Costo comisiones tarjeta',
        compute='_compute_profitability',
        currency_field='currency_id',
    )
    realized_financial_margin = fields.Monetary(
        string='Margen realizado antes de costo fondeo',
        compute='_compute_profitability',
        currency_field='currency_id',
    )

    @api.depends(
        'schedule_line_ids.interest',
        'funding_line_ids.amount',
        'funding_line_ids.cost_rate',
        'funding_line_ids.cost_period',
        'term_months',
        'payment_ids.state',
        'payment_ids.interest_amount',
        'payment_ids.late_fee_amount',
        'payment_ids.card_fee_amount',
    )
    def _compute_profitability(self):
        for rec in self:
            rec.projected_interest_income = sum(rec.schedule_line_ids.mapped('interest'))
            rec.funding_total = sum(rec.funding_line_ids.mapped('amount'))

            weighted_sum = 0.0
            projected_cost = 0.0
            for line in rec.funding_line_ids:
                if line.amount <= 0:
                    continue
                monthly_rate = line.cost_rate / 100.0 if line.cost_period == 'monthly' else line.cost_rate / 1200.0
                weighted_sum += line.amount * monthly_rate
                projected_cost += line.amount * monthly_rate * rec.term_months

            if rec.funding_total > 0:
                rec.weighted_funding_monthly_rate = (weighted_sum / rec.funding_total) * 100.0
            else:
                rec.weighted_funding_monthly_rate = 0.0

            rec.projected_funding_cost = projected_cost
            rec.projected_financial_margin = rec.projected_interest_income - projected_cost

            posted = rec.payment_ids.filtered(lambda p: p.state == 'posted')
            rec.realized_interest_income = sum(posted.mapped('interest_amount'))
            rec.realized_late_income = sum(posted.mapped('late_fee_amount'))
            rec.realized_card_fees = sum(posted.mapped('card_fee_amount'))
            rec.realized_financial_margin = (
                rec.realized_interest_income
                + rec.realized_late_income
                - rec.realized_card_fees
            )

    @api.constrains('funding_line_ids', 'financed_amount')
    def _check_funding_coverage(self):
        for rec in self.filtered(lambda r: r.funding_line_ids and not r.is_quote):
            total = sum(rec.funding_line_ids.mapped('amount'))
            if total > rec.financed_amount + 0.01:
                raise ValidationError(
                    _('El fondeo asignado no puede exceder el monto financiado de la operacion.')
                )


class LenkaFundingLineProfitability(models.Model):
    _inherit = 'lenka.funding.line'

    monthly_cost_rate = fields.Float(
        string='Costo mensual equivalente (%)',
        compute='_compute_funding_metrics',
    )
    projected_cost = fields.Monetary(
        string='Costo proyectado',
        compute='_compute_funding_metrics',
        currency_field='currency_id',
    )
    funding_share = fields.Float(
        string='% del fondeo',
        compute='_compute_funding_metrics',
    )

    @api.depends('amount', 'cost_rate', 'cost_period', 'operation_id.term_months', 'operation_id.financed_amount')
    def _compute_funding_metrics(self):
        for line in self:
            monthly_rate = line.cost_rate if line.cost_period == 'monthly' else line.cost_rate / 12.0
            line.monthly_cost_rate = monthly_rate
            line.projected_cost = line.amount * (monthly_rate / 100.0) * line.operation_id.term_months
            financed = line.operation_id.financed_amount
            line.funding_share = (line.amount / financed * 100.0) if financed else 0.0
