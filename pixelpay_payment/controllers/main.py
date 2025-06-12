# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request


_logger = logging.getLogger(__name__)


class AuthorizeController(http.Controller):

    @http.route('/payment/pixelpay/get_acquirer_info', type='json', auth='public')
    def pixel_get_acquirer_info(self, acquirer_id):
        """ Return public information on the acquirer.

        :param int acquirer_id: The acquirer handling the transaction, as a `payment.acquirer` id
        :return: Information on the acquirer, namely: the state, payment method type, login ID, and
                 public client key
        :rtype: dict
        """
        acquirer_sudo = request.env['payment.acquirer'].sudo().browse(acquirer_id).exists()
        return {
            'state': acquirer_sudo.state,
            'payment_method_type': acquirer_sudo.pixel_payment_method_type,
            'pixel_endpoint': acquirer_sudo.pixel_endpoint,
            'pixel_key': acquirer_sudo.pixel_key,
            'pixel_secret_key': acquirer_sudo.pixel_secret_key,
        }

    @http.route('/payment/pixelpay/get_order_info', type='json', auth='public')
    def pixel_get_order_info(self, order_id):
        sale_order_sudo = request.env['sale.order'].sudo().search([('id', '=', order_id)])

        if not sale_order_sudo.partner_id.email:
            raise ValidationError(
                _("The email does not appear to be correct. Set an email in the billing address adfdf"))

        return {
            'saleOrderInfo': {
                'order_id': sale_order_sudo.id,
                'order_name': sale_order_sudo.name,
                'order_currency': sale_order_sudo.currency_id.name,
                'order_amount': sale_order_sudo.amount_total,
                'order_customer_name': sale_order_sudo.partner_id.name,
                'order_customer_email': sale_order_sudo.partner_id.email
            },
        }

    @http.route('/payment/pixelpay/get_invoice_info', type='json', auth='public')
    def pixel_get_invoice_info(self, invoice_id):
        sale_invoice_sudo = request.env['account.move'].sudo().search([('id', '=', invoice_id)])

        return {
            'saleOrderInfo': {
                'order_id': sale_invoice_sudo.id,
                'order_name': sale_invoice_sudo.name,
                'order_currency': sale_invoice_sudo.currency_id.name,
                'order_amount': sale_invoice_sudo.amount_total,
                'order_customer_name': sale_invoice_sudo.partner_id.name,
                'order_customer_email': sale_invoice_sudo.partner_id.email
            },
        }

    @http.route('/payment/pixelpay/get_customer_info', type='json', auth='public')
    def pixel_get_customer_info(self, partner_id):
        partner_sudo = request.env['res.partner'].sudo().search([('id', '=', partner_id)])

        if not partner_sudo.name:
            raise ValidationError(
                _("The username does not appear to be correct. Set username in the billing address"))

        if not partner_sudo.street:
            raise ValidationError(
                _("The billing address does not appear to be correct. Set an address in the billing address"))

        if not partner_sudo.city:
            raise ValidationError(
                _("The city does not appear to be correct. Set an city in the billing address"))

        if not partner_sudo.state_id.code_3166_2:
            raise ValidationError(
                _("The country code does not seem to be correct. Set the country in the billing address"))

        # if not partner_sudo.country_id.code:
        #     raise ValidationError(
        #         _("The country code does not seem to be correct. Set the country in the billing address"))
        #
        # if not partner_sudo.state_id.code:
        #     raise ValidationError(
        #         _("The state code does not seem to be correct. Set the state in the billing address"))

        if partner_sudo.phone or partner_sudo.mobile:
            phone = partner_sudo.phone if partner_sudo.phone else partner_sudo.mobile
        else:
            raise ValidationError(
                _("The phone does not appear to be correct. Set an phone in the billing address"))

        if not partner_sudo.email:
            raise ValidationError(
                _("The email does not appear to be correct. Set an email in the billing address"))

        return {
            'partnerInfo': {
                "partner": partner_sudo.name,
                "billing_address": partner_sudo.street,
                "billing_city": partner_sudo.city,
                "billing_country": partner_sudo.country_id.code,
                "billing_state": partner_sudo.state_id.code_3166_2,
                "billing_phone": phone,
                "billing_zip": partner_sudo.zip if partner_sudo.zip else '',
                "email": partner_sudo.email,
            }
        }

    @http.route('/payment/pixel/create_token', type='json', auth='public')
    def pixel_create_token(self, acquirer_id, partner_id, pixel_token, mask, network):
        acquirer_sudo = request.env['payment.acquirer'].sudo().browse(acquirer_id).exists()

        # todo Verify that all configuration-specific required parameters are provided.

        # Create the token and return its id
        token_sudo = acquirer_sudo._pixel_create_token(partner_id, pixel_token, mask, network)
        return token_sudo.id

    @http.route('/payment/pixel/payment', type='json', auth='public')
    def authorize_payment(self, data):
        request.env['payment.transaction'].sudo()._handle_feedback_data('pixel', data)

    @http.route('/payment/pixel/get_token', type='json', auth='public')
    def get_payment(self, tokenId):
        token_id = request.env['payment.token'].sudo().search([('id', '=', tokenId)])

        return {
            'pixelToken': token_id.acquirer_ref,
            'acquirer_id': token_id.acquirer_id.id
        }

