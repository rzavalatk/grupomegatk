from markupsafe import Markup, escape

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


LOCKED_STATES = ('approved', 'contracted', 'active', 'done')
CONFIG_FIELDS = {'lenka_sole_signature_approver_id', 'lenka_sole_signature_requester_id'}
AUDIT_FIELDS = {
    'sole_signature_status', 'sole_signature_requested_by', 'sole_signature_requested_at',
    'sole_signature_authorizer_id', 'sole_signature_activity_id',
    'sole_signature_notification_id', 'sole_signature_decided_at',
    'approved_by', 'approval_date',
}
TERMS_FIELDS = {
    'partner_id', 'company_id', 'currency_id', 'operation_type', 'product_id', 'date',
    'principal_amount', 'down_payment', 'interest_rate', 'rate_period', 'term_months',
    'first_payment_date', 'calculation_method', 'interest_only_months',
    'balloon_base_payment', 'residual_purchase_percent', 'recalculation_policy',
    'guarantor_ids', 'guarantee_ids', 'security_mode', 'approval_notes',
    'schedule_line_ids', 'extra_payment_line_ids', 'is_quote',
}


class LenkaCompany(models.Model):
    _inherit = 'res.company'

    lenka_sole_signature_approver_id = fields.Many2one(
        'res.users', string='Luis Moran - autorizador exclusivo a sola firma',
        domain="[('share', '=', False), ('active', '=', True)]", ondelete='restrict',
        help='Seleccione el usuario verificado de Luis Moran. Solo este usuario puede decidir estas solicitudes.',
    )
    lenka_sole_signature_requester_id = fields.Many2one(
        'res.users', string='Elisa Rodriguez - responsable de solicitudes',
        domain="[('share', '=', False), ('active', '=', True)]", ondelete='restrict',
    )

    @api.constrains('lenka_sole_signature_approver_id', 'lenka_sole_signature_requester_id')
    def _check_sole_signature_users(self):
        for company in self:
            approver = company.lenka_sole_signature_approver_id
            requester = company.lenka_sole_signature_requester_id
            if approver and approver == requester:
                raise ValidationError(_('El solicitante y el autorizador deben ser usuarios distintos.'))
            for user in approver | requester:
                if not user.active or user.share or company not in user.company_ids:
                    raise ValidationError(_('Los usuarios deben estar activos, ser internos y tener acceso a esta empresa.'))

    def write(self, vals):
        if CONFIG_FIELDS.intersection(vals) and not (self.env.su or self.env.user.has_group('base.group_system')):
            raise AccessError(_('Solo un administrador puede configurar los usuarios verificados de Luis Moran y Elisa Rodriguez.'))
        return super().write(vals)


class LenkaSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    lenka_sole_signature_approver_id = fields.Many2one(
        related='company_id.lenka_sole_signature_approver_id', readonly=False,
        groups='base.group_system',
    )
    lenka_sole_signature_requester_id = fields.Many2one(
        related='company_id.lenka_sole_signature_requester_id', readonly=False,
        groups='base.group_system',
    )


class LenkaSoleSignature(models.Model):
    _inherit = 'lenka.financial.operation'

    security_mode = fields.Selection([
        ('backed', 'Con aval o garantia'),
        ('sole_signature', 'Sin aval ni garantia - autorizacion de Luis Moran'),
    ], required=True, default='backed', string='Modalidad de respaldo', tracking=True)
    sole_signature_status = fields.Selection([
        ('none', 'Sin solicitar'), ('pending', 'Pendiente de autorizacion de Luis Moran'),
        ('approved', 'Autorizada por Luis Moran'), ('rejected', 'Rechazada por Luis Moran'),
    ], default='none', readonly=True, copy=False, tracking=True)
    sole_signature_requested_by = fields.Many2one('res.users', string='Solicitud enviada por', readonly=True, copy=False, tracking=True)
    sole_signature_requested_at = fields.Datetime(string='Solicitud enviada el', readonly=True, copy=False, tracking=True)
    sole_signature_authorizer_id = fields.Many2one('res.users', string='Autorizador asignado', readonly=True, copy=False, tracking=True)
    sole_signature_decided_at = fields.Datetime(string='Fecha de decision', readonly=True, copy=False, tracking=True)
    sole_signature_decision_notes = fields.Text(string='Observaciones de Luis Moran', copy=False, tracking=True)
    sole_signature_activity_id = fields.Many2one('mail.activity', readonly=True, copy=False, ondelete='set null')
    sole_signature_notification_id = fields.Many2one('mail.mail', readonly=True, copy=False, ondelete='set null')
    sole_signature_notification_state = fields.Selection(related='sole_signature_notification_id.state', string='Estado del correo', readonly=True)
    can_request_sole_signature = fields.Boolean(compute='_compute_sole_signature_actions')
    can_decide_sole_signature = fields.Boolean(compute='_compute_sole_signature_actions')
    can_request_legacy_sole_signature = fields.Boolean(compute='_compute_sole_signature_actions')

    @api.depends_context('uid')
    @api.depends('security_mode', 'state', 'sole_signature_status', 'sole_signature_authorizer_id', 'guarantor_ids', 'guarantee_ids', 'contract_signed', 'disbursed_amount',
                 'company_id.lenka_sole_signature_approver_id', 'company_id.lenka_sole_signature_requester_id')
    def _compute_sole_signature_actions(self):
        for rec in self:
            company = rec.company_id.sudo()
            rec.can_request_legacy_sole_signature = (
                rec.security_mode == 'backed' and rec.state == 'approved'
                and not rec.guarantor_ids and not rec.guarantee_ids
                and not rec.contract_signed and not rec.disbursed_amount
                and company.lenka_sole_signature_requester_id.id == self.env.uid
            )
            rec.can_request_sole_signature = (
                rec.security_mode == 'sole_signature' and rec.sole_signature_status in ('none', 'rejected')
                and rec.state in ('draft', 'review', 'rejected')
                and company.lenka_sole_signature_requester_id.id == self.env.uid
            )
            rec.can_decide_sole_signature = (
                rec.security_mode == 'sole_signature' and rec.sole_signature_status == 'pending'
                and rec.sole_signature_authorizer_id.id == self.env.uid
                and company.lenka_sole_signature_approver_id.id == self.env.uid
                and self.env.user.has_group('lenka_financiero.group_lenka_sole_authorizer')
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (AUDIT_FIELDS - {'approved_by', 'approval_date'}).intersection(vals):
                raise AccessError(_('El historial de autorizacion se registra mediante las acciones del sistema.'))
        records = super().create(vals_list)
        for rec in records.filtered(lambda r: r.security_mode == 'sole_signature'):
            if rec.state not in ('draft', 'review') or rec.sole_signature_status != 'none' or rec.approved_by or rec.approval_date:
                raise ValidationError(_('Cree la solicitud sin aval ni garantia en borrador y enviela a Luis Moran.'))
        records._check_sole_signature_backing()
        return records

    @api.constrains('security_mode', 'guarantor_ids', 'guarantee_ids')
    def _check_sole_signature_backing(self):
        for rec in self:
            if rec.security_mode == 'sole_signature' and (rec.guarantor_ids or rec.guarantee_ids):
                raise ValidationError(_('Una operacion sin aval ni garantia no debe incluir estos respaldos.'))

    def _sole_signature_users(self):
        self.ensure_one()
        company = self.company_id.sudo()
        approver = company.lenka_sole_signature_approver_id
        requester = company.lenka_sole_signature_requester_id
        company._check_sole_signature_users()
        if not approver or not requester:
            raise ValidationError(_('Configure los usuarios verificados de Luis Moran y Elisa Rodriguez en Ajustes de Financiero Lenka.'))
        if not approver.has_group('lenka_financiero.group_lenka_sole_authorizer'):
            raise ValidationError(_('El usuario de Luis Moran necesita el permiso Autorizacion exclusiva a sola firma.'))
        if not requester.has_group('lenka_financiero.group_lenka_user'):
            raise ValidationError(_('El usuario de Elisa Rodriguez necesita el permiso Usuario de Financiero Lenka.'))
        if not approver.email:
            raise ValidationError(_('El usuario de Luis Moran debe tener un correo verificado para recibir la solicitud.'))
        return approver, requester

    def _require_sole_authorizer(self):
        self.ensure_one()
        approver, requester = self._sole_signature_users()
        if self.env.uid != approver.id or self.sole_signature_authorizer_id != approver:
            raise AccessError(_('Solo el usuario asignado de Luis Moran puede autorizar o rechazar esta solicitud.'))
        if not self.env.user.has_group('lenka_financiero.group_lenka_sole_authorizer'):
            raise AccessError(_('Se requiere el permiso exclusivo de autorizacion a sola firma.'))
        return approver

    def _validate_sole_financials(self):
        self.ensure_one()
        self._check_sole_signature_backing()
        if self.is_quote or self.financed_amount <= 0 or self.term_months <= 0 or self.interest_rate < 0:
            raise ValidationError(_('Revise la solicitud, el monto financiado, la tasa y el plazo.'))
        if not (self.approval_notes or '').strip():
            raise ValidationError(_('Indique el motivo de la solicitud sin aval ni garantia.'))
        if not self.schedule_line_ids:
            raise ValidationError(_('Calcule el plan de pagos antes de enviar la solicitud.'))
        if self.document_ids.filtered(lambda d: d.required and (d.state != 'received' or not d.attachment_id)):
            raise ValidationError(_('Faltan documentos obligatorios del expediente.'))

    def action_request_sole_signature(self):
        self.check_access('write')
        for rec in self:
            approver, requester = rec._sole_signature_users()
            if self.env.uid != requester.id:
                raise AccessError(_('Solo la responsable asignada Elisa Rodriguez puede enviar estas solicitudes.'))
            if rec.security_mode != 'sole_signature' or rec.is_quote or rec.state not in ('draft', 'review', 'rejected') or rec.sole_signature_status not in ('none', 'rejected'):
                raise ValidationError(_('Convierta la cotizacion en solicitud y seleccione Sin aval ni garantia antes de enviarla.'))
            # Recalcular antes de congelar las condiciones que Luis revisara.
            rec.action_generate_schedule()
            rec._validate_sole_financials()
            sender = rec.company_id.email or self.env.user.email_formatted
            if not sender:
                raise ValidationError(_('Configure el correo del remitente de Lenka o de Elisa antes de enviar solicitudes.'))
            note = rec._sole_signature_request_body()
            activity = self.env['mail.activity'].sudo().create({
                'res_model_id': self.env['ir.model']._get_id(rec._name),
                'res_id': rec.id, 'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'user_id': approver.id, 'summary': _('Autorizar prestamo sin aval ni garantia'),
                'note': note, 'date_deadline': fields.Date.context_today(rec),
            })
            mail = self.env['mail.mail'].sudo().create({
                'subject': _('Lenka: solicitud pendiente de tu autorizacion - %s') % rec.name,
                'email_to': approver.email, 'email_from': sender, 'body_html': note,
                'model': rec._name, 'res_id': rec.id, 'auto_delete': False,
            })
            super(LenkaSoleSignature, rec).write({
                'state': 'review', 'sole_signature_status': 'pending',
                'sole_signature_requested_by': self.env.uid,
                'sole_signature_requested_at': fields.Datetime.now(),
                'sole_signature_authorizer_id': approver.id,
                'sole_signature_activity_id': activity.id, 'sole_signature_notification_id': mail.id,
                'sole_signature_decision_notes': False, 'sole_signature_decided_at': False,
            })
            rec.message_post(body=_('Solicitud enviada a Luis Moran por %s. La operacion queda pendiente de su autorizacion exclusiva.') % self.env.user.display_name, email_from=sender)
        return True

    def _sole_signature_request_body(self):
        self.ensure_one()
        body = Markup('<p>Solicitud pendiente de autorizacion de Luis Moran: prestamo sin aval ni garantia.</p><ul>')
        for label, value in [
            ('Operacion', self.name), ('Empresa', self.company_id.display_name),
            ('Cliente', self.partner_id.display_name),
            ('Monto', '%s %.2f' % (self.currency_id.name, self.financed_amount)),
            ('Tasa', '%s%% %s' % (self.interest_rate, self.rate_period)),
            ('Plazo', '%s meses' % self.term_months),
            ('Solicitado por', self.env.user.display_name), ('Motivo', self.approval_notes),
        ]:
            body += Markup('<li><strong>%s:</strong> %s</li>') % (escape(label), escape(value))
        url = '%s/web#id=%s&model=%s&view_type=form' % (self.get_base_url(), self.id, self._name)
        return body + Markup('</ul><p><a href="%s">Revisar y decidir en Odoo</a></p>') % escape(url)

    def action_request_legacy_sole_signature(self):
        self.check_access('write')
        for rec in self:
            approver, requester = rec._sole_signature_users()
            if self.env.uid != requester.id:
                raise AccessError(_('Solo Elisa Rodriguez puede reenviar esta operacion a autorizacion.'))
            if rec.security_mode != 'backed' or rec.state != 'approved' or rec.guarantor_ids or rec.guarantee_ids:
                raise ValidationError(_('Esta accion solo aplica a operaciones aprobadas que quedaron sin aval ni garantia.'))
            if rec.contract_signed or rec.contract_date or rec.disbursement_ids.filtered(lambda d: d.state == 'posted') or rec.generated_document_ids.filtered(lambda d: d.state == 'signed'):
                raise ValidationError(_('No puede reenviar una operacion contratada, firmada o desembolsada.'))
            previous = _('Aprobacion anterior reenviada para autorizacion exclusiva. Responsable anterior: %s; fecha anterior: %s.') % (rec.approved_by.display_name or '-', rec.approval_date or '-')
            super(LenkaSoleSignature, rec).write({
                'state': 'review', 'security_mode': 'sole_signature',
                'approved_by': False, 'approval_date': False,
            })
            rec.message_post(body=previous, email_from=rec.company_id.email or self.env.user.email_formatted)
            rec.action_request_sole_signature()
        return True

    def _validate_for_approval(self):
        self.ensure_one()
        if self.security_mode != 'sole_signature':
            return super()._validate_for_approval()
        self._require_sole_authorizer()
        if self.state != 'review' or self.sole_signature_status != 'pending':
            raise ValidationError(_('La solicitud debe estar pendiente de autorizacion de Luis Moran.'))
        self._validate_sole_financials()

    def action_approve(self):
        self.check_access('write')
        for rec in self:
            if rec.security_mode != 'sole_signature':
                if not self.env.su and not self.env.user.has_group('lenka_financiero.group_lenka_manager'):
                    raise AccessError(_('Solo la gerencia puede aprobar operaciones con respaldo.'))
                super(LenkaSoleSignature, rec).action_approve()
                continue
            rec._validate_for_approval()
            super(LenkaSoleSignature, rec).write({
                'state': 'approved', 'approved_by': self.env.uid, 'approval_date': fields.Datetime.now(),
                'sole_signature_status': 'approved', 'sole_signature_decided_at': fields.Datetime.now(),
            })
            rec._finish_sole_signature_activity(_('Autorizada por Luis Moran.'))
        return True

    def action_reject_sole_signature(self):
        self.check_access('write')
        for rec in self:
            rec._require_sole_authorizer()
            if rec.security_mode != 'sole_signature' or rec.state != 'review' or rec.sole_signature_status != 'pending':
                raise ValidationError(_('Solo puede rechazar una solicitud pendiente de autorizacion.'))
            if not (rec.sole_signature_decision_notes or '').strip():
                raise ValidationError(_('Indique el motivo del rechazo en Observaciones de Luis Moran.'))
            super(LenkaSoleSignature, rec).write({
                'state': 'rejected', 'sole_signature_status': 'rejected',
                'sole_signature_decided_at': fields.Datetime.now(),
            })
            rec._finish_sole_signature_activity(_('Rechazada por Luis Moran: %s') % rec.sole_signature_decision_notes)
        return True

    def _finish_sole_signature_activity(self, feedback):
        self.ensure_one()
        sender = self.company_id.email or self.env.user.email_formatted
        if not sender:
            raise ValidationError(_('Configure el correo del remitente antes de registrar la decision.'))
        if self.sole_signature_activity_id:
            self.sole_signature_activity_id.sudo().with_context(mail_notify_force_send=False).action_feedback(feedback=feedback)
        self.message_post(body=feedback, email_from=sender)

    def action_generate_schedule(self):
        if self.filtered(lambda r: r.security_mode == 'sole_signature' and r.sole_signature_status in ('pending', 'approved')):
            raise ValidationError(_('El plan enviado a Luis Moran no puede recalcularse mientras esta pendiente o autorizado.'))
        return super().action_generate_schedule()

    def action_mark_contracted(self):
        for rec in self:
            if rec.security_mode == 'backed' and not rec.guarantor_ids and not rec.guarantee_ids:
                raise ValidationError(_('Una operacion aprobada que quedo sin aval ni garantia necesita la autorizacion exclusiva de Luis Moran antes de contratar.'))
        return super().action_mark_contracted()

    def write(self, vals):
        sole = self.filtered(lambda r: r.security_mode == 'sole_signature' or vals.get('security_mode') == 'sole_signature')
        if sole and AUDIT_FIELDS.intersection(vals):
            raise AccessError(_('Utilice Enviar a Luis Moran, Autorizar o Rechazar para registrar la decision.'))
        if {'security_mode', 'guarantor_ids', 'guarantee_ids'}.intersection(vals) and self.filtered(lambda r: r.state in LOCKED_STATES or r.approval_date):
            raise ValidationError(_('No puede cambiar el respaldo de una operacion aprobada.'))
        if TERMS_FIELDS.intersection(vals) and sole.filtered(lambda r: r.sole_signature_status in ('pending', 'approved')):
            raise ValidationError(_('Las condiciones enviadas a Luis Moran no pueden modificarse.'))
        if 'sole_signature_decision_notes' in vals:
            for rec in sole:
                rec._require_sole_authorizer()
                if rec.sole_signature_status != 'pending':
                    raise ValidationError(_('Solo puede registrar observaciones en una solicitud pendiente.'))
        if 'state' in vals:
            for rec in sole:
                target = vals['state']
                if target == rec.state:
                    continue
                if rec.sole_signature_status == 'pending' or target == 'approved':
                    raise AccessError(_('La solicitud requiere la decision de Luis Moran mediante Autorizar o Rechazar.'))
                if rec.approval_date and target in ('draft', 'review'):
                    raise ValidationError(_('Una operacion autorizada no puede volver a borrador. Use una reestructuracion.'))
                if target in ('contracted', 'active', 'done'):
                    if rec.sole_signature_status != 'approved' or rec.approved_by != rec.sole_signature_authorizer_id:
                        raise ValidationError(_('La operacion requiere autorizacion exclusiva de Luis Moran antes de contratar o desembolsar.'))
                    if target == 'contracted':
                        if rec.state != 'approved' or not rec.contract_signed or not rec.generated_document_ids.filtered(lambda d: d.document_type == 'contract' and d.state == 'signed' and d.attachment_id):
                            raise ValidationError(_('Debe existir un contrato firmado y adjunto antes de contratar.'))
                    if target == 'active' and (rec.state != 'contracted' or rec.pending_disbursement > .01 or rec.disbursed_amount + rec.restructured_funding_amount <= 0):
                        raise ValidationError(_('Debe completar la contratacion y el fondeo antes de activar.'))
        return super().write(vals)


class LenkaGuaranteeProtection(models.Model):
    _inherit = 'lenka.guarantee'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if records.mapped('operation_id').filtered(lambda r: r.security_mode == 'sole_signature'):
            raise ValidationError(_('Una operacion sin aval ni garantia no admite garantias.'))
        return records

    def write(self, vals):
        if set(vals) - {'state'} and self.mapped('operation_id').filtered(lambda r: r.state in LOCKED_STATES or r.sole_signature_status == 'pending'):
            raise ValidationError(_('No puede modificar el respaldo de una operacion aprobada o enviada a autorizacion.'))
        if vals.get('operation_id') and self.env['lenka.financial.operation'].browse(vals['operation_id']).security_mode == 'sole_signature':
            raise ValidationError(_('No puede trasladar una garantia a una operacion sin respaldo.'))
        return super().write(vals)

    def unlink(self):
        if self.mapped('operation_id').filtered(lambda r: r.state in LOCKED_STATES or r.approval_date):
            raise ValidationError(_('No puede eliminar la garantia de una operacion aprobada.'))
        return super().unlink()


class LenkaExtraPlanProtection(models.Model):
    _inherit = 'lenka.extra.payment.plan'

    def _check_pending_operation(self):
        if self.mapped('operation_id').filtered(lambda r: r.security_mode == 'sole_signature' and r.sole_signature_status in ('pending', 'approved')):
            raise ValidationError(_('No puede cambiar pagos extraordinarios de una solicitud enviada a Luis Moran.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_pending_operation()
        return records

    def write(self, vals):
        self._check_pending_operation()
        if vals.get('operation_id'):
            operation = self.env['lenka.financial.operation'].browse(vals['operation_id'])
            if operation.security_mode == 'sole_signature' and operation.sole_signature_status in ('pending', 'approved'):
                raise ValidationError(_('No puede trasladar pagos a una solicitud enviada a Luis Moran.'))
        return super().write(vals)

    def unlink(self):
        self._check_pending_operation()
        return super().unlink()


class LenkaAmortizationProtection(models.Model):
    _inherit = 'lenka.amortization.line'

    def _check_authorization_plan(self):
        if self.mapped('operation_id').filtered(lambda r: r.security_mode == 'sole_signature' and r.sole_signature_status in ('pending', 'approved')):
            raise ValidationError(_('El plan pendiente o autorizado por Luis Moran no puede modificarse directamente.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_authorization_plan()
        return records

    def write(self, vals):
        protected = {'operation_id', 'sequence', 'date', 'opening_balance', 'capital', 'interest', 'extra_charge', 'payment', 'closing_balance'}
        if protected.intersection(vals):
            self._check_authorization_plan()
            if vals.get('operation_id'):
                operation = self.env['lenka.financial.operation'].browse(vals['operation_id'])
                if operation.security_mode == 'sole_signature' and operation.sole_signature_status in ('pending', 'approved'):
                    raise ValidationError(_('No puede trasladar cuotas a un plan enviado a Luis Moran.'))
        return super().write(vals)

    def unlink(self):
        self._check_authorization_plan()
        return super().unlink()
