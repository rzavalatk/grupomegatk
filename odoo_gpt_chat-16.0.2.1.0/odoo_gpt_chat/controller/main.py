
from odoo import http
from odoo.http import request
import requests
import json

class KitchenScreenBase(http.Controller):

    @http.route('/get/chatbot', type="json", auth="public")
    def _get_chatbot(self):
        whis_settings = request.env['ir.config_parameter'].sudo()
        if whis_settings.get_param('odoo_gpt_chat.chat_bot_id', False) and whis_settings.get_param('odoo_gpt_chat.show_chat_bot', False):
            return {
                'id': whis_settings.get_param('odoo_gpt_chat.chat_bot_id', False), 
                'front_end': whis_settings.get_param('odoo_gpt_chat.show_chat_bot_f', False), 
                'back_end': whis_settings.get_param('odoo_gpt_chat.show_chat_bot_b', False) 
            }
        else:
            return False
        
    @http.route('/get/login/user', type='json', auth='public', cors="*")
    def get_login_user(self):
        origin = ''
        if 'HTTP_REFERER' in request.httprequest.headers.environ.keys():
            origin = request.httprequest.headers.environ['HTTP_REFERER']
        
        return {
            'origin': origin,
            'userid': request.env.user.id,
            'name': request.env.user.name,
            'email': request.env.user.email,
            'phone': request.env.user.phone,
        }

    @http.route('/create/chatbot/lead', type="json", auth="public", cors="*")
    def _create_lead(self):
        whis_user = request.env.ref('odoo_gpt_chat.whisperchat_user_bits')
        country_id = False
        res_data = request.get_json_data()
        if res_data.get('ip'):
            res = requests.request("GET", f"https://geolocation-db.com/json/{res_data.get('ip')}&position=true")
            data = json.loads(res.text)
            country_id = request.env['res.country'].search([('code','=',data.get("country_code", ""))], limit=1).id
        lead = request.env['crm.lead'].with_user(whis_user.id).create({
            'name': res_data.get('name', ''),
            'contact_name': res_data.get('name', ''),
            'email_from': res_data.get('email', ''),
            'phone': res_data.get('phone', ''),
            'type': 'lead',
            'country_id':country_id,
            'session_token':res_data.get('session_token', ''),
        })
        chats = requests.get('https://api.whisperchat.ai/return/chat/session', json={'session_id': lead.session_token})
        chats = json.loads(chats.text).get('result', [])
        message = ""
        for chat in chats:
            message += f"<p>Q: {chat.get('qns', '')}</p>\n"
            message += f"<p>A: {chat.get('ans', '')}</p><br/>\n"
        # lead = lead.with_user(whis_user.id)
        lead.message_post(body=message,author_id=whis_user.partner_id.id,email_from = 'hello@whisperchat.ai')
        return True
