# -*- coding: utf-8 -*-


import urllib.parse as urllib

from odoo import models, fields, api


class PortalShare(models.TransientModel):
    _inherit = 'portal.share'

    share_type = fields.Selection([
        ('mail', 'Mail'),
        ('whatsapp', 'Whatsapp')], string="Sharing Method", default="mail")
    mobile_number = fields.Char()
    partner_id = fields.Many2one('res.partner', string='Customer')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.mobile_number = self.partner_id.mobile

    def action_send_whatsapp(self):
        """"""
        """En esta función estamos redirigiendo a la web de whatsapp
                con los parámetros requeridos"""
        if self.note and self.mobile_number:
            if self.res_model == 'sale.order':
                common_message = 'Ha sido invitado a acceder a la siguiente Orden de venta.'
            elif self.res_model == 'account.move':
                common_message = 'Se le ha invitado a acceder a la siguiente factura.'
            elif self.res_model == 'purchase.order':
                common_message = 'Se le ha invitado a acceder a la siguiente Compra.'
            else:
                common_message = 'Se le ha invitado a acceder al siguiente documento.'
            message_string = self.note + '%0a' + common_message + '%0a' + urllib.quote(self.share_link)
            related_record = self.env[self.res_model].search([('id', '=', int(self.res_id))])
            related_record.message_post(body=message_string)
            return {
                'type': 'ir.actions.act_url',
                'url': "https://api.whatsapp.com/send?phone=" + self.mobile_number + "&text=" + message_string,
                'target': 'new',
                'res_id': self.id,
            }



