# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import datetime
from odoo.exceptions import Warning
import pytz
import time
import json

import logging
import math


_logger = logging.getLogger(__name__)



class Facturas(models.Model):
    _inherit = "account.move"

    cierre_id = fields.Many2one("account.cierre")


class CierreDiario(models.Model):
    _name = "account.cierre"
    _order = "create_date desc"
    _description = "Account Cierre"

    regions_list = [
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

    def _total_cobrado(self):
        self.total_cobrado = self._recorrec_lines("cobrado")

    def _total(self):
        self.total = self._recorrec_lines("total")

    def _total_facturado(self):
        self.total_facturado = self._recorrec_lines("facturado")

    def _team_id(self):
        if self.region == "San Pedro Sula":
            self.team_id = 43

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
    facturas_ids = fields.One2many("account.move", "cierre_id", "Facturas")
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
        if self.region == self.regions_list[1][0]:
            canales_ids = [35, 36, 37, 38, 39, 45, 47, 53]
        elif self.region == self.regions_list[0][0]:
            canales_ids = [43, 41, 46, 58, 44]
        else:
            canales_ids = [50, 49]

        pagos = self.env['account.payment'].sudo().search([
            '&',
            '&',
            '&',
            ('date', '=', self.date),
            ('company_id', '=', self.company_id.id),
            ('region', '=', self.region),
            ('partner_type', '=', 'customer'),
            ('state', '=', 'posted'),
        ])
        self.register_ids(pagos, 'pagos')

        _logger.warning('Arreglo de Pagos : ' + str(pagos))
        # 1

        facturas = self.env['account.move'].sudo().search([
            '&',
            '&',
            '&',
            '&',
            '&',
            # '&',
            ('invoice_date', '=', self.date),
            ('company_id', '=', self.company_id.sudo().id),
            # ('user_id','in',users_ids),
            ('team_id', 'in', canales_ids),
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel'),
            ('state', '!=', 'draft'),
            # ('de_consignacion', '=', False),
        ])
        self.register_ids(facturas, 'facturas')
        _logger.warning('Arreglo de facturas : ' + str(facturas))
        # 1

        mas_de_un_pago_factura = {}
        ids_facturas = []

        # Recorrer los pagos
        for pago in pagos:
            # Recorrer los diarios del cierre asignados
            for item in self.cierre_line_ids:
                # Compartar que pagos entran en los diarios de cierre
                if pago.journal_id.sudo().id == item.journal_id.sudo().id:
                    _logger.warning('id pago diario:' + str(pago.journal_id.sudo().id) + 'id item diario:'+ str(item.journal_id.sudo().id))
                    acumulado_factura = 0  # lo acumulado de facturas
                    # recorrer facturas de los pagos
                    for factura in pago.move_id.sudo().ids:
                        #_logger.warning('Prueba 1 . factura : '+ str(factura))
                        #_logger.warning('pagos.move=_id.sudo.ids : '+ str(pago.move_id.sudo().ids))

                        if factura not in ids_facturas:
                            factura_move= self.env['account.move'].sudo().browse(factura)
                            factura_id = self.env['account.move'].search([('name', '=', factura_move.ref)])
                            self.register_ids(factura_id, 'facturas de pagos')
                            _logger.warning(factura_id.invoice_date)
                            _logger.warning('total pago: ' + str(factura_id.invoice_payments_widget.pay))

                            if factura_id.invoice_date == self.date:
                                try:
                                    if factura_id.state != 'cancel':
                                        _logger.warning("Pase: ")
                                        payments_widget = factura_id.invoice_payments_widget
                                        payments_list = payments_widget["content"]
                                        _logger.warning("Payments: " + str(payments_list))

                                    else:
                                        payments_widget = []
                                except:
                                    _logger.warning('Error . factura : '+ str(factura))
                                    raise Warning(
                                        f'Valor de payments_widget {factura_id.invoice_payments_widget} de factura {factura_id.name} con id {factura_id.id}')

                                for pay in payments_list:
                                    if pay['date'] == str(self.date) and pay['account_payment_id'] == pago.id:
                                        acumulado_factura += pay['amount']
                                        if len(payments_widget) > 1:
                                            try:
                                                mas_de_un_pago_factura[factura_id.internal_number]
                                                temp = mas_de_un_pago_factura[factura_id.internal_number] - 1
                                                if temp <= 0:
                                                    if 'Crédito' not in factura_id.invoice_payment_term_id.sudo().name:
                                                        ids_facturas = ids_facturas + \
                                                            [factura_id.id]
                                                else:
                                                    mas_de_un_pago_factura[factura_id.internal_number] = temp
                                            except:
                                                mas_de_un_pago_factura[factura_id.internal_number] = len(
                                                    payments_widget) - 1
                                        else:
                                            if 'Crédito' not in factura_id.invoice_payment_term_id.sudo().name:
                                                ids_facturas = ids_facturas + \
                                                    [factura_id.id]

                    self.write({
                        'cierre_line_ids': [(1, item.id, {
                            'facturado': acumulado_factura + item.facturado,
                            'cobrado': pago.amount + item.cobrado if acumulado_factura == 0 else item.cobrado
                        })]
                    })
                    # ids_facturas = ids_facturas + pago.invoice_ids.sudo().ids
        self.register_list(ids_facturas, 'ids_facturas')
        for factura in facturas:
            if factura.payment_state == 'not_paid' and factura.invoice_payment_term_id.sudo().name == 'Contado':
                self.write({
                    'facturas_ids': [(4, factura.id)]
                })

        for factura in facturas:
            if factura.id not in ids_facturas:
                if factura.invoice_payment_term_id.sudo().name != 'Contado':
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
                    j = 0
                    while j < 2:
                        obj = self.create({
                            'date': today,
                            'company_id': i,
                            'region': self.regions_list[j][0]
                        })
                        ids.append(obj.id)
                        j += 1
                """else:
                    obj = self.create({
                        'date': today,
                        'company_id': i,
                        'region': self.regions_list[0][0]
                    })
                    ids.append(obj.id)"""
            for i in ids:
                principal_emails = "lmoran@megatk.com,jmoran@meditekhn.com,dvasquez@megatk.com"
                cc_mega = "yalvarado@megatk.com"
                cc_meditek = "nfuentes@meditekhn.com"
                cierre = self.sudo().browse(i)
                cierre.iniciar_cierre()
                time.sleep(1)
                cierre.procesar_cierre()
                if cierre.company_id.sudo().id in [8, 12]:
                    time.sleep(1)
                    # if cierre.company_id.sudo().id == 12:
                    #    cc_mega += ",kpadilla@meditekhn.com"
                    if cierre.sudo().region == 'San Pedro Sula':
                        cc_mega += ",vmoran@megatk.com"
                        cc_meditek += "dgarcia@meditekhn.com"
                    # print("/////////////",principal_emails,cc_mega,"//////////////")
                    cierre.send_email(principal_emails, cc_mega)
                if cierre.company_id.sudo().id in [9]:
                    time.sleep(1)
                    cierre.send_email(principal_emails, cc_meditek)
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
    _description = "description"

    @api.depends('cobrado', 'facturado', 'credito')
    def _total(self):
        for record in self:
            total = record.cobrado + record.facturado
            if record.credito:
                total = 0
            record.total = round(total, 2)

    @api.depends('credito', 'journal_id.name')
    def _name_(self):
        for record in self:
            if record.credito:
                record.name = "Al credito"
            else:
                record.name = record.journal_id.name

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
