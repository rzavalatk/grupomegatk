# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import datetime
import pytz
import time
import json


class CXC(models.Model):
    _name = "account.cierre.cxc"
    _order = "create_date desc"
    _description = "description"
    
    def _name_(self):
        for record in self:
            company_name = record.company_id.name or ''
            create_date = record.create_date
            formatted_date = create_date.strftime('%Y-%m-%d')
            record.name = f'{company_name} - {formatted_date}'        
    

    name = fields.Char(compute=_name_)
    cierre_cxc_line_ids = fields.One2many(
        "account.cierre.cxc.line", "cierre_cxc_id", string="Lineas de Cierre CXC")
    moves_ids = fields.One2many(
        "account.move.line", "cierre_cxc_id", string="Lineas de Movimientos")
    company_id = fields.Many2one(
        "res.company", "Compañia", default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    total = fields.Monetary("Total")
    date = fields.Date("Fecha")
    logs = fields.Text("Registros", default="")
    state = fields.Selection([
        ("draft", "Borrador"),
        ("init", "Iniciado"),
        ("add_move", "Obtener Movimientos"),
        ("proccess", "Proceso"),
        ("done", "Hecho"),
        ("cancel", "Cancelado")
    ], string="Estado", default="draft")
    
    def come_back_draft(self):
        self.write({
            'state': 'draft'
        })
    
    def cancel(self):
        lines_ids = []
        move = []
        for item in self.cierre_cxc_line_ids:
            lines_ids.append((2, item.sudo().id))
        for item in self.moves_ids:
            move.append((3, item.sudo().id))

        self.write({
            'cierre_cxc_line_ids': lines_ids,
            'moves_ids': move,
            'state': 'cancel'
        })
        
    def init_cierre_cxc(self):
        account_ids_setting = self.env["res.config.settings"].get_values_account_ids_cron_mega(self.company_id)
        account_ids = self.env["account.account"].browse(account_ids_setting)
        for item in account_ids:
            self.write({
                'cierre_cxc_line_ids': [(0,0,{
                    'account_id': item.id
                })],
                'state': 'init'
            })
            
    def add_move(self):
        account_ids_setting = self.env["res.config.settings"].get_values_account_ids_cron_mega(self.company_id)
        moves_ids = self.env["account.move.line"].sudo().search(['&',
            ('date','=',self.date),
            ('company_id','=',self.company_id.id),
            ('account_id','in',account_ids_setting),
            ])
        for item in moves_ids:
            item.write({
                'cierre_cxc_id': self.id
            })
        self.write({
            'state': 'add_move'
        })
             
    def proccess_cierre(self):
        for move in self.moves_ids:
            for line in self.cierre_cxc_line_ids:
                debit = line.debe
                credit = line.haber
                if move.account_id.id == line.account_id.id:
                    debit += move.debit
                    credit += move.credit
                line.write({
                    'debe': debit,
                    'haber': credit,
                })
        self.write({
            'state': 'proccess'
        })
        
    def send_email(self,mail,cc):
        template = self.env.ref(
            'crons_mega.email_template_cierre_diario_cxc')
        email_values = {
            'email_from': 'megatk.no_reply@megatk.com',
            'email_to': mail,
            'email_cc': cc
        }
        template.send_mail(self.id, email_values=email_values, force_send=True)
        self.write({
            'state': 'done'
        })
        return True
    
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
                cierre = self.sudo().browse(i)
                cierre.init_cierre_cxc()
                time.sleep(1)
                cierre.add_move()
                time.sleep(1)
                cierre.proccess_cierre()
                # cierre.send_email("azelaya@megatk.com","ecolindres@megatk.com")
                if cierre.company_id.sudo().id in [8, 12]:
                    time.sleep(1)
                    cierre.send_email(
                        "lmoran@megatk.com,jmoran@meditekhn.com,dvasquez@megatk.com", "eduron@megatk.com")
                if cierre.company_id.sudo().id in [9]:
                    time.sleep(1)
                    cierre.send_email(
                        "lmoran@megatk.com,jmoran@meditekhn.com,dvasquez@megatk.com", "nfuentes@meditekhn.com")
                time.sleep(1)
                     
    def go_to_view_tree(self):
        return {
            'name': 'Cierre Diario CXC',
            'type': 'ir.actions.act_window',
            'res_model': 'account.cierre.cxc',
            'view_type': 'form',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'target': 'current',
            'domain': [('company_id', '=', self.env.user.company_id.id)],
        }
    
class CXCLine(models.Model):
    _name = "account.cierre.cxc.line"
    _description = "description"
    
    def _name_(self):
        
        for record in self:
            self.name = record.account_id.name

    cierre_cxc_id = fields.Many2one("account.cierre.cxc")
    name = fields.Char("Nombre", compute=_name_)
    account_id = fields.Many2one("account.account")
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    debe = fields.Monetary("Debe")
    haber = fields.Monetary("Haber")

class Movimiento(models.Model):
    _inherit = "account.move.line"
    
    cierre_cxc_id = fields.Many2one("account.cierre.cxc")