# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
import pytz

import logging
import math


_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    #ESTE METODO SE UTILIZA PARA MANDAR CORREO 5 DIAS ANTES DE VENCER UNA FACTURA
    @api.model
    def notify_due_invoices(self):
        admin = self.env['res.users'].sudo().browse(2)
        user_tz = pytz.timezone(self.env.context.get('tz') or admin.tz)
        today = datetime.now(user_tz)
        due_date = today + timedelta(days=5)
        invoices = self.search([('invoice_date_due', '=', due_date), ('state', '=', 'posted')])
        mail_template = self.env.ref('crons_mega.mail_template_notification_invoice_dues')
        
        
        for invoice in invoices:
            
            if invoice.invoice_user_id:
                if invoice.partner_id.email:
                    if invoice.company_id.id == 8:
                            
                        email_values = {
                            'email_from': 'megatk.no_reply@megatk.com',
                            'email_to': invoice.partner_id.email,
                            'email_cc': invoice.invoice_user_id.login
                        }
                        mail_template.sudo().send_mail(invoice.id, email_values=email_values, force_send=True)
                            
                    elif invoice.company_id.id == 9:
                        
                        email_values = {
                            'email_from': 'meditek.no_reply@megatk.com',
                            'email_to': invoice.partner_id.email,
                            'email_cc': invoice.invoice_user_id.login
                        }
                        mail_template.sudo().send_mail(invoice.id, email_values=email_values, force_send=True)
    
    #ESTE METODO SE UTILIZA PARA MANDAR CORREO CUANDO YA SE VENCIO LA FACTURA
    @api.model
    def notify_date_due_invoices(self):
        admin = self.env['res.users'].sudo().browse(2)
        user_tz = pytz.timezone(self.env.context.get('tz') or admin.tz)
        today = datetime.now(user_tz)
        invoices = self.search([('invoice_date_due', '<', today), ('company_id', 'in', [8,9]), ('state', '=', 'posted'), ('move_type', '=', 'out_invoice'), ('payment_state', 'in', ['not_paid', 'partial'])])
        mail_template = self.env.ref('crons_mega.mail_template_notification_invoice_date_dues')
        
        
        for invoice in invoices:
            
            if invoice.invoice_payment_term_id.id not in [111,126]:
                
                #_logger.warning("#1 " + invoice.name )
                
                if invoice.invoice_user_id:
                    if invoice.partner_id.email:
                        
                        if invoice.company_id.id == 8:
                            
                            email_values = {
                                'email_from': 'megatk.no_reply@megatk.com',
                                #'email_to': invoice.partner_id.email,
                                #'email_cc': invoice.invoice_user_id.login
                                'email_to': 'dvasquez@megatk.com',
                                'email_cc': 'dzuniga@megatk.com'
                            }
                            mail_template.sudo().send_mail(invoice.id, email_values=email_values, force_send=True)
                           
                            
                        elif invoice.company_id.id == 9:
                            
                            email_values = {
                                'email_from': 'meditek.no_reply@megatk.com',
                                #'email_to': invoice.partner_id.email,
                                #'email_cc': invoice.invoice_user_id.login
                                'email_to': 'dvasquez@megatk.com',
                                'email_cc': 'dzuniga@megatk.com'
                            }
                            mail_template.sudo().send_mail(invoice.id, email_values=email_values, force_send=True)
                    
                    
                    
