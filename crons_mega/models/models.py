# -*- coding: utf-8 -*-

from odoo import models, api, fields
from datetime import datetime as dt, timedelta
import datetime
import pytz
import time


class LineasFactura(models.Model):
    _inherit = "account.move.line"
    
    product_report_id = fields.Many2one("product.report")

class Marcas(models.Model):
    _inherit = "product.marca"
    
    setting_id = fields.Many2one("product.template")
    
class ReporteSemanal(models.Model):
    _name = "product.report.line"
    _description = "description"
 
    product_id = fields.Many2one("product.template","Producto")
    report_id = fields.Many2one("product.report")
    total_quantity = fields.Float("Cantidad Vendida")
    total_sold = fields.Monetary("Total Vendido")
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)

class ReporteSemanal(models.Model):
    _name = "product.report"
    _order = "create_date desc"
    _description = "description"
    
    def _name_(self):
        self.name = self.company_id.name+' ('+ str(self.date_from) +' // '+str(self.date_to)+')'
    
    def _total(self):
        total = 0
        for item in self.line_invoices:
             total += item.price_total
        self.total = round(total, 2)
    
    def _sub_total(self):
        total = 0
        for item in self.line_invoices:
             total += item.price_subtotal
        self.sub_total = round(total, 2)
    
    def _tax_total(self):
        total = 0
        for item in self.line_invoices:
             total += item.price_tax
        self.tax_total = round(total, 2)
    
    name = fields.Char(compute=_name_)
    date_from = fields.Date("De")
    date_to = fields.Date("A")
    line_report = fields.One2many("product.report.line","report_id","Lineas de Reporte")
    line_invoices = fields.One2many("account.move.line","product_report_id","Lineas de Factura")
    company_id = fields.Many2one("res.company","Compañia",default=lambda self : self.env.user.company_id.id)
    state = fields.Selection([
        ("draft", "Borrador"),
        ("init", "Iniciado"),
        ("proccess", "Proceso"),
        ("done", "Hecho"),
        ("cancel", "Cancelado")
    ], string="Estado", default="draft")
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    total = fields.Monetary(compute=_total)
    sub_total = fields.Monetary(compute=_sub_total)
    tax_total = fields.Monetary(compute=_tax_total)
    
    def back_to_draft(self):
        self.write({
            'state': 'draft'
        })
        
    def cancel_report(self):
        self.write({
            'line_invoices': [(6,0,[])],
            'line_report': [(5,0,[])],
            'state': 'cancel'
        })
        
    def rangeDate(self,dateInit,dateEnd):
        dates = [
        dateInit + datetime.timedelta(n) for n in range(int((dateEnd - dateInit).days))
        ]
        return dates
    
    def init_report(self):
        marcas = self.env['res.config.settings'].get_values()
        marcas = marcas['marca_ids'][0][2]
        range_date = self.rangeDate(self.date_from,self.date_to)
        invoice_ids = self.env['account.move'].search(['&',
            ('date_invoice','in',range_date),
            ('state','=','paid')
        ])
        invoices_line_ids = []
        for i in invoice_ids:
            for j in i.invoice_line_ids:
                invoices_line_ids.append(j.id)
        line_invoice = self.env['account.move.line'].browse(invoices_line_ids)
        lines = []
        for line in line_invoice:
            if line.product_id.marca_id.id in marcas:
                lines.append(line.id)
        self.write({
            'line_invoices': [(6,0,lines)],
            'state': 'init'
        })
        
    def proccess_line_report(self):
        marcas = self.env['res.config.settings'].get_values()
        marcas = marcas['marca_ids'][0][2]
        product_ids = self.env['product.template'].search([('marca_id','in',marcas)])
        for product in product_ids:
            total_quantity = 0
            total_sold = 0
            for line in self.line_invoices: 
                if line.product_id.id == product.id:
                    total_quantity += line.quantity
                    total_sold += line.price_total
            if total_quantity != 0 and total_sold != 0:
                self.write({
                    'line_report': [(0,0,{
                        'product_id': product.id,
                        'total_quantity': total_quantity,
                        'total_sold': total_sold
                    })],
                })
        self.write({
            'state': 'proccess'
        })

    def send_email(self,email,cc):
        template = self.env.ref(
            'crons_mega.email_template_marca_productos')
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
        admin = self.env['res.users'].sudo().browse(2)
        user_tz = pytz.timezone(self.env.context.get('tz') or admin.tz)
        _to = dt.now(user_tz)
        if _to.weekday() == 5:
            _from = _to + timedelta(days=-7)
            company_ids = [8, 12]
            ids = []
            for i in company_ids:
                id = self.create({
                    'date_from': _from,
                    'date_to': _to,
                    'company_id': i
                })
                ids.append(id.id)
            for i in ids:
                principal_emails = "lmoran@megatk.com"
                cc = "yalvarado@megatk.com"
                cierre = self.sudo().browse(i)
                cierre.init_report()
                time.sleep(1)
                cierre.proccess_line_report()
                time.sleep(1)
                cierre.send_email(principal_emails,cc)