from decimal import Decimal, ROUND_HALF_UP

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LenkaFinancialOperation(models.Model):
    _name = 'lenka.financial.operation'
    _description = 'Operacion Financiera Lenka'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(default='Nuevo', readonly=True, copy=False, tracking=True)
    is_quote = fields.Boolean(string='Es cotizacion', default=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True)
    guarantor_ids = fields.Many2many('res.partner', 'lenka_operation_guarantor_rel', 'operation_id', 'partner_id', string='Avales')
    operation_type = fields.Selection([
        ('loan', 'Prestamo'), ('financing', 'Financiamiento'), ('lease', 'Arrendamiento')
    ], string='Tipo de operacion', required=True, default='financing', tracking=True)
    product_id = fields.Many2one('product.product', string='Equipo / Producto')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', required=True, default=lambda self: self.env.company.currency_id)
    date = fields.Date(required=True, default=fields.Date.context_today)
    principal_amount = fields.Monetary(string='Monto / Valor', required=True, tracking=True)
    down_payment = fields.Monetary(string='Prima', default=0.0)
    financed_amount = fields.Monetary(string='Monto financiado', compute='_compute_financed_amount', store=True)
    interest_rate = fields.Float(string='Tasa de interes (%)', required=True, tracking=True)
    rate_period = fields.Selection([('monthly', 'Mensual'), ('annual', 'Anual')], default='monthly', required=True)
    term_months = fields.Integer(string='Plazo (meses)', required=True, default=12)
    first_payment_date = fields.Date(string='Primera cuota')
    calculation_method = fields.Selection([
        ('level', 'Cuota nivelada'),
        ('balance', 'Interes sobre saldo / capital fijo'),
        ('interest_only', 'Solo intereses + capital al final'),
        ('balloon', 'Cuota bomba / extraordinarios'),
        ('custom', 'Plan personalizado'),
    ], string='Metodo de calculo', required=True, default='level')
    balloon_base_payment = fields.Monetary(string='Cuota regular antes de bombas')
    extra_payment_line_ids = fields.One2many('lenka.extra.payment.plan', 'operation_id', string='Pagos extraordinarios')
    residual_purchase_percent = fields.Float(string='Opcion de compra (%)', default=0.0)
    residual_purchase_amount = fields.Monetary(string='Opcion de compra', compute='_compute_residual_purchase_amount', store=True)
    recalculation_policy = fields.Selection([
        ('reduce_term', 'Reducir plazo'),
        ('reduce_payment', 'Reducir cuota'),
        ('keep_plan', 'Mantener plan contractual'),
    ], string='Regla para abonos extraordinarios reales', default='reduce_term', required=True)
    state = fields.Selection([
        ('draft', 'Borrador'), ('review', 'En revision'), ('approved', 'Aprobada'),
        ('contracted', 'Contratada'), ('active', 'Activa'), ('done', 'Finalizada'),
        ('rejected', 'Rechazada'), ('cancelled', 'Cancelada')
    ], default='draft', tracking=True)
    schedule_line_ids = fields.One2many('lenka.amortization.line', 'operation_id', string='Tabla de amortizacion', copy=False)
    funding_line_ids = fields.One2many('lenka.funding.line', 'operation_id', string='Fondeo')
    guarantee_ids = fields.One2many('lenka.guarantee', 'operation_id', string='Garantias')
    notes = fields.Text(string='Observaciones')

    @api.depends('principal_amount', 'down_payment')
    def _compute_financed_amount(self):
        for rec in self:
            principal = Decimal(str(rec.principal_amount or 0.0))
            down_payment = Decimal(str(rec.down_payment or 0.0))
            amount = max(principal - down_payment, Decimal('0'))
            if rec.currency_id:
                quantum = Decimal(str(rec.currency_id.rounding or 0.01))
                amount = amount.quantize(quantum, rounding=ROUND_HALF_UP)
            rec.financed_amount = float(amount)

    @api.depends('principal_amount', 'residual_purchase_percent')
    def _compute_residual_purchase_amount(self):
        for rec in self:
            rec.residual_purchase_amount = rec.principal_amount * rec.residual_purchase_percent / 100.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('lenka.financial.operation') or 'Nuevo'
        return super().create(vals_list)

    @api.constrains('principal_amount', 'down_payment', 'interest_rate', 'term_months', 'residual_purchase_percent', 'partner_id', 'guarantor_ids', 'balloon_base_payment')
    def _check_financial_values(self):
        for rec in self:
            if rec.principal_amount <= 0:
                raise ValidationError(_('El monto debe ser mayor que cero.'))
            if rec.down_payment < 0 or rec.down_payment > rec.principal_amount:
                raise ValidationError(_('La prima debe estar entre cero y el valor de la operacion.'))
            if rec.interest_rate < 0:
                raise ValidationError(_('La tasa no puede ser negativa.'))
            if rec.term_months <= 0:
                raise ValidationError(_('El plazo debe ser mayor que cero.'))
            if not 0 <= rec.residual_purchase_percent <= 100:
                raise ValidationError(_('La opcion de compra debe estar entre 0% y 100%.'))
            if rec.partner_id and rec.partner_id in rec.guarantor_ids:
                raise ValidationError(_('El cliente no puede ser su propio aval.'))
            if rec.balloon_base_payment < 0:
                raise ValidationError(_('La cuota regular no puede ser negativa.'))

    def write(self, vals):
        protected = {
            'partner_id', 'operation_type', 'product_id', 'company_id', 'currency_id',
            'principal_amount', 'down_payment', 'interest_rate', 'rate_period',
            'term_months', 'first_payment_date', 'calculation_method',
            'balloon_base_payment', 'residual_purchase_percent', 'recalculation_policy',
        }
        if protected.intersection(vals):
            locked = self.filtered(lambda r: r.state in ('approved', 'contracted', 'active', 'done'))
            if locked:
                raise ValidationError(_('Las condiciones financieras no pueden modificarse despues de aprobar la operacion. Use una reestructuracion para conservar el historial.'))
        return super().write(vals)

    @api.constrains('funding_line_ids')
    def _check_funding_total(self):
        for rec in self.filtered(lambda r: r.funding_line_ids):
            if any(line.amount <= 0 for line in rec.funding_line_ids):
                raise ValidationError(_('Cada fuente de fondeo debe tener un monto mayor que cero.'))
            total = sum(rec.funding_line_ids.mapped('amount'))
            if total > rec.financed_amount + 0.01:
                raise ValidationError(_('El fondeo total no puede exceder el monto financiado.'))

    def _monthly_rate(self):
        self.ensure_one()
        return self.interest_rate / 100.0 if self.rate_period == 'monthly' else self.interest_rate / 1200.0

    def _level_payment(self, principal, monthly_rate, periods):
        self.ensure_one()
        if not monthly_rate:
            return principal / periods
        return principal * monthly_rate / (1 - (1 + monthly_rate) ** -periods)

    def action_generate_schedule(self):
        self.check_access('write')
        # Validar el lote antes de reemplazar tablas existentes.
        for rec in self:
            if rec.state in ('active', 'done') or rec.disbursement_ids.filtered(lambda d: d.state == 'posted'):
                raise ValidationError(_('No se puede reemplazar la tabla de amortizacion despues de un desembolso. Use una reestructuracion para conservar el historial contractual.'))
            if rec.calculation_method != 'custom' and rec.financed_amount <= 0:
                raise ValidationError(_('El monto financiado debe ser mayor que cero para generar el plan.'))
            if rec.calculation_method == 'balloon' and any(line.installment_number > rec.term_months for line in rec.extra_payment_line_ids):
                raise ValidationError(_('Hay pagos extraordinarios asignados a cuotas fuera del plazo.'))
        for rec in self:
            if rec.calculation_method == 'custom':
                continue
            principal = rec.financed_amount
            n = rec.term_months
            monthly_rate = rec._monthly_rate()
            balance = principal
            payment_date = rec.first_payment_date or fields.Date.add(rec.date, months=1)
            first_payment_date = payment_date
            lines = []
            level_payment = rec._level_payment(principal, monthly_rate, n) if rec.calculation_method in ('level', 'balloon') else 0.0
            fixed_capital = principal / n if rec.calculation_method == 'balance' else 0.0
            extras = {}
            for line in rec.extra_payment_line_ids:
                extras[line.installment_number] = extras.get(line.installment_number, 0.0) + line.amount
            rounding = rec.currency_id.round if rec.currency_id else (lambda value: value)

            for number in range(1, n + 1):
                balance = rounding(balance)
                if balance <= 0:
                    break
                interest = rounding(balance * monthly_rate)
                extra = rounding(extras.get(number, 0.0)) if rec.calculation_method == 'balloon' else 0.0

                if rec.calculation_method == 'level':
                    capital = rounding(min(max(level_payment - interest, 0.0), balance))
                    if number == n:
                        capital = balance
                elif rec.calculation_method == 'balance':
                    capital = balance if number == n else rounding(min(fixed_capital, balance))
                elif rec.calculation_method == 'interest_only':
                    capital = balance if number == n else 0.0
                elif rec.calculation_method == 'balloon':
                    regular_payment = rec.balloon_base_payment or level_payment
                    regular_capital = rounding(max(regular_payment - interest, 0.0))
                    capital = rounding(min(regular_capital + extra, balance))
                    if number == n:
                        capital = balance
                    extra = rounding(min(extra, capital))
                else:
                    capital = 0.0

                capital = rounding(capital)
                end_balance = rounding(max(balance - capital, 0.0))
                if number == n and end_balance:
                    capital = rounding(capital + end_balance)
                    end_balance = 0.0
                total = rounding(capital + interest)
                lines.append((0, 0, {
                    'sequence': number,
                    'date': payment_date,
                    'opening_balance': balance,
                    'capital': capital,
                    'interest': interest,
                    'extra_charge': extra,
                    'payment': total,
                    'closing_balance': end_balance,
                }))
                balance = end_balance
                payment_date = fields.Date.add(first_payment_date, months=number)

            # Escritura limitada al detalle calculado de una operacion autorizada.
            # El usuario conserva solo lectura sobre las cuotas individuales.
            rec.schedule_line_ids.sudo().unlink()
            self.env['lenka.amortization.line'].sudo().create([
                dict(command[2], operation_id=rec.id) for command in lines
            ])
        return True

    def action_convert_to_application(self):
        self.check_access('write')
        for rec in self:
            if not rec.is_quote:
                continue
            if rec.state not in ('draft', 'review'):
                raise ValidationError(_('Solo una cotizacion en borrador o revision puede convertirse en solicitud.'))
            if not rec.schedule_line_ids and rec.calculation_method != 'custom':
                rec.action_generate_schedule()
            rec.write({'is_quote': False, 'state': 'review'})
        return True


class LenkaExtraPaymentPlan(models.Model):
    _name = 'lenka.extra.payment.plan'
    _description = 'Pago Extraordinario Planificado Lenka'
    _order = 'installment_number'

    operation_id = fields.Many2one('lenka.financial.operation', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='operation_id.currency_id')
    installment_number = fields.Integer(string='Cuota #', required=True)
    amount = fields.Monetary(string='Pago extraordinario', required=True)
    note = fields.Char(string='Descripcion')

    @api.constrains('installment_number', 'amount')
    def _check_values(self):
        for rec in self:
            if rec.installment_number <= 0:
                raise ValidationError(_('El numero de cuota debe ser mayor que cero.'))
            if rec.amount <= 0:
                raise ValidationError(_('El pago extraordinario debe ser mayor que cero.'))


class LenkaAmortizationLine(models.Model):
    _name = 'lenka.amortization.line'
    _description = 'Linea de Amortizacion Lenka'
    _order = 'sequence'

    operation_id = fields.Many2one('lenka.financial.operation', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='operation_id.currency_id')
    sequence = fields.Integer(string='#', required=True)
    date = fields.Date(string='Fecha', required=True)
    opening_balance = fields.Monetary(string='Saldo inicial')
    capital = fields.Monetary(string='Capital')
    interest = fields.Monetary(string='Interes')
    extra_charge = fields.Monetary(string='Pago extraordinario')
    payment = fields.Monetary(string='Cuota total')
    closing_balance = fields.Monetary(string='Saldo final')


class LenkaFundingLine(models.Model):
    _name = 'lenka.funding.line'
    _description = 'Fuente de Fondeo Lenka'

    operation_id = fields.Many2one('lenka.financial.operation', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='operation_id.currency_id')
    source_type = fields.Selection([
        ('own', 'Capital propio'), ('cash', 'Efectivo'), ('bank', 'Cuenta bancaria'),
        ('bank_loan', 'Prestamo bancario'), ('credit_card', 'Tarjeta de credito empresarial'),
        ('investor', 'Inversionista / depositante'), ('third_party', 'Fondos de terceros'), ('other', 'Otro')
    ], string='Fuente', required=True)
    partner_id = fields.Many2one('res.partner', string='Banco / Inversionista / Tercero')
    reference = fields.Char(string='Cuenta / Instrumento / Referencia')
    amount = fields.Monetary(string='Monto', required=True)
    cost_rate = fields.Float(string='Costo financiero (%)')
    cost_period = fields.Selection([('monthly', 'Mensual'), ('annual', 'Anual')], default='annual')

    @api.constrains('amount', 'cost_rate', 'source_type', 'partner_id', 'operation_id')
    def _check_values(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('El monto de fondeo debe ser mayor que cero.'))
            if rec.cost_rate < 0:
                raise ValidationError(_('El costo financiero no puede ser negativo.'))
            if rec.source_type in ('bank_loan', 'credit_card', 'investor', 'third_party') and not rec.partner_id:
                raise ValidationError(_('Seleccione el banco, inversionista o tercero que proporciona esta fuente de fondeo.'))
            if sum(rec.operation_id.funding_line_ids.mapped('amount')) > rec.operation_id.financed_amount + 0.01:
                raise ValidationError(_('El fondeo total no puede exceder el monto financiado.'))


class LenkaGuarantee(models.Model):
    _name = 'lenka.guarantee'
    _description = 'Garantia Lenka'

    operation_id = fields.Many2one('lenka.financial.operation', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='operation_id.currency_id')
    guarantee_type = fields.Selection([
        ('equipment', 'Equipo financiado'), ('vehicle', 'Vehiculo'), ('property', 'Inmueble'),
        ('labor', 'Derechos laborales'), ('deposit', 'Deposito'), ('other', 'Otra')
    ], string='Tipo', required=True)
    owner_id = fields.Many2one('res.partner', string='Propietario')
    description = fields.Char(string='Descripcion', required=True)
    declared_value = fields.Monetary(string='Valor declarado')
    appraisal_value = fields.Monetary(string='Valor de avaluo')
    serial_reference = fields.Char(string='Serie / VIN / Matricula')
    state = fields.Selection([
        ('proposed', 'Propuesta'), ('accepted', 'Aceptada'), ('active', 'Vigente'),
        ('release_pending', 'Pendiente de liberar'), ('released', 'Liberada'), ('executed', 'Ejecutada')
    ], default='proposed')

    def action_release(self):
        for rec in self:
            if rec.operation_id.state != 'done':
                raise ValidationError(_('La garantia solo puede liberarse cuando la operacion esta finalizada.'))
            if rec.state not in ('release_pending', 'active', 'accepted'):
                raise ValidationError(_('La garantia no esta disponible para liberacion.'))
            rec.state = 'released'
        return True
