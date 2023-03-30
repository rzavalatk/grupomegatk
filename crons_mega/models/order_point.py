# -*- coding: utf-8 -*-

from odoo import models, api, fields
from datetime import datetime as dt
import pytz
import time


class ReviewRules(models.Model):
    _name = "orderpoint.review.rules"
    _order = "create_date desc"
    
    @api.one
    def _name_(self):
        self.name = self.company_id.name + \
            " - " + self.date.strftime("%d/%m/%Y")
    
    
    @api.one
    def _send(self):
        self.send = len(self.warehouse_ids.ids) > 0
    
    
    name = fields.Char(compute=_name_)
    date = fields.Date("Fecha",default=dt.today().date())
    send = fields.Boolean(compute=_send)
    warehouse_ids = fields.Many2many("stock.warehouse.orderpoint","review_id",string="Reglas")
    company_id = fields.Many2one("res.company","Compañia",default=lambda self: self.env.user.company_id.id)
    state = fields.Selection([
        ("draft", "Borrador"),
        ("init", "Iniciado"),
        ("done", "Hecho"),
        ("cancel", "Cancelado")
    ], string="Estado", default="draft")
    
    def back_to_draft(self):
        self.write({
            'state': 'draft'
        })
    
    
    def cancel_review(self):
        self.write({
            'warehouse_ids': [(6,0,[])],
            'state': 'cancel'
        })
    
    
    def init_review(self):
        ids = self.warehouse_ids.search_quantity_minimal()
        self.write({
            'warehouse_ids': [(6,0,ids)],
            'state': 'init'
        })
    
    
    def send_email(self, email, cc=""):
        template = self.env.ref(
            'crons_mega.email_template_orderpoint_review_rules')
        email_values = {
            'email_from': 'megatk.no_reply@megatk.com',
            'email_to': email,
            'email_cc': cc
        }
        template.send_mail(self.id, email_values=email_values, force_send=True)
        self.write({
            'state': 'done'
        })
        return True

    
    def cron_eject(self):
        if len(self.warehouse_ids.ids) > 0:
            admin = self.env['res.users'].sudo().browse(2)
            user_tz = pytz.timezone(self.env.context.get('tz') or admin.tz)
            _today = dt.now(user_tz)
            if _today.weekday() != 0:
                company_ids = [8, 9]
                ids = []
                for i in company_ids:
                    id = self.create({
                        'date': _today,
                        'company_id': i
                    })
                    ids.append(id.id)
                review = self.env['orderpoint.review.rules'].sudo().browse(ids)
                for item in review:
                    principal_emails = "lmoran@megatk.com,bodegatgu@megatk.com"
                    cc = ""
                    item.init_review()
                    time.sleep(1)
                    if item.send:
                        if i == 9:
                            cc += "jmoran@meditekhn.com,"
                        item.send_email(principal_emails,cc)
                        time.sleep(1)
    

class Warehouse(models.Model):
    _inherit = "stock.warehouse.orderpoint"
    
    review_id = fields.Many2one("orderpoint.review.rules")
    

    def search_quantity_minimal(self):
        ids = []
        for rule in self.search([]):
            if rule.product_id.qty_available <= rule.product_min_qty:
                ids.append(rule.id)
        return ids