# -*- coding: utf-8 -*-
from odoo import models, api, fields
import datetime
from datetime import datetime as dt, timedelta
import pytz
import time
import json


class Factura(models.Model):
    _inherit = "account.invoice"

    expire_id = fields.Many2one("account.invoice.expire")
    expire_customer_id = fields.Many2one("account.invoice.expire")
    expire_line_id = fields.Many2one("invoice.expire.line")
    warning_customer = fields.Boolean(default=False)
    state_expired = fields.Selection([
        ("none", "No Vencida"),
        ("1er Aviso", "1er Aviso"),
        ("2do Aviso", "2do Aviso")
    ], default="none", string="Estado Aviso")


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
    invoice_expire_line = fields.One2many(
        "invoice.expire.line", "invoice_expire_id", "Facturas")
    facturas_ids_customers = fields.One2many(
        "account.invoice", "expire_customer_id", "Facturas Vencidas")
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
        for item in self.facturas_ids_customers:
            if item.date_due.strftime("%Y-%m-%d") == self.date.strftime("%Y-%m-%d"):
                item.write({
                    'warning_customer': False
                })

        for item in self.facturas_ids:
            item.write({
                'state_expired': 'none'
            })
        self.write({
            'facturas_ids': [(6, 0, [])],
            'facturas_ids_customers': [(6, 0, [])],
            'invoice_expire_line': [(5, 0, [])],
            'state': 'cancel'
        })

    def init_review(self):
        dias_3 = self.date + timedelta(days=-3)
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
            ('state_expired', 'in', ['none', '1er Aviso']),
            ('date_due', 'in', [
                dias_7.strftime("%Y-%m-%d"),
                dias_14.strftime("%Y-%m-%d"),
            ])]
        filtros2 = [
            '&',
            '&',
            '&',
            '&',
            ('company_id', '=', self.company_id.sudo().id),
            ('type', '=', 'out_invoice'),
            ('state', '=', 'open'),
            ('state_expired', 'in', ['none', '1er Aviso', '2do Aviso']),
            ('date_due', '<=',
                dias_3.strftime("%Y-%m-%d")
             )
            ]
        facturas_ids = self.env['account.invoice'].sudo().search(filtros)
        facturas_ids_customers = self.env['account.invoice'].sudo().search(
            filtros2)
        ids_customers = []

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
        for factura in facturas_ids_customers:
            range_date = self.env['invoice.expire.line']
            if not "oc. " in factura.number:
                if (range_date.rangeDate(factura.date_invoice,self.date) % 2) != 0:
                    ids_customers.append(factura.id)
         
        self.write({
            'state': 'init',
            'facturas_ids_customers': [(6, 0, ids_customers)]
        })

    def _exist_id(self, id, list):
        for item in list:
            try:
                if item[2]['user_id'] == id:
                    return True
            except:
                if item[2]['partner_id'] == id:
                    return True
        return False

    def procesar_facturas(self):
        vals = []
        vals2 = []
        for factura in self.facturas_ids_customers:
            if factura.date_due.strftime("%Y-%m-%d") == self.date.strftime("%Y-%m-%d"):
                factura.write({
                    'warning_customer': True
                })

            if len(vals2) == 0:
                vals2.append((0, 0, {
                    'partner_id': factura.partner_id.id,
                    'facturas_ids': [(6, 0, [factura.id])],
                    'type': 'customer'
                }))
            else:
                if self._exist_id(factura.partner_id.id, vals2):
                    for item in vals2:
                        if item[2]['partner_id'] == factura.partner_id.id:
                            item[2]['facturas_ids'][0][2].append(factura.id)
                else:
                    vals2.append((0, 0, {
                        'partner_id': factura.partner_id.id,
                        'facturas_ids': [(6, 0, [factura.id])],
                        'type': 'customer'
                    }))

        for factura in self.facturas_ids:
            if len(vals) == 0:
                vals.append((0, 0, {
                    'user_id': factura.user_id.id,
                    'facturas_ids': [(6, 0, [factura.id])]
                }))
            else:
                if self._exist_id(factura.user_id.id, vals):
                    for item in vals:
                        if item[2]['user_id'] == factura.user_id.id:
                            item[2]['facturas_ids'][0][2].append(factura.id)
                else:
                    vals.append((0, 0, {
                        'user_id': factura.user_id.id,
                        'facturas_ids': [(6, 0, [factura.id])]
                    }))
        self.write({
            'invoice_expire_line': vals + vals2,
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
        today = dt.now(user_tz)
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

    @api.one
    def _name_(self):
        self.name = self.user_id.name if self.type == 'comercial' else self.partner_id.name

    @api.one
    def _company_id(self):
        self.company_id = self.invoice_expire_id.company_id.id

    @api.one
    def _show_tabla(self):
        if len(self.facturas_ids.ids) > 1:
            self.show_tabla = True
        else:
            self.show_tabla = False
    
    
    def rangeDate(self, dateInit, dateEnd):
        try:
            dates = [
                dateInit + datetime.timedelta(n) for n in range(int((dateEnd - dateInit).days))
            ]
            return len(dates)
        except:
            return 1
          
    

    @api.one
    def _time_due(self):
        if not len(self.facturas_ids.ids) > 1:
            for invoice in self.facturas_ids:
                self.time_due = self.rangeDate(invoice.date_due,self.invoice_expire_id.date)

    name = fields.Char("Nombre", compute=_name_)
    user_id = fields.Many2one("res.users", string="Comercial")
    partner_id = fields.Many2one("res.partner", string="Cliente")
    invoice_expire_id = fields.Many2one("account.invoice.expire")
    company_id = fields.Many2one(
        "res.company", compute=_company_id)
    facturas_ids = fields.One2many(
        "account.invoice", "expire_line_id", "Facturas")
    show_tabla = fields.Boolean(compute=_show_tabla)
    time_due = fields.Integer(compute=_time_due)
    type = fields.Selection([
        ("customer", "Cliente"),
        ("comercial", "Comercial")
    ], string="Tipo", default='comercial')
    
    
    
    

    def send_email(self):
        if self.type == 'comercial':
            template = self.env.ref(
                'crons_mega.email_template_account_invoice_expire')
            email_values = {
                'email_from': 'megatk.no_reply@megatk.com',
                'email_to': self.user_id.login,
            }
            template.send_mail(
                self.id, email_values=email_values, force_send=True)
        if self.type == 'customer':
            if self.partner_id.total_due > 0:
                template = self.env.ref(
                    'crons_mega.email_template_account_invoice_expire_customer')
                email_values = {
                    'email_from': 'megatk.no_reply@megatk.com',
                    'email_to': self.partner_id.email,
                }
                template.send_mail(
                    self.id, email_values=email_values, force_send=True)
        return True
