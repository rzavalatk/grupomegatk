# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
import pytz

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def notify_due_invoices(self):
        admin = self.env['res.users'].sudo().browse(2)
        user_tz = pytz.timezone(self.env.context.get('tz') or admin.tz)
        today = datetime.now(user_tz)
        due_date = today + timedelta(days=5)
        invoices = self.search([('invoice_date_due', '=', due_date), ('state', '=', 'posted')])
        mail_template = self.env.ref('crons_mega.mail_template_notification_invoice_due')

        for invoice in invoices:
            if invoice.invoice_user_id:
                mail_template.sudo().send_mail(invoice.id, force_send=True)
                if invoice.partner_id.email:
                    mail_template.sudo().send_mail(invoice.id, email_values={'email_to': invoice.partner_id.email}, force_send=True)
