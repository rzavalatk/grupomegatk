# -*- coding: utf-8 -*-

import logging

from odoo import fields, api, models, _
import pycountry
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AcquirerPixel(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(selection_add=[("pixel", "PixelPay")], ondelete={'pixel': 'set default'})
    pixel_endpoint = fields.Char('Endpoint', groups='base.group_user', help="htttp://example.com")
    pixel_key = fields.Char('Key ID', groups='base.group_user', help="Enter your company's API key.")
    pixel_secret_key = fields.Char('Secret Key', groups='base.group_user', help="Enter the value of the secret key converted to an MD5 hash.")
    pixel_payment_method_type = fields.Selection(
        string="Allow Payments From",
        help="Determines with what payment method the customer can pay.",
        selection=[('credit_card', "Credit Card")],
        default='credit_card',
        required_if_provider='pixel',
    )

    def _pixel_create_token(self, partner_id, pixel_token, mask, network):
        try:
            payment_token = self.env['payment.token'].sudo().create({
                'acquirer_id': self.id,
                'partner_id': partner_id,
                'name': mask,
                'network': network,
                'acquirer_ref': pixel_token
            })
            return payment_token
        except:
            return {'error': True, 'message': 'Could not store token'}

    def get_country_provinces(self):
        # self.country_ids.search([('state_ids', '=', False), ('state_required', '=', False)])
        try:
            if self.country_ids:
                for ct in self.country_ids:
                    if not ct.state_ids:
                        state_ids = pycountry.subdivisions.get(country_code=ct.code)
                        if state_ids:
                            for si in state_ids:
                                print(si)
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
                                            print(si)
                                            vals = {
                                                'code_3166_2': si.code
                                            }
                                            ct.update({'state_ids': [(1, state.id, vals)]})
                            ct.state_required = True
                message = _("Get Provinces Successful!")

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': message,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                message = _("Select a country in the module settings!")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': message,
                        'type': 'warning',
                        'sticky': False,
                    }
                }
        except:
            raise ValidationError("Verify that you have selected a country")





class PixelPaymentToken(models.Model):
    _inherit = "payment.token"

    network = fields.Char(string='Network')


