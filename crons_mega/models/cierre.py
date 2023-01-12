# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import datetime
import pytz
import time
import json


class Facturas(models.Model):
    _inherit = "account.invoice"

    cierre_id = fields.Many2one("account.cierre")


class CierreDiario(models.Model):
    _name = "account.cierre"
    _order = "create_date desc"

    regions_list = [
        ("Nicaragua", "NIC"),
        ("San Pedro Sula", "SPS"),
        ("Tegucigalpa", "TGU"),
    ]

    def _recorrec_lines(self, field):
        total = 0
        for item in self.cierre_line_ids:
            if field == 'total':
                total += item.total
            if field == 'cobrado':
                total += item.cobrado
            if field == 'facturado':
                total += item.facturado
        return round(total, 2)

    @api.one
    def _total_cobrado(self):
        self.total_cobrado = self._recorrec_lines("cobrado")
        
    @api.one
    def _total(self):
        self.total = self._recorrec_lines("total")

    @api.one
    def _total_facturado(self):
        self.total_facturado = self._recorrec_lines("facturado")

    @api.one
    def _team_id(self):
        if self.region == "San Pedro Sula":
            self.team_id = 43

    @api.one
    def _name_(self):
        self.name = self.company_id.name + \
            " - " + self.date.strftime("%d/%m/%Y")

    name = fields.Char(compute=_name_)
    cierre_line_ids = fields.One2many(
        "account.cierre.line", "cierre_id", string="Lineas de Cierre")
    company_id = fields.Many2one(
        "res.company", "Compañia", default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    total_facturado = fields.Monetary(
        "Total Facturado", compute=_total_facturado)
    facturas_ids = fields.One2many("account.invoice", "cierre_id", "Facturas")
    total_cobrado = fields.Monetary("Total Cobrado", compute=_total_cobrado)
    total = fields.Monetary("Total Cobrado", compute=_total)
    region = fields.Selection(
        regions_list, string="Region/Zona", required=True)
    date = fields.Date("Fecha")
    logs = fields.Text("Registros", default="")
    state = fields.Selection([
        ("draft", "Borrador"),
        ("init", "Iniciado"),
        ("proccess", "Proceso"),
        ("done", "Hecho"),
        ("cancel", "Cancelado")
    ], string="Estado", default="draft")
    date = fields.Date("Fecha")

    def volver_borrador(self):
        self.write({
            'state': 'draft'
        })

    def cancel(self):
        lines_ids = []
        facturas = []
        for item in self.cierre_line_ids:
            lines_ids.append((2, item.sudo().id))
        for item in self.facturas_ids:
            facturas.append((3, item.sudo().id))

        self.write({
            'cierre_line_ids': lines_ids,
            'facturas_ids': facturas,
            'logs': "",
            'state': 'cancel'
        })

    def iniciar_cierre(self):
        journal_ids = self.env['res.config.settings'].sudo().get_values_journal_ids(
            self.company_id.id)
        values = [(0, 0,  {
            'credito': True
        })]
        for item in journal_ids:
            values.append((0, 0, {
                'journal_id': item
            }))
        self.write({
            'cierre_line_ids': values,
            'state': 'init'
        })

    def register_ids(self, obj, name):
        text = ""
        length = 0
        for item in obj:
            text += str(item.sudo().id) + ", "
            length += 1
        self.write({
            'logs': self.logs + "ids de objetos consultados: \n"
            + text + "\n Nombre lista: " + name + "\n" + "Tamaño: " + str(length) +
            "\n ----------------------------------------------------------------------\n"
        })

    def register_list(self, lists, name):
        text = ""
        for item in lists:
            try:
                text += item + ", "
            except:
                text += str(item) + ", "
        self.write({
            'logs': self.logs + "Datos en la lista: \n"
            + text + "\n Nombre lista: " + name + "\n" + "Tamaño: " + str(len(lists)) +
            "\n ----------------------------------------------------------------------\n"
        })

    # def register_sleep(self,i,secuencia):
    #     cierre = self.browse(i)
    #     self.write({
    #         'logs': self.logs +secuencia +" sleep: \n    Fecha: " +
    #         str(cierre.date) + "\nCompañia: " + cierre.company_id.name + "\nZona: "+ cierre.region +
    #         "\n ----------------------------------------------------------------------\n"
    #     })

    def procesar_cierre(self):
        if self.region == self.regions_list[2][0]:
            canales_ids = [35, 36, 37, 38, 39, 45, 47, 53]
        elif self.region == self.regions_list[1][0]:
            canales_ids = [43, 41, 46, 58, 44]
        else:
            canales_ids = [50, 49]
        pagos = self.env['account.payment'].sudo().search([
            '&',
            '&',
            '&',
            ('payment_date', '=', self.date),
            ('company_id', '=', self.company_id.id),
            ('region', '=', self.region),
            ('partner_type', '=', 'customer'),
            ('state', '=', 'posted'),
        ])
        self.register_ids(pagos, 'pagos')
        facturas = self.env['account.invoice'].sudo().search([
            '&',
            '&',
            '&',
            '&',
            '&',
            # '&',
            ('date_invoice', '=', self.date),
            ('company_id', '=', self.company_id.sudo().id),
            # ('user_id','in',users_ids),
            ('team_id', 'in', canales_ids),
            ('type', '=', 'out_invoice'),
            ('state', '!=', 'cancel'),
            ('state', '!=', 'draft'),
            # ('de_consignacion', '=', False),
        ])
        self.register_ids(facturas, 'facturas')
        mas_de_un_pago_factura = {}
        ids_facturas = []
        # Recorrer los pagos
        for pago in pagos:
            # Recorrer los diarios del cierre asignados
            for item in self.cierre_line_ids:
                # Compartar que pagos entran en los diarios de cierre
                if pago.journal_id.sudo().id == item.journal_id.sudo().id:
                    acumulado_factura = 0 # lo acumulado de facturas
                    # recorrer facturas de los pagos
                    for factura in pago.invoice_ids.sudo().ids:
                        if factura not in ids_facturas:
                            factura_id = self.env['account.invoice'].sudo().browse(
                                factura)
                            self.register_ids(factura_id, 'facturas de pagos')
                            if factura_id.date_invoice == self.date:
                                payments_widget = json.loads(factura_id.payments_widget)['content']
                                
                                for pay in payments_widget:
                                    if pay['date'] == str(self.date) and pay['account_payment_id'] == pago.id:
                                        acumulado_factura += pay['amount']
                                        if len(payments_widget) > 1:
                                            try:
                                                mas_de_un_pago_factura[factura_id.internal_number]
                                                temp = mas_de_un_pago_factura[factura_id.internal_number] -1
                                                if temp <= 0:
                                                    ids_facturas = ids_facturas + [factura_id.id]
                                                else:
                                                    mas_de_un_pago_factura[factura_id.internal_number] = temp
                                            except:
                                                mas_de_un_pago_factura[factura_id.internal_number] = len(payments_widget) - 1
                                        else:
                                            ids_facturas = ids_facturas + [factura_id.id]
                                            
                    self.write({
                        'cierre_line_ids': [(1, item.id, {
                            'facturado': acumulado_factura + item.facturado,
                            'cobrado': pago.amount + item.cobrado if acumulado_factura == 0 else item.cobrado
                        })]
                    })
                    # ids_facturas = ids_facturas + pago.invoice_ids.sudo().ids
        self.register_list(ids_facturas, 'ids_facturas')
        for factura in facturas:
            if factura.state == 'open' and factura.payment_term_id.sudo().name == 'Contado':
                self.write({
                    'facturas_ids': [(4, factura.id)]
                })

        for factura in facturas:
            if factura.id not in ids_facturas:
                if factura.payment_term_id.sudo().name != 'Contado':
                    for item in self.cierre_line_ids:
                        if item.credito:
                            self.write({
                                'cierre_line_ids': [(1, item.id, {
                                    'facturado': factura.amount_total_signed + item.facturado
                                })]
                            })
                # else:
                #     for item in self.cierre_line_ids:
                #         if item.journal_id.name == "Efectivo":
                #             self.write({
                #                 'cierre_line_ids': [(1, item.id, {
                #                     'facturado': factura.amount_total_signed + item.facturado
                #                 })]
                #             })
        self.write({
            'state': 'proccess'
        })

    def send_email(self, email, cc=""):
        template = self.env.ref(
            'crons_mega.email_template_cierre_diario_1')
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
        today = datetime.now(user_tz)
        if today.weekday() != 6:
            company_ids = [8, 9, 12]
            ids = []
            for i in company_ids:
                if i != 12:
                    j = 1
                    while j < 3:
                        obj = self.create({
                            'date': today,
                            'company_id': i,
                            'region': self.regions_list[j][0]
                        })
                        ids.append(obj.id)
                        j += 1
                else:
                    obj = self.create({
                        'date': today,
                        'company_id': i,
                        'region': self.regions_list[0][0]
                    })
                    ids.append(obj.id)
            for i in ids:
                cierre = self.sudo().browse(i)
                cierre.iniciar_cierre()
                time.sleep(1)
                cierre.procesar_cierre()
                # cierre.send_email("azelaya@megatk.com","ecolindres@megatk.com")
                if cierre.company_id.sudo().id in [8, 12]:
                    # print("lmoran@megatk.com,jmoran@meditekhn.com,dvasquez@megatk.com","eduron@megatk.com")
                    time.sleep(1)
                    cierre.send_email(
                        "lmoran@megatk.com,jmoran@meditekhn.com,dvasquez@megatk.com", "eduron@megatk.com")
                if cierre.company_id.sudo().id in [9]:
                    # print("lmoran@megatk.com,jmoran@meditekhn.com,dvasquez@megatk.com","nfuentes@meditekhn.com")
                    time.sleep(1)
                    cierre.send_email(
                        "lmoran@megatk.com,jmoran@meditekhn.com,dvasquez@megatk.com", "nfuentes@meditekhn.com")
                time.sleep(1)

    def go_to_view_tree(self):
        return {
            'name': 'Cierre Diario',
            'type': 'ir.actions.act_window',
            'res_model': 'account.cierre',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'target': 'current',
            'domain': [('company_id', '=', self.env.user.company_id.id)],
        }


class CierreDiarioLine(models.Model):
    _name = "account.cierre.line"

    @api.one
    def _name_(self):
        if self.credito:
            self.name = "Al credito"
        else:
            self.name = self.journal_id.name

    @api.one
    def _total(self):
        total = self.cobrado + self.facturado
        if self.credito:
            total = 0
        # if total < 0:
        #     total = total * (-1)
        # elif total == 0:
        #     total = self.cobrado
        self.total = round(total, 2)

    name = fields.Char("Nombre", compute=_name_)
    cierre_id = fields.Many2one("account.cierre")
    journal_id = fields.Many2one("account.journal")
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    facturado = fields.Monetary("Facturado", default=0)
    cobrado = fields.Monetary("Cobrado", default=0)
    total = fields.Monetary("Total", compute=_total)
    credito = fields.Boolean("Es Crédito")

    def toggle_credito(self):
        self.credito = not self.credito
