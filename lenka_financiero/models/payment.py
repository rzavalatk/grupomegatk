from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


_PAYMENT_RESULT_FIELDS = {
    'late_fee_amount', 'interest_amount', 'capital_amount',
    'extra_capital_amount', 'unapplied_amount', 'allocation_line_ids',
}


class LenkaPayment(models.Model):
    _name = 'lenka.payment'
    _description = 'Cobro Lenka'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payment_date desc, id desc'

    name = fields.Char(default='Nuevo', readonly=True, copy=False)
    operation_id = fields.Many2one('lenka.financial.operation', string='Operacion', required=True, tracking=True)
    partner_id = fields.Many2one(related='operation_id.partner_id', store=True, string='Cliente')
    currency_id = fields.Many2one(related='operation_id.currency_id', store=True)
    payment_date = fields.Date(string='Fecha de pago', required=True, default=fields.Date.context_today)
    amount = fields.Monetary(string='Monto procesado / entregado por cliente', required=True, tracking=True)
    payment_method = fields.Selection([
        ('cash', 'Efectivo'), ('transfer', 'Transferencia'), ('check', 'Cheque'),
        ('card', 'Tarjeta'), ('other', 'Otro')
    ], string='Forma de pago', required=True, default='transfer')
    reference = fields.Char(string='Referencia')
    state = fields.Selection([('draft', 'Borrador'), ('posted', 'Aplicado'), ('cancelled', 'Anulado')], default='draft', tracking=True, copy=False)

    card_fee_rate = fields.Float(string='Comision tarjeta (%)', default=lambda self: self._default_card_fee_rate())
    card_fee_amount = fields.Monetary(string='Cargo bancario / tarjeta', compute='_compute_card_net', store=True)
    net_bank_amount = fields.Monetary(string='Monto neto aplicable a la deuda', compute='_compute_card_net', store=True)

    late_fee_amount = fields.Monetary(string='Aplicado a mora', readonly=True, copy=False)
    interest_amount = fields.Monetary(string='Aplicado a interes', readonly=True, copy=False)
    capital_amount = fields.Monetary(string='Aplicado a capital', readonly=True, copy=False)
    extra_capital_amount = fields.Monetary(string='Abono extraordinario a capital', readonly=True, copy=False)
    unapplied_amount = fields.Monetary(string='Saldo sin aplicar', readonly=True, copy=False)
    allocation_line_ids = fields.One2many('lenka.payment.allocation', 'payment_id', string='Aplicacion', copy=False, readonly=True)
    notes = fields.Text(string='Observaciones')

    def _default_card_fee_rate(self):
        value = self.env['ir.config_parameter'].sudo().get_param('lenka_financiero.card_fee_rate', '3.5')
        try:
            return float(value)
        except (TypeError, ValueError):
            return 3.5

    @api.depends('amount', 'payment_method', 'card_fee_rate')
    def _compute_card_net(self):
        for rec in self:
            if rec.payment_method == 'card':
                rate = max(rec.card_fee_rate, 0.0) / 100.0
                rec.card_fee_amount = rec.amount * rate
                rec.net_bank_amount = rec.amount - rec.card_fee_amount
            else:
                rec.card_fee_amount = 0.0
                rec.net_bank_amount = rec.amount

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('state', 'draft') != 'draft' or any(vals.get(key) for key in _PAYMENT_RESULT_FIELDS):
                raise ValidationError(_('Cree el cobro en borrador y utilice Aplicar pago para calcular su distribucion.'))
            vals['state'] = 'draft'
            for key in _PAYMENT_RESULT_FIELDS:
                vals[key] = [] if key == 'allocation_line_ids' else 0.0
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('lenka.payment') or 'Nuevo'
        return super().create(vals_list)

    def write(self, vals):
        if _PAYMENT_RESULT_FIELDS.intersection(vals):
            raise ValidationError(_('La distribucion del cobro se calcula al aplicar el pago y no puede editarse manualmente.'))
        if 'state' in vals and any(rec.state != vals['state'] for rec in self):
            raise ValidationError(_('Utilice Aplicar pago o Anular para cambiar el estado del cobro.'))
        financial_fields = {'operation_id', 'payment_date', 'amount', 'payment_method', 'card_fee_rate'}
        if financial_fields.intersection(vals) and any(rec.state != 'draft' for rec in self):
            raise ValidationError(_('Los datos financieros de un cobro aplicado o anulado no pueden modificarse. Anule el cobro mediante su accion y registre uno nuevo.'))
        return super().write(vals)

    def unlink(self):
        if any(rec.state != 'draft' or rec.move_id for rec in self):
            raise ValidationError(_('Solo se pueden eliminar cobros en borrador sin partida contable. Conserve los demas cobros para auditoria.'))
        return super().unlink()

    @api.constrains('amount', 'card_fee_rate')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('El monto recibido debe ser mayor que cero.'))
            if rec.card_fee_rate < 0 or rec.card_fee_rate > 100:
                raise ValidationError(_('La comision de tarjeta debe estar entre 0% y 100%.'))

    def action_post(self):
        self.check_access('write')
        self.mapped('operation_id').check_access('read')
        for rec in self:
            if rec.state != 'draft':
                continue
            if rec.operation_id.state != 'active':
                raise ValidationError(_('Solo se pueden aplicar cobros a operaciones activas.'))
            if not rec.operation_id.schedule_line_ids:
                raise ValidationError(_('La operacion no tiene tabla de amortizacion.'))
            if rec.allocation_line_ids:
                raise ValidationError(_('El cobro en borrador ya tiene una distribucion. Revise su historial antes de aplicarlo.'))

            # IMPORTANTE: si el pago es con tarjeta, solo el neto recibido despues
            # de la comision bancaria se aplica a la deuda del cliente.
            remaining = rec.net_bank_amount
            allocations = []
            late_total = interest_total = capital_total = 0.0

            due_lines = rec.operation_id.schedule_line_ids.filtered(
                lambda l: l.date and l.date <= rec.payment_date
            ).sorted(key=lambda l: (l.date, l.sequence))

            # 1) Mora vencida.
            for line in due_lines:
                if remaining <= 0:
                    break
                due_late = max(line.late_fee_due - line.late_fee_paid, 0.0)
                if due_late <= 0:
                    continue
                pay_late = min(remaining, due_late)
                remaining -= pay_late
                # La cuota es de solo lectura para el operador. Actualizar solo
                # los importes calculados tras comprobar el acceso al cobro.
                line.sudo().write({'late_fee_paid': line.late_fee_paid + pay_late})
                late_total += pay_late
                allocations.append((0, 0, {
                    'schedule_line_id': line.id,
                    'late_fee_amount': pay_late,
                }))

            # 2) Intereses exigibles a la fecha. Nunca se pagan intereses futuros.
            for line in due_lines:
                if remaining <= 0:
                    break
                due_interest = max(line.interest - line.interest_paid, 0.0)
                if due_interest <= 0:
                    continue
                pay_interest = min(remaining, due_interest)
                remaining -= pay_interest
                line.sudo().write({'interest_paid': line.interest_paid + pay_interest})
                interest_total += pay_interest
                allocations.append((0, 0, {
                    'schedule_line_id': line.id,
                    'interest_amount': pay_interest,
                }))

            # 3) Capital exigible de cuotas vencidas/a la fecha.
            # Los abonos extraordinarios anteriores reducen el saldo global,
            # aunque no se distribuyan entre las cuotas de la tabla original.
            # Nunca aplicar nuevamente ese capital al vencer dichas cuotas.
            capital_available = rec.operation_id.outstanding_capital
            for line in due_lines:
                if remaining <= 0 or capital_available <= 0:
                    break
                due_capital = max(line.capital - line.capital_paid, 0.0)
                if due_capital <= 0:
                    continue
                pay_capital = min(remaining, due_capital, capital_available)
                remaining -= pay_capital
                capital_available -= pay_capital
                line.sudo().write({'capital_paid': line.capital_paid + pay_capital})
                capital_total += pay_capital
                allocations.append((0, 0, {
                    'schedule_line_id': line.id,
                    'capital_amount': pay_capital,
                }))

            # 4) Si paga mas, todo excedente se aplica directamente a capital.
            # No se anticipan intereses de cuotas futuras.
            extra_capital = min(remaining, capital_available)
            remaining -= extra_capital
            if extra_capital:
                capital_total += extra_capital

            # Detalle generado por el sistema; no otorgar creacion/edicion
            # manual de distribuciones a los usuarios operativos.
            self.env['lenka.payment.allocation'].sudo().create([
                dict(command[2], payment_id=rec.id) for command in allocations
            ])

            # Transicion interna: conservar ORM, permisos y seguimiento sin
            # permitir que write/importaciones omitan la aplicacion del pago.
            super(LenkaPayment, rec).write({
                'late_fee_amount': late_total,
                'interest_amount': interest_total,
                'capital_amount': capital_total,
                'extra_capital_amount': extra_capital,
                'unapplied_amount': remaining,
                'state': 'posted',
            })
        return True

    def action_cancel(self):
        self.check_access('write')
        self.mapped('operation_id').check_access('read')
        # Validar todo el lote antes de modificar cuotas o partidas.
        for rec in self:
            if rec.state == 'cancelled':
                continue
            if rec.state == 'posted' and rec.operation_id.state != 'active':
                raise ValidationError(_('No se puede anular un cobro de una operacion cerrada o inactiva. Revise primero el cierre de la operacion y sus garantias.'))
            if rec.move_id and rec.move_id.state == 'posted':
                raise ValidationError(_('No se puede anular el cobro mientras su partida este publicada. Regularice su anulacion en Contabilidad antes de continuar.'))
            for alloc in rec.allocation_line_ids:
                alloc.schedule_line_id.check_access('read')
                if alloc.schedule_line_id.operation_id != rec.operation_id:
                    raise ValidationError(_('La distribucion del cobro contiene una cuota de otra operacion.'))
        for rec in self:
            if rec.state == 'cancelled':
                continue
            if rec.move_id.state == 'draft':
                rec.move_id.button_cancel()
            if rec.state != 'posted':
                super(LenkaPayment, rec).write({'state': 'cancelled'})
                continue
            for alloc in rec.allocation_line_ids:
                line = alloc.schedule_line_id
                line.sudo().write({
                    'late_fee_paid': max(line.late_fee_paid - alloc.late_fee_amount, 0.0),
                    'interest_paid': max(line.interest_paid - alloc.interest_amount, 0.0),
                    'capital_paid': max(line.capital_paid - alloc.capital_amount, 0.0),
                })
            super(LenkaPayment, rec).write({'state': 'cancelled'})
        return True


class LenkaPaymentAllocation(models.Model):
    _name = 'lenka.payment.allocation'
    _description = 'Aplicacion de Cobro Lenka'

    payment_id = fields.Many2one('lenka.payment', required=True, ondelete='cascade')
    schedule_line_id = fields.Many2one('lenka.amortization.line', required=True, ondelete='restrict')
    currency_id = fields.Many2one(related='payment_id.currency_id')
    late_fee_amount = fields.Monetary(string='Mora')
    interest_amount = fields.Monetary(string='Interes')
    capital_amount = fields.Monetary(string='Capital')


class LenkaFinancialOperationPaymentMixin(models.Model):
    _inherit = 'lenka.financial.operation'

    payment_ids = fields.One2many('lenka.payment', 'operation_id', string='Cobros')
    late_fee_rate = fields.Float(string='Mora mensual (%)', default=0.0)
    grace_days = fields.Integer(string='Dias de gracia', default=0)
    paid_capital = fields.Monetary(string='Capital pagado', compute='_compute_collection_totals')
    paid_interest = fields.Monetary(string='Interes pagado', compute='_compute_collection_totals')
    paid_late_fees = fields.Monetary(string='Mora pagada', compute='_compute_collection_totals')
    paid_card_fees = fields.Monetary(string='Comisiones de tarjeta', compute='_compute_collection_totals')
    net_collections = fields.Monetary(string='Neto recibido', compute='_compute_collection_totals')
    outstanding_capital = fields.Monetary(string='Capital pendiente', compute='_compute_collection_totals')

    @api.depends(
        'financed_amount',
        'schedule_line_ids.capital_paid', 'schedule_line_ids.interest_paid', 'schedule_line_ids.late_fee_paid',
        'payment_ids.state', 'payment_ids.extra_capital_amount', 'payment_ids.card_fee_amount', 'payment_ids.net_bank_amount'
    )
    def _compute_collection_totals(self):
        for rec in self:
            posted = rec.payment_ids.filtered(lambda p: p.state == 'posted')
            scheduled_capital = sum(rec.schedule_line_ids.mapped('capital_paid'))
            extra_capital = sum(posted.mapped('extra_capital_amount'))
            rec.paid_capital = scheduled_capital + extra_capital
            rec.paid_interest = sum(rec.schedule_line_ids.mapped('interest_paid'))
            rec.paid_late_fees = sum(rec.schedule_line_ids.mapped('late_fee_paid'))
            rec.paid_card_fees = sum(posted.mapped('card_fee_amount'))
            rec.net_collections = sum(posted.mapped('net_bank_amount'))
            rec.outstanding_capital = max(rec.financed_amount - rec.paid_capital, 0.0)

    def action_update_late_fees(self):
        today = fields.Date.context_today(self)
        for rec in self:
            monthly_rate = rec.late_fee_rate / 100.0
            for line in rec.schedule_line_ids:
                due_date = fields.Date.add(line.date, days=rec.grace_days)
                if today <= due_date or line.payment_state == 'paid':
                    continue
                overdue_capital = max(line.capital - line.capital_paid, 0.0)
                line.late_fee_due = overdue_capital * monthly_rate
        return True

    def get_payoff_amount(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        pending_interest = sum(
            max(l.interest - l.interest_paid, 0.0)
            for l in self.schedule_line_ids if l.date and l.date <= today
        )
        pending_late = sum(max(l.late_fee_due - l.late_fee_paid, 0.0) for l in self.schedule_line_ids)
        return self.outstanding_capital + pending_interest + pending_late

    def action_close_paid_operation(self):
        for rec in self:
            if rec.state != 'active':
                raise ValidationError(_('Solo una operacion activa puede cerrarse por pago total.'))
            payoff = rec.get_payoff_amount()
            if payoff > 0.01:
                raise ValidationError(_('La operacion aun tiene saldo pendiente de %.2f %s.') % (payoff, rec.currency_id.name))
            unapplied = sum(rec.payment_ids.filtered(lambda p: p.state == 'posted').mapped('unapplied_amount'))
            if unapplied > 0.01:
                raise ValidationError(_('Existen cobros con saldo sin aplicar. Regularice esos valores antes de cerrar la operacion.'))
            rec.state = 'done'
            rec.guarantee_ids.filtered(lambda g: g.state in ('accepted', 'active')).write({'state': 'release_pending'})
        return True


class LenkaAmortizationPaymentMixin(models.Model):
    _inherit = 'lenka.amortization.line'

    capital_paid = fields.Monetary(string='Capital pagado', default=0.0)
    interest_paid = fields.Monetary(string='Interes pagado', default=0.0)
    late_fee_due = fields.Monetary(string='Mora generada', default=0.0)
    late_fee_paid = fields.Monetary(string='Mora pagada', default=0.0)
    amount_paid = fields.Monetary(string='Total pagado', compute='_compute_payment_status')
    amount_due = fields.Monetary(string='Pendiente', compute='_compute_payment_status')
    payment_state = fields.Selection([
        ('pending', 'Pendiente'), ('partial', 'Parcial'), ('paid', 'Pagada'), ('overdue', 'Vencida')
    ], string='Estado de cuota', compute='_compute_payment_status')

    @api.depends('capital', 'interest', 'late_fee_due', 'capital_paid', 'interest_paid', 'late_fee_paid', 'date')
    def _compute_payment_status(self):
        today = fields.Date.context_today(self)
        for line in self:
            total_due = line.capital + line.interest + line.late_fee_due
            paid = line.capital_paid + line.interest_paid + line.late_fee_paid
            pending = max(total_due - paid, 0.0)
            line.amount_paid = paid
            line.amount_due = pending
            if pending <= 0.01:
                line.payment_state = 'paid'
            elif paid > 0:
                line.payment_state = 'partial'
            elif line.date and line.date < today:
                line.payment_state = 'overdue'
            else:
                line.payment_state = 'pending'
