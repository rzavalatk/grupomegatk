"""Audited correction of an unpaid contracted loan's calendar, never its amounts."""
import hashlib
import json

from markupsafe import Markup, escape
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


# An RPC context cannot manufacture this Python identity. No public action returns it.
_DATE_CORRECTION_TOKEN = object()
_DATE_FIELDS = {'date', 'contract_date', 'first_payment_date'}
_SCHEDULE_FIELDS = [
    'sequence', 'date', 'opening_balance', 'capital', 'interest', 'extra_charge',
    'payment', 'closing_balance', 'capital_paid', 'interest_paid', 'late_fee_paid', 'late_fee_due',
]


class LenkaContractDateCorrection(models.Model):
    _inherit = 'lenka.financial.operation'

    can_correct_contract_dates = fields.Boolean(compute='_compute_can_correct_contract_dates')

    @api.depends_context('uid', 'allowed_company_ids')
    @api.depends('state', 'company_id.lenka_sole_signature_approver_id')
    def _compute_can_correct_contract_dates(self):
        for rec in self:
            rec.can_correct_contract_dates = (
                rec.state == 'contracted'
                and rec.company_id in self.env.companies
                and rec.company_id.lenka_sole_signature_approver_id == self.env.user
                and self.env.user.has_group('lenka_financiero.group_lenka_sole_authorizer')
                and self.env.user.has_group('lenka_financiero.group_lenka_manager'))

    def _is_contract_date_correction_write(self, vals):
        return (len(self) == 1
                and self.env.context.get('_lenka_contract_date_token') is _DATE_CORRECTION_TOKEN
                and self.env.context.get('_lenka_contract_date_operation') == self.id
                and set(vals) <= _DATE_FIELDS)

    def _require_contract_date_authorizer(self):
        self.ensure_one()
        self.check_access('write')
        if (self.company_id not in self.env.companies
                or self.company_id.lenka_sole_signature_approver_id != self.env.user
                or not self.env.user.has_group('lenka_financiero.group_lenka_sole_authorizer')
                or not self.env.user.has_group('lenka_financiero.group_lenka_manager')):
            raise AccessError(_('Solo Luis Moran, configurado para esta empresa y con permisos de gerente, puede corregir estas fechas.'))

    def _validate_contract_date_correction(self):
        self._require_contract_date_authorizer()
        if self.state != 'contracted' or self.operation_type != 'loan' or self.is_quote:
            raise ValidationError(_('La correccion solo admite prestamos contratados, todavia sin activar.'))
        if self.security_mode == 'sole_signature' and (
                self.sole_signature_status != 'approved'
                or self.approved_by != self.company_id.lenka_sole_signature_approver_id):
            raise ValidationError(_('El prestamo debe conservar la autorizacion exclusiva de Luis Moran.'))
        lines = self.schedule_line_ids.sorted('sequence')
        lines.check_access('write')
        if (self.calculation_method == 'custom' or len(lines) != self.term_months
                or lines.mapped('sequence') != list(range(1, self.term_months + 1))):
            raise ValidationError(_('Se requiere un plan mensual completo y regular; revise los planes personalizados por separado.'))
        first = self.first_payment_date or lines[:1].date
        if not first or any(l.date != fields.Date.add(first, months=l.sequence - 1) for l in lines):
            raise ValidationError(_('Las fechas existentes no forman un calendario mensual regular.'))
        # A cancelled collection may still have an audit/allocation: do not reinterpret it.
        if self.payment_ids or any(l.capital_paid or l.interest_paid or l.late_fee_paid or l.late_fee_due for l in lines):
            raise ValidationError(_('Existen cobros o mora registrada. Se requiere revision separada antes de corregir el calendario.'))
        if self.env['lenka.payment.allocation'].search_count([('schedule_line_id', 'in', lines.ids)]):
            raise ValidationError(_('Existen aplicaciones de cobros vinculadas al plan.'))
        if self.restructured_funding_amount or self.env['lenka.restructuring'].search_count([
                '|', ('operation_id', '=', self.id), ('successor_operation_id', '=', self.id)]):
            raise ValidationError(_('Una operacion vinculada a reestructuraciones requiere revision separada.'))
        moves = self.disbursement_ids.mapped('move_id') | self.disbursement_ids.mapped('refinance_move_id')
        moves.check_access('read')
        if moves.filtered(lambda m: m.reversed_entry_id or m.reversal_move_ids.filtered(lambda r: r.state == 'posted')):
            raise ValidationError(_('Existe una partida revertida; revise la operacion con Contabilidad.'))
        capital = moves.line_ids.filtered(lambda l: l.account_id == self.company_id.lenka_portfolio_account_id)
        if any(l.reconciled or l.matched_debit_ids or l.matched_credit_ids for l in capital):
            raise ValidationError(_('La CxC tiene conciliaciones. No puede corregirse como un prestamo sin cobros.'))
        return lines

    def _contract_dates_snapshot(self):
        self.ensure_one()
        return {
            'operation': self.read([
                'date', 'contract_date', 'first_payment_date', 'state', 'partner_id', 'company_id',
                'currency_id', 'principal_amount', 'down_payment', 'interest_rate', 'rate_period',
                'term_months', 'calculation_method', 'interest_only_months', 'contract_signed',
                'approved_by', 'approval_date', 'sole_signature_status',
            ])[0],
            'schedule': self.schedule_line_ids.sorted('sequence').read(_SCHEDULE_FIELDS),
            'payments': self.payment_ids.read(['state', 'amount', 'payment_date', 'move_id']),
            'disbursements': self.disbursement_ids.sorted('id').read([
                'state', 'date', 'amount', 'move_id', 'refinance_line_id', 'capital_due_date']),
            'documents': self.generated_document_ids.sorted('id').read([
                'state', 'attachment_id', 'signed_date', 'write_date']),
        }

    def _contract_dates_fingerprint(self):
        payload = json.dumps(self._contract_dates_snapshot(), default=str, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def action_open_contract_date_correction(self):
        self.ensure_one()
        self._validate_contract_date_correction()
        return {
            'type': 'ir.actions.act_window', 'name': _('Corregir fechas del contrato'),
            'res_model': 'lenka.contract.date.wizard', 'view_mode': 'form', 'target': 'new',
            'context': {'default_operation_id': self.id},
        }

    def _correct_contract_dates(self, operation_date, contract_date, first_payment_date, reason, fingerprint):
        self._require_contract_date_authorizer()
        if not all((operation_date, contract_date, first_payment_date, (reason or '').strip(), fingerprint)):
            raise ValidationError(_('Indique las tres fechas, el motivo y una revision vigente de la operacion.'))
        operation_date, contract_date, first_payment_date = map(
            fields.Date.to_date, (operation_date, contract_date, first_payment_date))
        if operation_date > first_payment_date or contract_date >= first_payment_date:
            raise ValidationError(_('La primera cuota debe ser posterior al contrato y no anterior a la operacion.'))
        with self.env.cr.savepoint():
            self.flush_recordset()
            self.env.cr.execute('SELECT id FROM lenka_financial_operation WHERE id = %s FOR UPDATE', [self.id])
            # Serialize with disbursement and collection actions using the same operation row.
            self.env.cr.execute('UPDATE lenka_financial_operation SET write_date = write_date WHERE id = %s', [self.id])
            self.env.invalidate_all()
            lines = self._validate_contract_date_correction()
            if fingerprint != self._contract_dates_fingerprint():
                raise ValidationError(_('La operacion cambio desde que abrio la revision. Cierre y vuelva a abrir el asistente.'))
            if any(d.date < contract_date or d.date < operation_date
                   for d in self.disbursement_ids.filtered(lambda d: d.state == 'posted')):
                raise ValidationError(_('El contrato y la operacion no pueden quedar despues de un desembolso aplicado.'))
            if (self.date, self.contract_date, self.first_payment_date) == (operation_date, contract_date, first_payment_date):
                raise ValidationError(_('Las fechas indicadas ya coinciden con las actuales.'))
            before = self._contract_dates_snapshot()
            scoped = self.with_context(
                _lenka_contract_date_token=_DATE_CORRECTION_TOKEN, _lenka_contract_date_operation=self.id)
            scoped.write({'date': operation_date, 'contract_date': contract_date, 'first_payment_date': first_payment_date})
            for line in lines:
                line.with_env(scoped.env).write({'date': fields.Date.add(first_payment_date, months=line.sequence - 1)})
            # IDs, principal, interest and all accounting records remain identical.
            after = self._contract_dates_snapshot()
            self.with_context(mail_notify_force_send=False, mail_create_nosubscribe=True).message_post(
                subtype_xmlid='mail.mt_note',
                body=Markup('<b>Correccion de fechas de captura por %s</b><p>Motivo: %s</p>'
                            '<p>Se conservan importes, autorizacion, desembolsos, partidas y documentos firmados. '
                            'El PDF firmado original no se sustituye. El vencimiento contable de la CxC se revisa por separado.</p>'
                            '<p>Antes:</p><pre>%s</pre><p>Despues:</p><pre>%s</pre>') % (
                    escape(self.env.user.name), escape(reason.strip()),
                    escape(json.dumps(before, default=str, ensure_ascii=False)),
                    escape(json.dumps(after, default=str, ensure_ascii=False))))
        return True


class LenkaAmortizationDateCorrection(models.Model):
    _inherit = 'lenka.amortization.line'

    def _is_contract_date_correction_write(self, vals):
        operations = self.mapped('operation_id')
        return (set(vals) == {'date'} and len(operations) == 1
                and operations._is_contract_date_correction_write(vals))


class LenkaContractDateWizard(models.TransientModel):
    _name = 'lenka.contract.date.wizard'
    _description = 'Correccion auditada de fechas de un prestamo contratado sin cobros'

    operation_id = fields.Many2one('lenka.financial.operation', required=True, readonly=True)
    fingerprint = fields.Char(required=True, readonly=True)
    operation_date = fields.Date(string='Fecha de la operacion', required=True)
    contract_date = fields.Date(string='Fecha del contrato', required=True)
    first_payment_date = fields.Date(string='Primera cuota correcta', required=True)
    last_payment_date = fields.Date(string='Ultima cuota resultante', compute='_compute_preview')
    level_payment_start_date = fields.Date(string='Inicio de cuota nivelada resultante', compute='_compute_preview')
    reason = fields.Text(string='Motivo de la correccion', required=True)
    confirmed = fields.Boolean(string='Confirmo que son las fechas pactadas y una correccion de captura')

    @api.depends('first_payment_date', 'operation_id.term_months', 'operation_id.interest_only_months', 'operation_id.calculation_method')
    def _compute_preview(self):
        for rec in self:
            rec.last_payment_date = fields.Date.add(rec.first_payment_date, months=rec.operation_id.term_months - 1) if rec.first_payment_date else False
            rec.level_payment_start_date = (fields.Date.add(rec.first_payment_date, months=rec.operation_id.interest_only_months)
                                           if rec.first_payment_date and rec.operation_id.calculation_method == 'interest_then_level' else False)

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        if vals.get('operation_id'):
            operation = self.env['lenka.financial.operation'].browse(vals['operation_id'])
            operation._validate_contract_date_correction()
            defaults = {'fingerprint': operation._contract_dates_fingerprint(), 'operation_date': operation.date,
                        'contract_date': operation.contract_date, 'first_payment_date': operation.first_payment_date}
            vals.update({k: v for k, v in defaults.items() if k in fields_list})
        return vals

    def action_apply(self):
        self.ensure_one()
        if not self.confirmed:
            raise ValidationError(_('Confirme que se trata de una correccion de las fechas pactadas.'))
        self.operation_id._correct_contract_dates(
            self.operation_date, self.contract_date, self.first_payment_date, self.reason, self.fingerprint)
        return {'type': 'ir.actions.act_window_close'}
