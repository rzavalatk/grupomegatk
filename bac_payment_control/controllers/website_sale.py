from urllib.parse import quote

from odoo import http
from odoo.http import request
from odoo.tools.misc import format_amount
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleBacPaymentControl(WebsiteSale):

    def _get_shop_payment_values(self, order, **kwargs):
        values = super()._get_shop_payment_values(order, **kwargs)
        bac_payment_controls = []
        if order and order._bac_contains_enabled_products():
            controls = order.sudo().bac_payment_control_ids.filtered(
                lambda control: control.payment_link and control.payment_state != 'cancelled'
            )
            state_labels = dict(request.env['bac.payment.control']._fields['payment_state'].selection)
            bac_payment_controls = [
                {
                    'product_name': control.product_id.display_name,
                    'payment_link': control.payment_link,
                    'configured_amount_display': format_amount(
                        request.env,
                        control.configured_amount,
                        control.configured_currency_id,
                    ),
                    'payment_state': control.payment_state,
                    'payment_state_label': state_labels.get(control.payment_state, control.payment_state),
                    'note': control.note,
                }
                for control in controls
            ]
        values.update({
            'bac_payment_controls': bac_payment_controls,
            'bac_has_payment_links': bool(bac_payment_controls),
        })
        return values

    def _bac_get_setting(self, key, default=False):
        param = request.env['ir.config_parameter'].sudo().get_param(key)
        if param is None:
            return default
        return str(param).strip().lower() in ('1', 'true', 'yes', 'on')

    def _bac_order_requires_registered_payment(self, order):
        if not order or not order._bac_contains_enabled_products():
            return False
        return self._bac_get_setting('bac_payment_control.registered_only_payment', True)

    def _bac_auto_prepare_controls(self, order):
        if not order:
            return
        auto_prepare = self._bac_get_setting('bac_payment_control.auto_prepare_checkout', True)
        if not auto_prepare:
            return
        if not order._bac_contains_enabled_products():
            return
        if order.state in ('draft', 'sent', 'sale'):
            order.sudo().action_prepare_bac_payment_controls()

    @http.route(['/shop/payment'], type='http', auth='public', website=True, sitemap=False)
    def shop_payment(self, **post):
        order = request.website.sale_get_order()
        if order and self._bac_order_requires_registered_payment(order):
            if request.env.user == request.website.user_id:
                redirect_target = quote('/shop/payment?bac_login_required=1', safe='')
                return request.redirect('/web/login?redirect=%s' % redirect_target)
        self._bac_auto_prepare_controls(order)
        return super().shop_payment(**post)