from calendar import monthrange
from datetime import date, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LenkaStatement(models.Model):
    _name = 'lenka.statement'
    _description = 'Estado de Cuenta Lenka'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_to desc, id desc'

    name = fields.Char(default='Nuevo', readonly=True, copy=False)
    statement_type = fields.Selection([
        ('operation', 'Prestamo / Financiamiento / Arrendamiento'),
        ('investment', 'Inversion / Deposito'),
    ], required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True)
    operation_id = fields.Many2one('lenka.financial.operation', string='Operacion')
    investment_id = fields.Many2one('lenka.investment', string='Inversion / Deposito')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', required=True)
    date_from = fields.Date(string='Desde', required=True)
    date_to = fields.Date(string='Hasta', required=True)
    opening_balance = fields.Monetary(string='Saldo inicial', copy=False)
    closing_balance = fields.Monetary(string='Saldo final', copy=False)
    period_interest = fields.Monetary(string='Intereses del periodo', copy=False)
    period_late_fees = fields.Monetary(string='Mora del periodo', copy=False)
    period_capital = fields.Monetary(string='Capital del periodo', copy=False)
    period_fees = fields.Monetary(string='Comisiones / cargos', copy=False)
    line_ids = fields.One2many('lenka.statement.line', 'statement_id', string='Movimientos', copy=False)
    state = fields.Selection([
        ('draft', 'Borrador'), ('generated', 'Generado'), ('sent', 'Enviado'), ('cancelled', 'Cancelado')
    ], default='draft', tracking=True, copy=False)
    sent_date = fields.Datetime(string='Enviado el', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('lenka.statement') or 'Nuevo'
        return super().create(vals_list)

    @api.onchange('statement_type', 'operation_id', 'investment_id')
    def _onchange_source(self):
        for rec in self:
            if rec.statement_type == 'operation':
                rec.investment_id = False
                source = rec.operation_id
            else:
                rec.operation_id = False
                source = rec.investment_id
            if source:
                rec.partner_id = source.partner_id
                rec.company_id = source.company_id
                rec.currency_id = source.currency_id

    def write(self, vals):
        identity = {'statement_type', 'partner_id', 'operation_id', 'investment_id', 'company_id', 'currency_id', 'date_from', 'date_to'}
        results = {'opening_balance', 'closing_balance', 'period_interest', 'period_late_fees', 'period_capital', 'period_fees', 'line_ids', 'state', 'sent_date'}
        if identity.intersection(vals) and any(rec.state != 'draft' for rec in self):
            raise ValidationError(_('El periodo y origen de un estado de cuenta generado no pueden modificarse. Dupliquelo para preparar un nuevo borrador.'))
        if results.intersection(vals) and any(rec.state in ('sent', 'cancelled') for rec in self):
            raise ValidationError(_('Un estado de cuenta enviado o cancelado no puede modificarse.'))
        return super().write(vals)

    @api.constrains('statement_type', 'operation_id', 'investment_id', 'partner_id', 'company_id', 'currency_id', 'date_from', 'date_to')
    def _check_statement(self):
        for rec in self:
            if rec.date_from > rec.date_to:
                raise ValidationError(_('La fecha inicial no puede ser posterior a la fecha final.'))
            if rec.operation_id and rec.investment_id:
                raise ValidationError(_('Seleccione solo una operacion o una inversion para el estado de cuenta.'))
            if rec.statement_type == 'operation' and not rec.operation_id:
                raise ValidationError(_('Seleccione una operacion financiera.'))
            if rec.statement_type == 'operation' and rec.operation_id and rec.operation_id.partner_id != rec.partner_id:
                raise ValidationError(_('El cliente del estado de cuenta debe coincidir con el cliente de la operacion.'))
            if rec.statement_type == 'operation' and rec.operation_id and rec.operation_id.company_id != rec.company_id:
                raise ValidationError(_('La empresa del estado de cuenta debe coincidir con la empresa de la operacion.'))
            if rec.statement_type == 'investment' and not rec.investment_id:
                raise ValidationError(_('Seleccione una inversion o deposito.'))
            if rec.statement_type == 'investment' and rec.investment_id and rec.investment_id.partner_id != rec.partner_id:
                raise ValidationError(_('El inversionista del estado de cuenta debe coincidir con la inversion seleccionada.'))
            if rec.statement_type == 'investment' and rec.investment_id and rec.investment_id.company_id != rec.company_id:
                raise ValidationError(_('La empresa del estado de cuenta debe coincidir con la empresa de la inversion.'))
            source = rec.operation_id if rec.statement_type == 'operation' else rec.investment_id
            if source and rec.currency_id != source.currency_id:
                raise ValidationError(_('La moneda del estado de cuenta debe coincidir con la de su operacion o inversion.'))

    def action_generate(self):
        self.check_access('write')
        self.mapped('operation_id').check_access('read')
        self.mapped('investment_id').check_access('read')
        self._check_statement()
        if any(rec.state not in ('draft', 'generated') for rec in self):
            raise ValidationError(_('Solo pueden generarse estados de cuenta en borrador o generados.'))
        for rec in self:
            if rec.statement_type == 'operation':
                rec._generate_operation_statement()
            else:
                rec._generate_investment_statement()
            rec.state = 'generated'
        return True

    def _replace_generated_lines(self, commands):
        self.ensure_one()
        self.check_access('write')
        # Solo el detalle calculado; no cambiar los permisos de edicion manual.
        self.line_ids.sudo().unlink()
        self.env['lenka.statement.line'].sudo().create([
            dict(command[2], statement_id=self.id) for command in commands
        ])

    def _generate_operation_statement(self):
        self.ensure_one()
        operation = self.operation_id

        lines = []
        payments_before = operation.payment_ids.filtered(
            lambda p: p.state == 'posted' and p.payment_date < self.date_from
        )
        payments_period = operation.payment_ids.filtered(
            lambda p: p.state == 'posted' and self.date_from <= p.payment_date <= self.date_to
        ).sorted('payment_date')

        transfers = operation.restructuring_out_ids.filtered('original_operation_closed')
        transferred_before = sum(transfers.filtered(lambda r: r.completed_date and r.completed_date < self.date_from).mapped('approved_capital'))
        capital_before = sum(payments_before.mapped('capital_amount')) + transferred_before
        self.opening_balance = max(operation.financed_amount - capital_before, 0.0)

        capital = interest = late = fees = 0.0
        for payment in payments_period:
            capital += payment.capital_amount
            interest += payment.interest_amount
            late += payment.late_fee_amount
            fees += payment.card_fee_amount
            lines.append((0, 0, {
                'date': payment.payment_date,
                'description': _('Pago %s') % payment.name,
                'reference': payment.reference,
                'debit': 0.0,
                'credit': payment.net_bank_amount,
                'capital': payment.capital_amount,
                'interest': payment.interest_amount,
                'late_fee': payment.late_fee_amount,
                'fee': payment.card_fee_amount,
            }))

        for transfer in transfers.filtered(lambda r: r.completed_date and self.date_from <= r.completed_date <= self.date_to):
            capital += transfer.approved_capital
            lines.append((0, 0, {
                'date': transfer.completed_date,
                'description': _('Saldo trasladado por reestructuracion (sin cobro de efectivo)'),
                'reference': transfer.successor_operation_id.name,
                'capital': transfer.approved_capital,
                'credit': transfer.approved_capital,
            }))

        self.period_capital = capital
        self.period_interest = interest
        self.period_late_fees = late
        self.period_fees = fees
        self.closing_balance = max(self.opening_balance - capital, 0.0)
        self._replace_generated_lines(sorted(lines, key=lambda cmd: cmd[2]['date']))

    def _generate_investment_statement(self):
        self.ensure_one()
        investment = self.investment_id

        interest_before = investment.interest_line_ids.filtered(
            lambda l: l.state in ('accrued', 'paid') and l.period_date < self.date_from
        )
        withdrawals_before = investment.withdrawal_ids.filtered(
            lambda w: w.state == 'posted' and w.date < self.date_from
        )
        principal_before = investment.principal_amount if investment.start_date < self.date_from else 0.0
        opening = principal_before + sum(interest_before.mapped('net_amount')) - sum(withdrawals_before.mapped('total_amount'))
        self.opening_balance = max(opening, 0.0)

        lines = []
        deposit = investment.principal_amount if self.date_from <= investment.start_date <= self.date_to else 0.0
        if deposit:
            lines.append((0, 0, {
                'date': investment.start_date,
                'description': _('Deposito inicial de inversion'),
                'reference': investment.contract_reference,
                'credit': deposit,
                'capital': deposit,
            }))
        interest_total = 0.0
        tax_total = 0.0
        withdrawal_total = 0.0
        period_interests = investment.interest_line_ids.filtered(
            lambda l: l.state in ('accrued', 'paid') and self.date_from <= l.period_date <= self.date_to
        ).sorted('period_date')
        period_withdrawals = investment.withdrawal_ids.filtered(
            lambda w: w.state == 'posted' and self.date_from <= w.date <= self.date_to
        ).sorted('date')

        for line in period_interests:
            interest_total += line.amount
            tax_total += line.tax_amount
            lines.append((0, 0, {
                'date': line.period_date,
                'description': _('Interes capitalizado/devengado'),
                'credit': line.amount,
                'interest': line.amount,
            }))
            if line.tax_amount:
                lines.append((0, 0, {
                    'date': line.period_date,
                    'description': _('Retencion sobre intereses'),
                    'debit': line.tax_amount,
                }))
        for withdrawal in period_withdrawals:
            withdrawal_total += withdrawal.total_amount
            lines.append((0, 0, {
                'date': withdrawal.date,
                'description': _('Retiro de inversion'),
                'reference': withdrawal.reference,
                'debit': withdrawal.total_amount,
            }))

        self.period_interest = interest_total
        self.period_capital = 0.0
        self.period_late_fees = 0.0
        self.period_fees = 0.0
        self.closing_balance = max(self.opening_balance + deposit + interest_total - tax_total - withdrawal_total, 0.0)
        self._replace_generated_lines(sorted(lines, key=lambda cmd: cmd[2].get('date') or self.date_from))

    def action_send_email(self):
        self.check_access('write')
        if any(rec.state not in ('draft', 'generated') for rec in self):
            raise ValidationError(_('Solo pueden enviarse estados de cuenta en borrador o generados.'))
        for rec in self:
            if rec.state == 'draft':
                rec.action_generate()
            if not rec.partner_id.email:
                raise ValidationError(_('El cliente no tiene correo electronico.'))

            report = self.env.ref('lenka_financiero.action_report_lenka_statement')
            pdf_content, report_format = report._render_qweb_pdf(report.report_name, res_ids=rec.ids)
            attachment = self.env['ir.attachment'].create({
                'name': '%s.pdf' % rec.name,
                'type': 'binary',
                'datas': __import__('base64').b64encode(pdf_content),
                'mimetype': 'application/pdf',
                'res_model': rec._name,
                'res_id': rec.id,
            })
            subject = _('Estado de cuenta Lenka %s - %s') % (rec.date_from, rec.date_to)
            body = _(
                '<p>Estimado/a %s,</p><p>Adjuntamos su estado de cuenta de Inversiones Lenka '
                'correspondiente al periodo %s al %s.</p>'
            ) % (rec.partner_id.name, rec.date_from, rec.date_to)
            mail = self.env['mail.mail'].create({
                'subject': subject,
                'body_html': body,
                'email_to': rec.partner_id.email,
                'attachment_ids': [(4, attachment.id)],
            })
            mail.send()
            rec.write({'state': 'sent', 'sent_date': fields.Datetime.now()})
        return True

    @api.model
    def _cron_generate_monthly_statements(self):
        today = fields.Date.context_today(self)
        first_this_month = today.replace(day=1)
        last_prev_month = first_this_month - timedelta(days=1)
        first_prev_month = last_prev_month.replace(day=1)
        auto_send = self.env['ir.config_parameter'].sudo().get_param(
            'lenka_financiero.auto_send_statements', 'False'
        ) == 'True'

        active_operations = self.env['lenka.financial.operation'].search([('state', '=', 'active'), ('company_id', 'in', self.env.companies.ids)])
        for operation in active_operations:
            existing = self.search_count([
                ('operation_id', '=', operation.id),
                ('date_from', '=', first_prev_month),
                ('date_to', '=', last_prev_month),
            ])
            if existing:
                continue
            statement = self.create({
                'statement_type': 'operation',
                'partner_id': operation.partner_id.id,
                'operation_id': operation.id,
                'company_id': operation.company_id.id,
                'currency_id': operation.currency_id.id,
                'date_from': first_prev_month,
                'date_to': last_prev_month,
            })
            statement.action_generate()
            if auto_send and statement.partner_id.email:
                statement.action_send_email()

        # Include the final month of closed investments, but never generate
        # a balance for an investment whose deposit has not started yet.
        final_withdrawals = self.env['lenka.investment.withdrawal'].search([
            ('state', '=', 'posted'), ('date', '>=', first_prev_month),
            ('date', '<=', last_prev_month),
            ('investment_id.company_id', 'in', self.env.companies.ids),
            ('investment_id.state', '=', 'closed'),
        ])
        active_investments = self.env['lenka.investment'].search([
            ('company_id', 'in', self.env.companies.ids),
            ('start_date', '<=', last_prev_month),
            '|', ('state', 'in', ('active', 'matured')),
            ('id', 'in', final_withdrawals.mapped('investment_id').ids),
        ])
        for investment in active_investments:
            existing = self.search_count([
                ('investment_id', '=', investment.id),
                ('date_from', '=', first_prev_month),
                ('date_to', '=', last_prev_month),
            ])
            if existing:
                continue
            statement = self.create({
                'statement_type': 'investment',
                'partner_id': investment.partner_id.id,
                'investment_id': investment.id,
                'company_id': investment.company_id.id,
                'currency_id': investment.currency_id.id,
                'date_from': first_prev_month,
                'date_to': last_prev_month,
            })
            statement.action_generate()
            if auto_send and statement.partner_id.email:
                statement.action_send_email()


class LenkaStatementLine(models.Model):
    _name = 'lenka.statement.line'
    _description = 'Movimiento Estado de Cuenta Lenka'
    _order = 'date, id'

    statement_id = fields.Many2one('lenka.statement', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='statement_id.currency_id')
    date = fields.Date(required=True)
    description = fields.Char(required=True)
    reference = fields.Char()
    debit = fields.Monetary(string='Debito / salida')
    credit = fields.Monetary(string='Credito / entrada')
    capital = fields.Monetary()
    interest = fields.Monetary(string='Interes')
    late_fee = fields.Monetary(string='Mora')
    fee = fields.Monetary(string='Comision / cargo')
