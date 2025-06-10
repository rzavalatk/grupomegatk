from odoo import models, fields, api, _
import requests
import json

class crm_lead(models.Model):
    _inherit = 'crm.lead'

    session_token = fields.Char(string='Session Token')

    def action_fetch_whis_chat(self):
        whis_user = self.env.ref('odoo_gpt_chat.whisperchat_user_bits')
        for record in self:
            if record.session_token:
                chats = requests.get('https://api.whisperchat.ai/return/chat/session', json={'session_id': record.session_token})
                chats = json.loads(chats.text).get('result', [])
                message = ""
                for chat in chats:
                    message += f"<p>Q: {chat.get('qns', '')}</p>\n"
                    message += f"<p>A: {chat.get('ans', '')}</p><br/>\n"
                # lead = lead.with_user(whis_user.id)
                record.message_post(body=message, author_id=whis_user.partner_id.id, email_from = 'hello@whisperchat.ai')
