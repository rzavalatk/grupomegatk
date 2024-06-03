# -*- coding: utf-8 -*-

from odoo import models, fields, api


class WhatsappSendMessage(models.TransientModel):
    _name = 'whatsapp.message.wizard'

    partner_id = fields.Many2one('res.partner', string="Cliente")
    mobile = fields.Char(required=True, string="Numero de contacto")
    message = fields.Text(string="Mensaje", required=True)
    image_1920 = fields.Binary(readonly=1)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Función para obtener el número de móvil y la imagen del socio en odoo"""
        self.mobile = self.partner_id.mobile
        self.image_1920 = self.partner_id.image_1920

    def send_message(self):
        
        if self.message and self.mobile:
            message_string = ''
            message = self.message.split(' ')
            for msg in message:
                message_string = message_string + msg + '%20'
            message_string = message_string[:(len(message_string) - 3)]
            message_post_content = message_string
            if self.partner_id:
                self.partner_id.message_post(body=message_post_content)
            return {
                'type': 'ir.actions.act_url',
                'url': "https://api.whatsapp.com/send?phone=" + self.mobile + "&text=" + message_string,
                'target': 'new',
                'res_id': self.id,
            }
