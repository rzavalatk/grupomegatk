# -*- coding: utf-8 -*-

import logging
from odoo import fields, api, models, _
import pycountry
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentProviderPixel(models.Model):
    _inherit = "payment.provider"

    # Definición correcta del provider
    code = fields.Selection(
        selection_add=[('pixel', 'PixelPay')],
        ondelete={'pixel': 'set default'}
    )
    
    pixel_endpoint = fields.Char('Endpoint', groups='base.group_user', help="http://example.com")
    pixel_key = fields.Char('Key ID', groups='base.group_user', help="Enter your company's API key.")
    pixel_secret_key = fields.Char('Secret Key', groups='base.group_user', 
                                 help="Enter the value of the secret key converted to an MD5 hash.")
    pixel_payment_method_type = fields.Selection(
        string="Allow Payments From",
        help="Determines with what payment method the customer can pay.",
        selection=[('credit_card', "Credit Card")],
        default='credit_card',
        required_if_provider='pixel',
    )

    def _pixel_create_token(self, partner_id, pixel_token, mask, network):
        """Método para crear tokens de pago - Adaptado a Odoo 16"""
        try:
            payment_token = self.env['payment.token'].sudo().create({
                'provider_id': self.id,  # Cambiado de acquirer_id a provider_id
                'partner_id': partner_id,
                'name': mask,
                'payment_details': network,  # Cambiado de network a payment_details
                'provider_ref': pixel_token  # Cambiado de acquirer_ref a provider_ref
            })
            return payment_token
        except Exception as e:
            _logger.error("Error creating payment token: %s", str(e))
            return {'error': True, 'message': 'Could not store token'}

    def get_country_provinces(self):
        """Método para obtener provincias - Se mantiene igual"""
        try:
            if self.country_ids:
                for ct in self.country_ids:
                    if not ct.state_ids:
                        state_ids = pycountry.subdivisions.get(country_code=ct.code)
                        if state_ids:
                            for si in state_ids:
                                vals = {
                                    'country_id': ct.id,
                                    'name': si.name,
                                    'code': si.code[(si.code.find("-")+1):],
                                    'code_3166_2': si.code
                                }
                                ct.write({'state_ids': [(0, 0, vals)]})
                        ct.state_required = True
                    else:
                        state_ids = pycountry.subdivisions.get(country_code=ct.code)
                        if state_ids:
                            for state in ct.state_ids:
                                if not state.code_3166_2:
                                    for si in state_ids:
                                        if si.code[(si.code.find("-") + 1):] == state.code:
                                            vals = {
                                                'code_3166_2': si.code
                                            }
                                            ct.update({'state_ids': [(1, state.id, vals)]})
                            ct.state_required = True
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _("Get Provinces Successful!"),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _("Select a country in the module settings!"),
                        'type': 'warning',
                        'sticky': False,
                    }
                }
        except Exception as e:
            _logger.error("Error getting provinces: %s", str(e))
            raise ValidationError(_("Verify that you have selected a country"))

class PaymentTokenPixel(models.Model):
    _inherit = "payment.token"

    # Campo adaptado a la nueva estructura
    payment_details = fields.Char(string='Payment Network')