from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class LenkaMobileService(models.AbstractModel):
    _name = 'lenka.mobile.service'
    _description = 'Servicio Movil Seguro Lenka'

    @api.model
    def _current_partner(self):
        user = self.env.user
        partner = user.partner_id
        if not partner:
            raise AccessError(_('El usuario autenticado no tiene un contacto asociado.'))
        commercial_partner = partner.commercial_partner_id
        if not user.has_group('lenka_financiero.group_lenka_mobile_client'):
            raise AccessError(_('El usuario no tiene habilitado el acceso a la app Financiero Lenka.'))
        if not commercial_partner.lenka_mobile_enabled:
            raise AccessError(_('El acceso movil de este cliente esta deshabilitado.'))
        return commercial_partner

    @api.model
    def _partner_domain(self, field_name='partner_id'):
        partner = self._current_partner()
        return [(field_name, 'child_of', partner.id)]

    @api.model
    def get_my_dashboard(self):
        partner = self._current_partner()
        operations = self.env['lenka.financial.operation'].sudo().search([
            ('partner_id', 'child_of', partner.id),
            ('is_quote', '=', False),
            ('state', 'in', ('approved', 'contracted', 'active', 'done')),
        ])
        investments = self.env['lenka.investment'].sudo().search([
            ('partner_id', 'child_of', partner.id),
            ('state', 'in', ('active', 'matured', 'closed')),
        ])
        statements = self.env['lenka.statement'].sudo().search([
            ('partner_id', 'child_of', partner.id),
            ('state', 'in', ('generated', 'sent')),
        ], order='date_to desc', limit=5)

        return {
            'partner': {
                'id': partner.id,
                'name': partner.display_name,
                'email': partner.email or '',
                'phone': partner.phone or partner.mobile or '',
            },
            'operations': {
                'count': len(operations),
                'outstanding_capital': sum(operations.mapped('outstanding_capital')),
                'paid_interest': sum(operations.mapped('paid_interest')),
                'paid_late_fees': sum(operations.mapped('paid_late_fees')),
            },
            'investments': {
                'count': len(investments),
                'outstanding_principal': sum(investments.mapped('outstanding_principal')),
                'accrued_interest': sum(investments.mapped('accrued_interest')),
            },
            'recent_statements': [{
                'id': statement.id,
                'name': statement.name,
                'type': statement.statement_type,
                'date_from': fields.Date.to_string(statement.date_from),
                'date_to': fields.Date.to_string(statement.date_to),
                'closing_balance': statement.closing_balance,
                'currency': statement.currency_id.name,
                'state': statement.state,
            } for statement in statements],
        }

    @api.model
    def get_my_operations(self):
        partner = self._current_partner()
        operations = self.env['lenka.financial.operation'].sudo().search([
            ('partner_id', 'child_of', partner.id),
            ('is_quote', '=', False),
            ('state', 'not in', ('draft', 'review', 'rejected', 'cancelled')),
        ], order='date desc, id desc')

        result = []
        for operation in operations:
            next_line = operation.schedule_line_ids.filtered(
                lambda l: l.payment_state != 'paid'
            ).sorted(key=lambda l: (l.date or fields.Date.today(), l.sequence))[:1]
            result.append({
                'id': operation.id,
                'name': operation.name,
                'type': operation.operation_type,
                'state': operation.state,
                'currency': operation.currency_id.name,
                'principal_amount': operation.principal_amount,
                'financed_amount': operation.financed_amount,
                'outstanding_capital': operation.outstanding_capital,
                'interest_rate': operation.interest_rate,
                'rate_period': operation.rate_period,
                'term_months': operation.term_months,
                'next_payment': {
                    'sequence': next_line.sequence,
                    'date': fields.Date.to_string(next_line.date) if next_line.date else False,
                    'amount_due': next_line.amount_due,
                    'state': next_line.payment_state,
                } if next_line else False,
            })
        return result

    @api.model
    def get_my_operation_detail(self, operation_id):
        partner = self._current_partner()
        operation = self.env['lenka.financial.operation'].sudo().search([
            ('id', '=', int(operation_id)),
            ('partner_id', 'child_of', partner.id),
            ('is_quote', '=', False),
        ], limit=1)
        if not operation:
            raise AccessError(_('La operacion solicitada no pertenece al usuario autenticado.'))

        return {
            'id': operation.id,
            'name': operation.name,
            'type': operation.operation_type,
            'state': operation.state,
            'currency': operation.currency_id.name,
            'principal_amount': operation.principal_amount,
            'down_payment': operation.down_payment,
            'financed_amount': operation.financed_amount,
            'outstanding_capital': operation.outstanding_capital,
            'interest_rate': operation.interest_rate,
            'rate_period': operation.rate_period,
            'term_months': operation.term_months,
            'first_payment_date': fields.Date.to_string(operation.first_payment_date) if operation.first_payment_date else False,
            'schedule': [{
                'sequence': line.sequence,
                'date': fields.Date.to_string(line.date),
                'capital': line.capital,
                'interest': line.interest,
                'late_fee_due': line.late_fee_due,
                'amount_due': line.amount_due,
                'payment_state': line.payment_state,
                'closing_balance': line.closing_balance,
            } for line in operation.schedule_line_ids.sorted('sequence')],
            'payments': [{
                'id': payment.id,
                'name': payment.name,
                'date': fields.Date.to_string(payment.payment_date),
                'gross_amount': payment.amount,
                'net_amount': payment.net_bank_amount,
                'card_fee': payment.card_fee_amount,
                'late_fee': payment.late_fee_amount,
                'interest': payment.interest_amount,
                'capital': payment.capital_amount,
                'state': payment.state,
            } for payment in operation.payment_ids.filtered(lambda p: p.state == 'posted').sorted('payment_date', reverse=True)],
        }

    @api.model
    def get_my_investments(self):
        partner = self._current_partner()
        investments = self.env['lenka.investment'].sudo().search([
            ('partner_id', 'child_of', partner.id),
            ('state', 'not in', ('draft', 'cancelled')),
        ], order='start_date desc, id desc')

        return [{
            'id': investment.id,
            'name': investment.name,
            'type': investment.investment_type,
            'state': investment.state,
            'currency': investment.currency_id.name,
            'principal_amount': investment.principal_amount,
            'outstanding_principal': investment.outstanding_principal,
            'accrued_interest': investment.accrued_interest,
            'passive_rate': investment.passive_rate,
            'early_withdrawal_rate': investment.early_withdrawal_rate,
            'rate_period': investment.rate_period,
            'start_date': fields.Date.to_string(investment.start_date),
            'maturity_date': fields.Date.to_string(investment.maturity_date) if investment.maturity_date else False,
            'capitalization': investment.capitalization,
        } for investment in investments]

    @api.model
    def get_my_investment_detail(self, investment_id):
        partner = self._current_partner()
        investment = self.env['lenka.investment'].sudo().search([
            ('id', '=', int(investment_id)),
            ('partner_id', 'child_of', partner.id),
        ], limit=1)
        if not investment:
            raise AccessError(_('La inversion solicitada no pertenece al usuario autenticado.'))

        return {
            'id': investment.id,
            'name': investment.name,
            'state': investment.state,
            'currency': investment.currency_id.name,
            'principal_amount': investment.principal_amount,
            'outstanding_principal': investment.outstanding_principal,
            'accrued_interest': investment.accrued_interest,
            'paid_interest': investment.paid_interest,
            'passive_rate': investment.passive_rate,
            'early_withdrawal_rate': investment.early_withdrawal_rate,
            'rate_period': investment.rate_period,
            'start_date': fields.Date.to_string(investment.start_date),
            'maturity_date': fields.Date.to_string(investment.maturity_date) if investment.maturity_date else False,
            'interest_history': [{
                'date': fields.Date.to_string(line.period_date),
                'base_amount': line.base_amount,
                'rate': line.rate,
                'amount': line.amount,
                'state': line.state,
            } for line in investment.interest_line_ids.sorted('period_date', reverse=True)],
            'withdrawals': [{
                'date': fields.Date.to_string(withdrawal.date),
                'principal_amount': withdrawal.principal_amount,
                'interest_amount': withdrawal.accrued_interest_amount,
                'effective_rate': withdrawal.effective_rate,
                'total_amount': withdrawal.total_amount,
                'early_withdrawal': withdrawal.early_withdrawal,
            } for withdrawal in investment.withdrawal_ids.filtered(lambda w: w.state == 'posted').sorted('date', reverse=True)],
        }

    @api.model
    def get_my_statements(self):
        partner = self._current_partner()
        statements = self.env['lenka.statement'].sudo().search([
            ('partner_id', 'child_of', partner.id),
            ('state', 'in', ('generated', 'sent')),
        ], order='date_to desc, id desc')

        return [{
            'id': statement.id,
            'name': statement.name,
            'type': statement.statement_type,
            'date_from': fields.Date.to_string(statement.date_from),
            'date_to': fields.Date.to_string(statement.date_to),
            'opening_balance': statement.opening_balance,
            'closing_balance': statement.closing_balance,
            'period_capital': statement.period_capital,
            'period_interest': statement.period_interest,
            'period_late_fees': statement.period_late_fees,
            'period_fees': statement.period_fees,
            'currency': statement.currency_id.name,
            'state': statement.state,
        } for statement in statements]
