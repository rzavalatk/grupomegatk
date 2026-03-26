from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class BacPaymentControl(models.Model):
    _name = 'bac.payment.control'
    _description = 'Control de pago BAC'
    _order = 'create_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True,
    )
    order_id = fields.Many2one(
        'sale.order',
        string='Pedido',
        required=True,
        ondelete='cascade',
    )
    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Linea de pedido',
        required=True,
        ondelete='cascade',
    )
    partner_id = fields.Many2one(
        related='order_id.partner_id',
        string='Cliente',
        store=True,
        readonly=True,
    )
    salesperson_id = fields.Many2one(
        related='order_id.user_id',
        string='Vendedor responsable',
        store=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=True,
        readonly=True,
    )
    configured_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda BAC',
        required=True,
    )
    configured_amount = fields.Monetary(
        string='Monto configurado',
        currency_field='configured_currency_id',
        required=True,
    )
    order_currency_id = fields.Many2one(
        related='order_id.currency_id',
        string='Moneda del pedido',
        store=True,
        readonly=True,
    )
    expected_amount = fields.Monetary(
        string='Monto esperado en pedido',
        currency_field='order_currency_id',
        required=True,
    )
    payment_link = fields.Char(
        string='Link BAC',
        required=True,
    )
    payment_state = fields.Selection(
        [
            ('pending', 'Pendiente'),
            ('paid', 'Pagado'),
            ('mismatch', 'Monto no coincide'),
            ('cancelled', 'Cancelado'),
        ],
        string='Estado',
        default='pending',
        required=True,
        tracking=True,
    )
    amount_matches = fields.Boolean(
        string='Monto coincide',
        compute='_compute_amount_matches',
        store=True,
    )
    payment_reference = fields.Char(string='Referencia pagada')
    incoming_reference = fields.Char(string='Referencia entrante')
    paid_on = fields.Datetime(string='Fecha de pago')
    duplicate_attempt_count = fields.Integer(string='Intentos duplicados', default=0)
    last_duplicate_reference = fields.Char(string='Ultima referencia duplicada')
    manual_validated_by_id = fields.Many2one(
        'res.users',
        string='Validado por',
        readonly=True,
    )
    manual_validated_on = fields.Datetime(
        string='Fecha de validacion',
        readonly=True,
    )
    note = fields.Text(string='Observaciones')

    def _check_manual_validation_permission(self):
        current_user = self.env.user
        for record in self:
            if current_user.has_group('sales_team.group_sale_manager'):
                continue
            if record.salesperson_id and record.salesperson_id == current_user:
                continue
            raise UserError(_(
                'Solo el vendedor responsable del pedido o un gerente de ventas puede validar o marcar pagos duplicados.'
            ))

    def _is_reference_used_in_order(self, reference):
        self.ensure_one()
        if not reference:
            return False
        domain = [
            ('order_id', '=', self.order_id.id),
            ('id', '!=', self.id),
            '|', '|',
            ('payment_reference', '=', reference),
            ('last_duplicate_reference', '=', reference),
            ('incoming_reference', '=', reference),
        ]
        return bool(self.search_count(domain))

    @api.constrains('order_id', 'payment_reference', 'last_duplicate_reference', 'incoming_reference')
    def _check_references_unique_per_order(self):
        for record in self:
            for field_name in ('payment_reference', 'last_duplicate_reference', 'incoming_reference'):
                reference = (record[field_name] or '').strip()
                if reference and record._is_reference_used_in_order(reference):
                    raise UserError(_('La referencia "%s" ya fue usada en este pedido. Debe ingresar una referencia unica por pedido.') % reference)

    @api.depends('order_id.name', 'product_id.display_name')
    def _compute_name(self):
        for record in self:
            order_name = record.order_id.name or _('Pedido')
            product_name = record.product_id.display_name or _('Producto')
            record.name = f'{order_name} - {product_name}'

    @api.depends('configured_amount', 'expected_amount', 'configured_currency_id', 'order_currency_id')
    def _compute_amount_matches(self):
        for record in self:
            same_currency = record.configured_currency_id == record.order_currency_id
            precision = record.order_currency_id.rounding if record.order_currency_id else 0.01
            same_amount = float_compare(
                record.configured_amount,
                record.expected_amount,
                precision_rounding=precision,
            ) == 0
            record.amount_matches = bool(same_currency and same_amount)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_payment_state_with_amount()
        for record in records:
            if record.payment_state == 'pending':
                responsible = record.order_id.user_id or self.env.user
                record.activity_schedule(
                    'mail.mail_activity_data_todo',
                    note=_(
                        'Pago BAC pendiente de validacion: Pedido <b>%s</b> — Producto <b>%s</b>. '
                        'Ingrese la referencia del comprobante BAC y valide el pago.'
                    ) % (record.order_id.name, record.product_id.display_name),
                    user_id=responsible.id,
                )
        return records

    def write(self, vals):
        result = super().write(vals)
        tracked_fields = {
            'configured_amount',
            'expected_amount',
            'configured_currency_id',
            'order_currency_id',
        }
        if tracked_fields.intersection(vals):
            self._sync_payment_state_with_amount()
        return result

    def _sync_payment_state_with_amount(self):
        for record in self:
            if record.payment_state == 'paid':
                continue
            record.payment_state = 'pending' if record.amount_matches else 'mismatch'

    def action_mark_paid(self):
        self._check_manual_validation_permission()
        for record in self:
            if not record.incoming_reference:
                raise UserError(_('Debe ingresar la referencia de comprobante antes de validar el pago manual.'))
            reference = record.incoming_reference.strip()
            if record._is_reference_used_in_order(reference):
                raise UserError(_('La referencia "%s" ya fue usada en este pedido. Debe ingresar una referencia unica por pedido.') % reference)
            if not record.amount_matches:
                raise UserError(_('No puede registrar el pago porque el monto del pedido no coincide con el monto configurado en BAC.'))
            if record.payment_state == 'paid':
                record.write({
                    'duplicate_attempt_count': record.duplicate_attempt_count + 1,
                    'last_duplicate_reference': reference,
                    'incoming_reference': False,
                })
                continue
            record.write({
                'payment_state': 'paid',
                'payment_reference': reference,
                'paid_on': fields.Datetime.now(),
                'manual_validated_by_id': self.env.user.id,
                'manual_validated_on': fields.Datetime.now(),
                'incoming_reference': False,
            })
            record.message_post(
                body=_(
                    'Pago BAC confirmado por <b>%s</b>.<br/>'
                    'Referencia de comprobante: <b>%s</b>'
                ) % (self.env.user.name, reference),
                partner_ids=record.partner_id.ids,
                subtype_xmlid='mail.mt_comment',
            )

    def action_mark_duplicate(self):
        self._check_manual_validation_permission()
        for record in self:
            if record.payment_state != 'paid':
                raise UserError(_('Solo puede marcar pagos duplicados sobre controles ya pagados.'))
            if not record.incoming_reference:
                raise UserError(_('Debe ingresar la referencia del segundo intento para registrar el duplicado.'))
            reference = record.incoming_reference.strip()
            if record._is_reference_used_in_order(reference):
                raise UserError(_('La referencia "%s" ya fue usada en este pedido. Debe ingresar una referencia unica por pedido.') % reference)
            record.write({
                'duplicate_attempt_count': record.duplicate_attempt_count + 1,
                'last_duplicate_reference': reference,
                'incoming_reference': False,
            })

    def action_cancel_control(self):
        self._check_manual_validation_permission()
        self.write({'payment_state': 'cancelled', 'incoming_reference': False})