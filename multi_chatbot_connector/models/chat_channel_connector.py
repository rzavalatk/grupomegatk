# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models, _
import datetime
import dateutil.relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError
import bs4
from bs4 import BeautifulSoup
import unicodedata
import random


class ResCompany_Bot(models.Model):
    _inherit = 'res.company'

    chain_of_bots = fields.One2many(
        'chain.bots', 'company_id', string='Chain of bots')

    def _chain_response(self, msg):
        return False


class ChainOfBots(models.Model):
    _name = 'chain.bots'
    _order = 'sequence'

    company_id = fields.Many2one('res.company', string="Company",
                                 readonly=True, default=lambda self: self.env.user.company_id)
    sequence = fields.Integer(string='Sequence', required=True)
    chatbot = fields.Many2one('chat.bots', string="Chatbot")

    _sql_constraints = [
        ('chatbot_unique', 'UNIQUE(chatbot)',
         'Record is already used, please choose a unique one'),
        ('sequence_unique', 'UNIQUE(sequence)',
         'Record is already used, please choose a unique one')
    ]


class ImLivechatMultiChannel(models.Model):
    _inherit = 'im_livechat.channel'

    def get_currnet_user_compnay_id(self):
        current_user = self.env['res.users'].sudo().search(
            [('id', '=', self._context.get('uid') or self._uid or self.env.user.id)], limit=1)
        if current_user:
            return current_user.company_id.id

    multi_chatbot = fields.Boolean(string="Multi Chatbot")
    company_id = fields.Many2one(
        'res.company', string='Company', default=get_currnet_user_compnay_id)
    bot_default_reply = fields.Char(
        string='Default Reply', help="When bot not understand Question")
    mailing_list_id = fields.Many2one('mail.mass_mailing.list', 'Mailing List')
    issue_category = fields.Many2one(
        'online.help.category', 'Support Category')
    timer = fields.Char('Waiting Timer')

    _sql_constraints = [
        ('issue_category_unique', 'UNIQUE(issue_category , company_id)',
         'A Category must be unique!'),
    ]

    @api.onchange('multi_chatbot')
    def multi_chatbot_onchange(self):
        self.bot_default_reply = False
        self.issue_category = False
        self.timer = False

    @api.multi
    def action_operators_user(self):
        view_id = self.env.ref(
            'multi_chatbot_connector.wizard_view_operators_user').sudo().id
        action_ctx = dict(self._context)
        action_ctx.update({'active_id': self.id, 'active_ids': [self.id],
                           'active_model': 'im_livechat.channel'})
        if self.issue_category:
            new = self.env['operators.user'].sudo().create({})
            user_id = self.env['res.users'].sudo().search(
                [('issue_category', '=', self.issue_category.id), ('company_ids', 'in', self.company_id.id)])
            for user in user_id:
                self.env['operators.user.line'].sudo().create({'operators_id': new.sudo().id,
                                                               'user_id': user.id,
                                                               'login': user.login,
                                                               'language': user.lang})
            return {
                'name': _('Operation User'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'operators.user',
                'views': [(view_id, 'form')],
                'view_id': view_id,
                'target': 'new',
                'res_id': new.sudo().id,
                'context': action_ctx}
        else:
            raise ValidationError(_('Please Select Channel Category!'))

    @api.multi
    def get_mail_channel_by_id(self, mail_channel_id, mail_id):
        mail_channel = self.env['mail.channel'].sudo().search(
            [('id', '=', mail_channel_id)])
        users = self.sudo().browse(mail_id).get_available_users()
        if len(users) == 0:
            return False
        user = random.choice(users)
        operator_partner_id = user.partner_id.id
        vals = mail_channel.sudo().with_context(
            im_livechat_operator_partner_id=operator_partner_id).channel_info()[0]
        return vals


class OnlineHelpdesk(models.Model):
    _name = 'online.helpdesk'
    _order = 'create_date desc'

    status = fields.Selection(
        [('new', 'New'), ('working', 'In Progress'), ('finish', 'Finish')], default='new')
    name = fields.Char('Name')
    email = fields.Char('E-mail')
    note = fields.Text('Note')
    user_id = fields.Many2one('res.users', 'User')
    issue_category = fields.Many2one(
        'online.help.category', 'Support Category')
    maill_channel_id = fields.Many2one('mail.channel', 'Channel')
    rating = fields.Selection([('0', 'No Feedback'), ('1', 'Fair'), (
        '5', 'Very Good'), ('10', 'Excellent')], "Rating Score", default=0)
    company_id = fields.Many2one('res.company', string='Company')
    previous_reply = fields.Char(string="Previous Reply")

    @api.multi
    def unlink(self):
        for helpdesk in self:
            if helpdesk.status not in ('draft'):
                raise UserError(
                    _('You can not delete a Helpdesk Lead History!'))
        return super(OnlineHelpdesk, self).unlink()

    @api.multi
    def online_helpdesk_process(self, cron_mode=True):
        CurrentDate = datetime.datetime.now()
        for helpdesk in self.env['online.helpdesk'].sudo().search([('status', '=', 'new')]):
            if self.env['mail.channel'].sudo().search([('helpdesk_lead_id', '=', helpdesk.id), ('create_date', '<', CurrentDate.strftime(DEFAULT_SERVER_DATE_FORMAT))]):
                helpdesk.status = 'finish'

    @api.multi
    def send_by_chat_history_mail(self):
        Template = self.env.ref(
            'multi_chatbot_connector.chat_feedback_history_template', False)
        html = "Hello, \n Here's a copy of the chat transcript you Requested: <br/><br/> \n\n"
        for message in reversed(self.maill_channel_id.message_ids):
            data = unicodedata.normalize('NFKD', message.body)
            cleantext = BeautifulSoup(str(data), "lxml").text
            if message.author_id:
                html += "<strong>" + \
                    str(message.author_id.name) + \
                    '</strong> : ' + str(cleantext) + '<br/>'
            else:
                html += 'Me : ' + str(cleantext) + '<br/>'
        html += "<br/><br/> \n\n Best Regard!"
        Template.update({'body_html': html})
        Template.send_mail(self.maill_channel_id.id, force_send=True)
        return True

    @api.multi
    def action_schedule_meeting(self):
        xml_id = 'im_livechat.mail_channel_view_tree'
        tree_view_id = self.env.ref(xml_id).id
        xml_id = 'im_livechat.mail_channel_view_form'
        form_view_id = self.env.ref(xml_id).id
        return {
            'name': _('Mail Channel'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'res_model': 'mail.channel',
            'domain': [('helpdesk_lead_id', 'in', self.ids)],
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def action_talk_to_client(self):
        mail_channel = self.env['mail.channel'].sudo().search(
            [('helpdesk_lead_id', '=', self.id)], limit=1)
        self.sudo().write({'status': 'working'})
        c_user = self._context.get('uid') or self._uid or self.env.user.id
        c_partner = self.env['res.users'].sudo().search(
            [('id', '=', c_user)], limit=1)
        c_partner.sudo().write({'is_busy': True})
        return {
            'type': 'ir.actions.act_url',
            'url': '/im_livechat/support/%s?help_id=%s' % (self.maill_channel_id.livechat_channel_id.id, mail_channel.id if mail_channel else False),
            'target': 'new',
            'target_type': 'public',
        }


class MailChannelMulti(models.Model):
    _inherit = 'mail.channel'

    helpdesk_lead_id = fields.Many2one('online.helpdesk', 'Online Helpdesk')

    def chat_order_desc(self):
        send = ""
        for chat in reversed(self.message_ids):
            name = ""
            if chat.author_id:
                name = '<span>'+chat.author_id.name+'</span> :'
            else:
                name = 'You :'
            text_body = bs4.BeautifulSoup(chat.body, "html").text
            send += "<p>"+name + "<span>"+text_body+"</span></p>"
        return send


class OnlineHelpCategory(models.Model):
    _name = 'online.help.category'

    name = fields.Char('Name')


class ResUsersMulti(models.Model):
    _inherit = 'res.users'

    issue_category = fields.Many2one(
        'online.help.category', 'Support Category')
    is_busy = fields.Boolean('Busy')


class ResConfigSettingsInheritMulti(models.TransientModel):
    _inherit = 'res.config.settings'

    is_chain_of_bot = fields.Boolean(string='is Chain of Bot')

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInheritMulti, self).get_values()
        ConfigOBJ = self.env['ir.config_parameter'].sudo()
        is_chain_of_bot = ConfigOBJ.get_param(
            'multi_chatbot_connector.is_chain_of_bot')
        res.update(
            is_chain_of_bot=is_chain_of_bot,
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].set_param(
            'multi_chatbot_connector.is_chain_of_bot', self.is_chain_of_bot)
        super(ResConfigSettingsInheritMulti, self).set_values()
