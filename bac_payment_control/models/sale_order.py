from odoo import _, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _bac_contains_enabled_products(self):
        self.ensure_one()
        lines = self.order_line.filtered(
            lambda line: not line.display_type and line.product_template_id.bac_payment_enabled
        )
        return bool(lines)

    bac_payment_control_ids = fields.One2many(
        'bac.payment.control',
        'order_id',
        string='Controles BAC',
    )
    bac_payment_control_count = fields.Integer(
        string='Controles BAC',
        compute='_compute_bac_payment_metrics',
    )
    bac_payment_status = fields.Selection(
        [
            ('no_bac', 'Sin BAC'),
            ('pending', 'Pendiente'),
            ('paid', 'Pagado'),
            ('duplicate', 'Con duplicados'),
            ('mismatch', 'Con diferencias'),
        ],
        string='Estado BAC',
        compute='_compute_bac_payment_metrics',
    )

    def _compute_bac_payment_metrics(self):
        for order in self:
            controls = order.bac_payment_control_ids
            order.bac_payment_control_count = len(controls)
            if not controls:
                order.bac_payment_status = 'no_bac'
            elif any(control.duplicate_attempt_count for control in controls):
                order.bac_payment_status = 'duplicate'
            elif any(control.payment_state == 'mismatch' for control in controls):
                order.bac_payment_status = 'mismatch'
            elif any(control.payment_state == 'paid' for control in controls):
                order.bac_payment_status = 'paid'
            else:
                order.bac_payment_status = 'pending'

    def _prepare_bac_payment_control_vals(self, line):
        template = line.product_template_id
        return {
            'order_id': self.id,
            'order_line_id': line.id,
            'product_id': line.product_id.id,
            'configured_currency_id': template.bac_payment_currency_id.id,
            'configured_amount': template.bac_payment_amount,
            'expected_amount': line.price_total,
            'payment_link': template.bac_payment_link,
            'note': _('Control generado desde el pedido %s.') % (self.name or ''),
        }

    def action_prepare_bac_payment_controls(self):
        control_model = self.env['bac.payment.control']
        for order in self:
            eligible_lines = order.order_line.filtered(
                lambda line: not line.display_type and line.product_template_id.bac_payment_enabled
            )
            for line in eligible_lines:
                control = order.bac_payment_control_ids.filtered(lambda current: current.order_line_id == line)[:1]
                values = order._prepare_bac_payment_control_vals(line)
                if control:
                    control.write(values)
                else:
                    control_model.create(values)
        return True

    def action_view_bac_payment_controls(self):
        self.ensure_one()
        action = self.env.ref('bac_payment_control.action_bac_payment_control').read()[0]
        action['domain'] = [('order_id', '=', self.id)]
        action['context'] = {
            'default_order_id': self.id,
            'default_partner_id': self.partner_id.id,
        }
        return action