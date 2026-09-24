from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class LenkaRestructuring(models.Model):
    _name = 'lenka.restructuring'
    _description = 'Reestructuracion Financiera Lenka'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(default='Nuevo', readonly=True, copy=False, tracking=True)
    operation_id = fields.Many2one(
        'lenka.financial.operation', string='Operacion original',
        required=True, ondelete='restrict', tracking=True,
    )
    company_id = fields.Many2one(related='operation_id.company_id', store=True)
    currency_id = fields.Many2one(related='operation_id.currency_id', store=True)
    partner_id = fields.Many2one(related='operation_id.partner_id', store=True)
    request_date = fields.Date(default=fields.Date.context_today, required=True)
    reason = fields.Text(string='Motivo', required=True, tracking=True)

    original_outstanding_capital = fields.Monetary(
        string='Capital pendiente original', readonly=True, copy=False,
    )
    original_payoff_amount = fields.Monetary(
        string='Liquidacion original a la fecha', readonly=True, copy=False,
    )
    original_interest_rate = fields.Float(string='Tasa original (%)', readonly=True, copy=False)
    original_rate_period = fields.Selection(
        [('monthly', 'Mensual'), ('annual', 'Anual')],
        string='Periodo tasa original', readonly=True, copy=False,
    )
    original_term_months = fields.Integer(string='Plazo original', readonly=True, copy=False)

    settlement_method = fields.Selection([
        ('capitalize', 'Sumar intereses y mora al nuevo capital'),
        ('pay_separately', 'Cobrar intereses y mora antes de reestructurar el capital'),
    ], string='Modalidad negociada', tracking=True)
    pending_capital = fields.Monetary(string='Capital pendiente actual', compute='_compute_settlement_preview')
    pending_interest = fields.Monetary(string='Intereses exigibles pendientes', compute='_compute_settlement_preview')
    pending_late_fees = fields.Monetary(string='Mora pendiente', compute='_compute_settlement_preview')
    suggested_principal = fields.Monetary(string='Capital segun modalidad', compute='_compute_settlement_preview')
    approved_capital = fields.Monetary(string='Capital aprobado para traslado', readonly=True, copy=False, tracking=True)
    approved_interest = fields.Monetary(string='Intereses pendientes al aprobar', readonly=True, copy=False, tracking=True)
    approved_late_fees = fields.Monetary(string='Mora pendiente al aprobar', readonly=True, copy=False, tracking=True)
    approved_by = fields.Many2one('res.users', string='Aprobado por', readonly=True, copy=False, tracking=True)
    approved_at = fields.Datetime(string='Fecha de aprobacion', readonly=True, copy=False, tracking=True)

    proposed_principal_amount = fields.Monetary(string='Nuevo capital', required=True, tracking=True)
    proposed_interest_rate = fields.Float(string='Nueva tasa (%)', required=True, tracking=True)
    proposed_rate_period = fields.Selection(
        [('monthly', 'Mensual'), ('annual', 'Anual')],
        string='Periodo nueva tasa', required=True, default='monthly',
    )
    proposed_term_months = fields.Integer(string='Nuevo plazo (meses)', required=True, tracking=True)
    proposed_calculation_method = fields.Selection([
        ('level', 'Cuota nivelada'),
        ('balance', 'Interes sobre saldo / capital fijo'),
        ('interest_only', 'Solo intereses + capital al final'),
        ('balloon', 'Cuota bomba / extraordinarios'),
        ('custom', 'Plan personalizado'),
    ], string='Nuevo metodo', required=True, default='level')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('review', 'En revision'),
        ('approved', 'Aprobada'),
        ('prepared', 'Nueva operacion preparada'),
        ('cancelled', 'Cancelada'),
    ], default='draft', tracking=True, copy=False)

    successor_operation_id = fields.Many2one(
        'lenka.financial.operation', string='Nueva operacion',
        readonly=True, copy=False, ondelete='restrict', tracking=True,
    )
    completed_date = fields.Date(string='Fecha de traslado de saldo', readonly=True, copy=False, tracking=True)
    original_operation_closed = fields.Boolean(string='Operacion original cerrada', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = self.browse()
        for vals in vals_list:
            if vals.get('state', 'draft') != 'draft' or vals.get('successor_operation_id') or vals.get('original_operation_closed'):
                raise ValidationError(_('Cree la solicitud en borrador y utilice las acciones de reestructuracion.'))
            for key in ('approved_capital', 'approved_interest', 'approved_late_fees', 'approved_by', 'approved_at'):
                vals[key] = False
            vals['state'] = 'draft'
            vals['successor_operation_id'] = False
            vals['original_operation_closed'] = False
            vals['completed_date'] = False
            operation = self.env['lenka.financial.operation'].browse(vals.get('operation_id')).exists()
            if not operation:
                raise ValidationError(_('Seleccione una operacion valida.'))
            if operation.state != 'active':
                raise ValidationError(_('Solo se puede reestructurar una operacion activa.'))
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('lenka.restructuring') or 'Nuevo'
            vals['original_outstanding_capital'] = operation.outstanding_capital
            vals['original_payoff_amount'] = operation.get_payoff_amount()
            vals['original_interest_rate'] = operation.interest_rate
            vals['original_rate_period'] = operation.rate_period
            vals['original_term_months'] = operation.term_months
            default_principal = operation.get_payoff_amount() if vals.get('settlement_method') == 'capitalize' else operation.outstanding_capital
            vals.setdefault('proposed_principal_amount', default_principal)
            vals.setdefault('proposed_interest_rate', operation.interest_rate)
            vals.setdefault('proposed_rate_period', operation.rate_period)
            vals.setdefault('proposed_term_months', operation.term_months)
            vals.setdefault('proposed_calculation_method', operation.calculation_method)
            records |= super().create(vals)
        return records

    def write(self, vals):
        protected = {
            'original_outstanding_capital', 'original_payoff_amount',
            'original_interest_rate', 'original_rate_period', 'original_term_months',
            'successor_operation_id', 'original_operation_closed', 'completed_date', 'state',
            'approved_capital', 'approved_interest', 'approved_late_fees', 'approved_by', 'approved_at',
        }
        if protected.intersection(vals):
            raise ValidationError(_('El historial y el estado solo pueden cambiar mediante las acciones de reestructuracion.'))
        if 'operation_id' in vals and any(rec.operation_id.id != vals['operation_id'] for rec in self):
            raise ValidationError(_('La operacion original no puede sustituirse. Cree otra solicitud.'))
        proposal_fields = {
            'operation_id', 'proposed_principal_amount', 'proposed_interest_rate',
            'proposed_rate_period', 'proposed_term_months',
            'proposed_calculation_method', 'reason', 'request_date', 'settlement_method',
        }
        if proposal_fields.intersection(vals):
            locked = self.filtered(lambda r: r.state in ('approved', 'prepared', 'cancelled'))
            if locked:
                raise ValidationError(_('Una reestructuracion aprobada no puede modificarse. Cree una nueva solicitud para conservar la auditoria.'))
        return super().write(vals)

    def _settlement_components(self):
        self.ensure_one()
        if self.original_operation_closed:
            return 0.0, 0.0, 0.0
        today = fields.Date.context_today(self)
        operation = self.operation_id
        interest = sum(max(line.interest - line.interest_paid, 0.0)
                       for line in operation.schedule_line_ids if line.date and line.date <= today)
        late = sum(max(line.late_fee_due - line.late_fee_paid, 0.0) for line in operation.schedule_line_ids)
        rounding = self.currency_id.round
        return tuple(rounding(value) for value in (operation.outstanding_capital, interest, late))

    @api.depends('settlement_method', 'original_operation_closed', 'operation_id.outstanding_capital',
                 'operation_id.schedule_line_ids.date', 'operation_id.schedule_line_ids.interest',
                 'operation_id.schedule_line_ids.interest_paid', 'operation_id.schedule_line_ids.late_fee_due',
                 'operation_id.schedule_line_ids.late_fee_paid')
    def _compute_settlement_preview(self):
        for rec in self:
            capital, interest, late = rec._settlement_components() if rec.operation_id else (0.0, 0.0, 0.0)
            rec.pending_capital, rec.pending_interest, rec.pending_late_fees = capital, interest, late
            rec.suggested_principal = capital + (interest + late if rec.settlement_method == 'capitalize' else 0.0)

    @api.onchange('operation_id', 'settlement_method')
    def _onchange_settlement_method(self):
        for rec in self:
            if rec.operation_id and rec.settlement_method and rec.state in ('draft', 'review'):
                rec.proposed_principal_amount = rec.suggested_principal

    def action_refresh_proposal(self):
        self.check_access('write')
        if any(rec.state not in ('draft', 'review') for rec in self):
            raise ValidationError(_('Solo puede actualizar los saldos de una propuesta sin aprobar.'))
        for rec in self:
            if not rec.settlement_method:
                raise ValidationError(_('Seleccione la modalidad negociada.'))
            capital, interest, late = rec._settlement_components()
            rec.proposed_principal_amount = capital + (interest + late if rec.settlement_method == 'capitalize' else 0.0)
        return True

    def action_return_to_review(self):
        self._check_manager_action()
        self.mapped('successor_operation_id').check_access('write')
        for rec in self:
            successor = rec.successor_operation_id
            if rec.state not in ('approved', 'prepared') or rec.original_operation_closed:
                raise ValidationError(_('Solo puede revisar una aprobacion antes de completar la sustitucion.'))
            if successor and (successor.state not in ('draft', 'review', 'approved') or successor.contract_signed
                              or successor.disbursement_ids.filtered(lambda d: d.state == 'posted')):
                raise ValidationError(_('No puede sustituir una nueva operacion ya contratada o desembolsada. Regularice primero su contrato.'))
        for rec in self:
            if rec.successor_operation_id:
                rec.successor_operation_id.state = 'cancelled'
        super().write({'state': 'review', 'successor_operation_id': False,
                       'approved_by': False, 'approved_at': False,
                       'approved_capital': 0.0, 'approved_interest': 0.0, 'approved_late_fees': 0.0})
        return True

    def _check_approved_settlement(self):
        self.ensure_one()
        if not self.settlement_method or not self.approved_at:
            raise ValidationError(_('Debe registrar y aprobar la modalidad de reestructuracion.'))
        capital, interest, late = self._settlement_components()
        if not self.currency_id.is_zero(capital - self.approved_capital):
            raise ValidationError(_('El capital cambio despues de la aprobacion. Revise y apruebe nuevamente la propuesta.'))
        if self.settlement_method == 'pay_separately':
            if not self.currency_id.is_zero(interest) or not self.currency_id.is_zero(late):
                raise ValidationError(_('Registre el pago de todos los intereses exigibles y la mora antes de preparar o completar la reestructuracion.'))
        elif (not self.currency_id.is_zero(interest - self.approved_interest)
              or not self.currency_id.is_zero(late - self.approved_late_fees)):
            raise ValidationError(_('Los intereses o la mora cambiaron despues de aprobar. Revise y apruebe nuevamente la propuesta.'))

    def unlink(self):
        if any(rec.state != 'draft' or rec.successor_operation_id for rec in self):
            raise ValidationError(_('Solo puede eliminar solicitudes en borrador sin una operacion sucesora.'))
        return super().unlink()

    def _check_manager_action(self):
        self.check_access('write')
        if not self.env.su and not self.env.user.has_group('lenka_financiero.group_lenka_manager'):
            raise AccessError(_('Solo un gerente de Lenka puede aprobar o completar una reestructuracion.'))
        self.mapped('operation_id').check_access('write')

    @api.constrains('proposed_principal_amount', 'proposed_interest_rate', 'proposed_term_months')
    def _check_proposal(self):
        for rec in self:
            if rec.proposed_principal_amount <= 0:
                raise ValidationError(_('El nuevo capital debe ser mayor que cero.'))
            if rec.proposed_interest_rate < 0:
                raise ValidationError(_('La nueva tasa no puede ser negativa.'))
            if rec.proposed_term_months <= 0:
                raise ValidationError(_('El nuevo plazo debe ser mayor que cero.'))

    def action_submit(self):
        self.check_access('write')
        for rec in self:
            if rec.state != 'draft':
                continue
            if rec.operation_id.state != 'active':
                raise ValidationError(_('La operacion original debe continuar activa.'))
            super(LenkaRestructuring, rec).write({'state': 'review'})
        return True

    def action_approve(self):
        self._check_manager_action()
        for rec in self:
            if rec.state != 'review':
                raise ValidationError(_('La reestructuracion debe estar en revision antes de aprobarse.'))
            if rec.operation_id.state != 'active':
                raise ValidationError(_('La operacion original debe continuar activa.'))
            if rec.operation_id.payment_ids.filtered(lambda p: p.state == 'posted' and p.unapplied_amount > 0.01):
                raise ValidationError(_('Existen cobros con saldo sin aplicar. Regularicelos antes de aprobar la reestructuracion.'))
            if not rec.settlement_method:
                raise ValidationError(_('Seleccione la modalidad negociada antes de aprobar.'))
            capital, interest, late = rec._settlement_components()
            expected = capital + (interest + late if rec.settlement_method == 'capitalize' else 0.0)
            if not rec.currency_id.is_zero(rec.proposed_principal_amount - expected):
                raise ValidationError(_('El nuevo capital no coincide con la modalidad y los saldos actuales. Actualice la propuesta antes de aprobar.'))
            super(LenkaRestructuring, rec).write({
                'state': 'approved', 'approved_capital': capital,
                'approved_interest': interest, 'approved_late_fees': late,
                'approved_by': self.env.user.id, 'approved_at': fields.Datetime.now(),
            })
        return True

    def action_prepare_successor(self):
        self._check_manager_action()
        for rec in self:
            if rec.state == 'prepared' and rec.successor_operation_id:
                continue
            if rec.state != 'approved':
                raise ValidationError(_('Apruebe la reestructuracion antes de preparar la nueva operacion.'))
            if rec.successor_operation_id:
                continue
            if rec.operation_id.state != 'active':
                raise ValidationError(_('La operacion original debe continuar activa.'))
            rec._check_approved_settlement()
            successor = self.env['lenka.financial.operation'].create({
                'partner_id': rec.partner_id.id,
                'guarantor_ids': [(6, 0, rec.operation_id.guarantor_ids.ids)],
                'operation_type': rec.operation_id.operation_type,
                'product_id': rec.operation_id.product_id.id,
                'company_id': rec.company_id.id,
                'currency_id': rec.currency_id.id,
                'principal_amount': rec.proposed_principal_amount,
                'down_payment': 0.0,
                'interest_rate': rec.proposed_interest_rate,
                'rate_period': rec.proposed_rate_period,
                'term_months': rec.proposed_term_months,
                'calculation_method': rec.proposed_calculation_method,
                'is_quote': False,
                'state': 'review',
                'notes': _('Preparada desde reestructuracion %s de la operacion %s. La operacion original permanece intacta hasta completar contrato y cierre controlado.') % (rec.name, rec.operation_id.name),
            })
            if successor.calculation_method != 'custom':
                successor.action_generate_schedule()
            super(LenkaRestructuring, rec).write({
                'successor_operation_id': successor.id,
                'state': 'prepared',
            })
        return True

    def action_complete_restructuring(self):
        self._check_manager_action()
        for rec in self:
            if rec.original_operation_closed:
                continue
            if rec.state != 'prepared' or not rec.successor_operation_id:
                raise ValidationError(_('Primero prepare la nueva operacion de la reestructuracion.'))
            successor = rec.successor_operation_id
            if successor.state not in ('contracted', 'active'):
                raise ValidationError(_('La nueva operacion debe estar contratada antes de trasladar el saldo y cerrar la operacion original.'))
            if successor.disbursement_ids.filtered(lambda d: d.state == 'posted'):
                raise ValidationError(_('La reestructuracion traslada deuda existente; no debe incluir un nuevo desembolso de efectivo.'))
            original = rec.operation_id
            if original.state != 'active':
                raise ValidationError(_('La operacion original debe continuar activa hasta completar la sustitucion.'))
            if original.payment_ids.filtered(lambda p: p.state == 'posted' and p.unapplied_amount > 0.01):
                raise ValidationError(_('Existen cobros sin aplicar en la operacion original. Regularicelos antes de completar la reestructuracion.'))
            rec._check_approved_settlement()
            if (successor.partner_id != original.partner_id
                    or successor.company_id != original.company_id
                    or successor.currency_id != original.currency_id
                    or successor.operation_type != original.operation_type
                    or not rec.currency_id.is_zero(successor.financed_amount - rec.proposed_principal_amount)
                    or successor.interest_rate != rec.proposed_interest_rate
                    or successor.rate_period != rec.proposed_rate_period
                    or successor.term_months != rec.proposed_term_months
                    or successor.calculation_method != rec.proposed_calculation_method):
                raise ValidationError(_('La nueva operacion debe conservar las condiciones aprobadas de la reestructuracion.'))
            super(LenkaRestructuring, rec).write({
                'original_operation_closed': True, 'completed_date': fields.Date.context_today(rec),
            })
            if successor.state == 'contracted':
                successor.action_activate()
            original.state = 'done'
            original.guarantee_ids.filtered(lambda g: g.state in ('accepted', 'active')).write({'state': 'release_pending'})
        return True

    def action_cancel(self):
        self.check_access('write')
        for rec in self:
            if rec.state == 'prepared':
                raise ValidationError(_('No se puede cancelar desde aqui una reestructuracion que ya preparo una nueva operacion. Revise primero la operacion sucesora.'))
            super(LenkaRestructuring, rec).write({'state': 'cancelled'})
        return True


class LenkaOperationRestructuring(models.Model):
    _inherit = 'lenka.financial.operation'

    restructuring_out_ids = fields.One2many('lenka.restructuring', 'operation_id', copy=False)
    restructuring_in_ids = fields.One2many('lenka.restructuring', 'successor_operation_id', copy=False)
    transferred_capital = fields.Monetary(string='Capital trasladado por reestructuracion', compute='_compute_transferred_amounts')
    restructured_funding_amount = fields.Monetary(string='Saldo recibido por reestructuracion', compute='_compute_transferred_amounts')

    @api.depends('restructuring_out_ids.original_operation_closed', 'restructuring_out_ids.approved_capital',
                 'restructuring_in_ids.original_operation_closed', 'restructuring_in_ids.proposed_principal_amount')
    def _compute_transferred_amounts(self):
        for rec in self:
            rec.transferred_capital = sum(rec.restructuring_out_ids.filtered('original_operation_closed').mapped('approved_capital'))
            rec.restructured_funding_amount = sum(rec.restructuring_in_ids.filtered('original_operation_closed').mapped('proposed_principal_amount'))

    @api.depends('financed_amount', 'schedule_line_ids.capital_paid', 'schedule_line_ids.interest_paid',
                 'schedule_line_ids.late_fee_paid', 'payment_ids.state', 'payment_ids.extra_capital_amount',
                 'payment_ids.card_fee_amount', 'payment_ids.net_bank_amount', 'transferred_capital')
    def _compute_collection_totals(self):
        super()._compute_collection_totals()
        for rec in self:
            rec.outstanding_capital = max(rec.outstanding_capital - rec.transferred_capital, 0.0)

    @api.depends('disbursement_ids.state', 'disbursement_ids.amount', 'financed_amount', 'restructured_funding_amount')
    def _compute_disbursed_amount(self):
        super()._compute_disbursed_amount()
        for rec in self:
            rec.pending_disbursement = max(rec.financed_amount - rec.disbursed_amount - rec.restructured_funding_amount, 0.0)

    def get_payoff_amount(self):
        self.ensure_one()
        if self.restructuring_out_ids.filtered('original_operation_closed'):
            return 0.0
        return super().get_payoff_amount()

    def write(self, vals):
        identity_fields = {'partner_id', 'company_id', 'currency_id', 'operation_type'}
        if identity_fields.intersection(vals):
            for rec in self.filtered('restructuring_in_ids'):
                for name in identity_fields.intersection(vals):
                    current = rec[name].id if name != 'operation_type' else rec[name]
                    if vals[name] != current:
                        raise ValidationError(_('La operacion sucesora debe conservar el cliente, la empresa, la moneda y el tipo de la operacion original.'))
        if 'state' in vals and vals['state'] != 'done' and any(rec.restructuring_out_ids.filtered('original_operation_closed') for rec in self):
            raise ValidationError(_('Una operacion sustituida por reestructuracion no puede reabrirse.'))
        return super().write(vals)


class LenkaRestructuringDisbursement(models.Model):
    _inherit = 'lenka.disbursement'

    def action_post(self):
        self.check_access('write')
        if any(rec.state == 'draft' and rec.operation_id.restructuring_in_ids for rec in self):
            raise ValidationError(_('Complete la sustitucion desde Reestructuraciones. El saldo se traslada sin un nuevo desembolso de efectivo.'))
        return super().action_post()
