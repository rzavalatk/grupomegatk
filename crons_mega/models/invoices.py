# -*- coding: utf-8 -*-
from odoo import models, api, fields
# from datetime import datetime
from datetime import datetime, timedelta
import pytz
import time
import json


class Factura(models.Model):
    _inherit = "account.invoice"

    expire_id = fields.Many2one("account.invoice.expire")
    expire_line_id = fields.Many2one("invoice.expire.line")
    state_expired = fields.Selection([
        ("none", "No Vencida"),
        ("1er Aviso", "1er Aviso"),
        ("2do Aviso", "2do Aviso")
    ],default="none",string="Estado Aviso")


class FacturasAVencer(models.Model):
    _name = "account.invoice.expire"
    _order = "create_date desc"
    
    @api.one
    def _name_(self):
        self.name = self.company_id.name + \
            " - " + self.date.strftime("%d/%m/%Y")
    
    
    name = fields.Char(compute=_name_)
    date = fields.Date("Fecha")
    company_id = fields.Many2one(
        "res.company", "Compañia", default=lambda self: self.env.user.company_id.id)
    invoice_expire_line = fields.One2many("invoice.expire.line", "invoice_expire_id", "Facturas")
    facturas_ids = fields.One2many("account.invoice", "expire_id", "Facturas")
    state = fields.Selection([
        ("draft", "Borrador"),
        ("init", "Iniciado"),
        ("proccess", "Proceso"),
        ("done", "Hecho"),
        ("cancel", "Cancelado")
    ], string="Estado", default="draft")
    
    def volver_borrador(self):
        self.write({
            'state': 'draft'
        })
    
    def cancel(self):
        facturas = []
        lines = []
        for item in self.invoice_expire_line:
            lines.append((3, item.sudo().id))
        for item in self.facturas_ids:
            facturas.append((3, item.sudo().id))
        for item in self.facturas_ids:
             item.write({
                    'state_expired': 'none'
                })
        self.write({
            'facturas_ids': facturas,
            'invoice_expire_line': lines,
            'state': 'cancel'
        })
    
    
    def init_review(self):
        dias_7 = self.date + timedelta(days=-7)
        dias_14 = self.date + timedelta(days=-14)
        filtros = [
            '&',
            '&',
            '&',
            '&',
            ('company_id', '=', self.company_id.sudo().id),
            ('type', '=', 'out_invoice'),
            ('state', '=', 'open'),
            ('state_expired', 'in', ['none','first']),
            ('date_due','in',[dias_7.strftime("%Y-%m-%d"),dias_14.strftime("%Y-%m-%d")]),
        ]
        facturas_ids = self.env['account.invoice'].sudo().search(filtros)
        for factura in facturas_ids:
            if factura.date_due.strftime("%Y-%m-%d") == dias_7.strftime("%Y-%m-%d"):
                factura.sudo().write({
                    'state_expired': '1er Aviso'
                })
            if factura.date_due.strftime("%Y-%m-%d") == dias_14.strftime("%Y-%m-%d"):
                factura.sudo().write({
                    'state_expired': '2do Aviso'
                })
            self.write({
                'facturas_ids': [(4, factura.id)]
            })
        self.write({
                'state': 'init'
            })
        
    def _exist_id(self,id,list):
        for item in list:
            if item[2]['user_id'] == id:
                return True
        return False
                        
        
    
    def procesar_facturas(self):
        vals = []
        for factura in self.facturas_ids:
            if len(vals) == 0:
                vals.append((0,0,{
                    'user_id': factura.user_id.id,
                    'facturas_ids': [(6,0,[factura.id])]
                }))
            else:
                if self._exist_id(factura.user_id.id, vals):
                    for item in vals:
                        if item[2]['user_id'] == factura.user_id.id:
                            item[2]['facturas_ids'][0][2].append(factura.id)
                else:
                    vals.append((0,0,{
                        'user_id': factura.user_id.id,
                        'facturas_ids': [(6,0,[factura.id])]
                    }))
        self.write({
            'invoice_expire_line': vals,
            'state': 'proccess'
        })
        
    
    def enviar_facturas_vencidas(self):
        for user in self.invoice_expire_line:
            user.send_email()
            time.sleep(1)
        self.write({
            'state': 'done'
        })  
             
            
            
            
    def cron_eject(self):
        admin = self.env['res.users'].sudo().browse(2)
        user_tz = pytz.timezone(self.env.context.get('tz') or admin.tz)
        today = datetime.now(user_tz)
        if today.weekday() != 6:
            company_ids = [8, 9, 12]
            ids = []
            for i in company_ids:
                obj = self.create({
                    'date': today,
                    'company_id': i,
                })
                ids.append(obj.id)
            for i in ids:
                vencidas = self.sudo().browse(i)
                vencidas.init_review()
                time.sleep(1)
                vencidas.procesar_facturas()
                time.sleep(1)
                vencidas.enviar_facturas_vencidas()
        
    
    
class FacturaVencerLine(models.Model):
    _name = "invoice.expire.line"
    _order = "create_date desc"
    
    
    user_id = fields.Many2one("res.users",string="Comercial")
    invoice_expire_id = fields.Many2one("account.invoice.expire")
    facturas_ids = fields.One2many("account.invoice", "expire_line_id", "Facturas")
    
    def send_email(self):
        template = self.env.ref(
            'crons_mega.email_template_account_invoice_expire')
        email_values = {
            'email_from': 'megatk.no_reply@megatk.com',
            'email_to': self.user_id.login,
        }
        template.send_mail(self.id, email_values=email_values, force_send=True)
        return True

    