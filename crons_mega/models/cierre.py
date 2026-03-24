# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import datetime
from odoo.exceptions import UserError
import pytz
import time
import json
from datetime import date

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
    promedio_mensual = fields.Monetary("Promedio mensual",)
    promedio_anual = fields.Monetary("Promedio anual")
    region = fields.Selection(
        regions_list, string="Region/Zona", required=True)
    date = fields.Date("Fecha")
    ganancia_diaria = fields.Monetary("Ganancia Diaria",)
    
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

    def _parse_int_list(self, value):
        if not value:
            return []

        if isinstance(value, (list, tuple)):
            return [int(item) for item in value if item]

        cleaned_value = str(value).replace('[', '').replace(']', '')
        return [int(item.strip()) for item in cleaned_value.split(',') if item.strip()]

    def _get_region_team_ids(self):
        default_team_ids = {
            self.regions_list[1][0]: [35, 36, 37, 38, 39, 45, 47, 53],
            self.regions_list[0][0]: [43, 41, 46, 58, 44],
        }

        if self.region == self.regions_list[0][0]:
            configured_ids = self._parse_int_list(
                self.env['ir.config_parameter'].sudo().get_param('crons_mega.teams_sps')
            )
            if configured_ids:
                return configured_ids

        return default_team_ids.get(self.region, [50, 49])

    def _is_credit_invoice(self, invoice):
        payment_term = invoice.invoice_payment_term_id.sudo()
        if not payment_term:
            return False

        if 'credit' in payment_term._fields:
            return bool(payment_term.credit)

        return any(line.nb_days > 0 for line in payment_term.line_ids)

    def _to_date(self, value):
        if not value:
            return False

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        return fields.Date.to_date(value)

    def _get_invoice_payment_lines(self, invoice):
        payments_widget = invoice.invoice_payments_widget
        if not payments_widget:
            return []

        if isinstance(payments_widget, str):
            try:
                payments_widget = json.loads(payments_widget)
            except ValueError:
                return []

        if not isinstance(payments_widget, dict):
            return []

        return payments_widget.get('content', []) or []

    def _get_payment_related_invoices(self, payment):
        related_invoices = self.env['account.move']

        if 'reconciled_invoice_ids' in payment._fields:
            related_invoices |= payment.reconciled_invoice_ids

        partial_reconciles = payment.move_id.line_ids.matched_debit_ids | payment.move_id.line_ids.matched_credit_ids
        related_invoices |= partial_reconciles.debit_move_id.move_id | partial_reconciles.credit_move_id.move_id
        related_invoices -= payment.move_id

        return related_invoices.filtered(
            lambda move: move.move_type == 'out_invoice' and move.company_id.id == self.company_id.id
        )

    def _get_paid_amount_for_invoice(self, payment, invoice):
        paid_amount = 0.0

        for payment_line in self._get_invoice_payment_lines(invoice):
            payment_date = self._to_date(payment_line.get('date') or payment_line.get('payment_date'))
            payment_id = payment_line.get('account_payment_id') or payment_line.get('payment_id')
            if payment_id != payment.id or payment_date != self.date:
                continue

            try:
                paid_amount += float(payment_line.get('amount', 0.0) or 0.0)
            except (TypeError, ValueError):
                continue

        if paid_amount:
            return round(paid_amount, 2)

        partial_reconciles = payment.move_id.line_ids.matched_debit_ids | payment.move_id.line_ids.matched_credit_ids
        related_partials = partial_reconciles.filtered(
            lambda partial: partial.debit_move_id.move_id == invoice or partial.credit_move_id.move_id == invoice
        )

        for partial in related_partials:
            partial_date = self._to_date(getattr(partial, 'max_date', False) or getattr(partial, 'create_date', False))
            if not partial_date or partial_date == self.date:
                paid_amount += partial.amount

        return round(paid_amount, 2)

    def procesar_cierre(self):
        canales_ids = self._get_region_team_ids()

        pagos = self.env['account.payment'].sudo().search([
            '&',
            '&',
            ('date', '=', self.date),
            ('company_id', '=', self.company_id.id),
            ('partner_type', '=', 'customer'),
            ('state', '=', 'posted'),
        ])
        self.register_ids(pagos, 'pagos')

        facturas_domain = [
            ('invoice_date', '=', self.date),
            ('company_id', '=', self.company_id.sudo().id),
            ('move_type', '=', 'out_invoice'),
            ('state', 'not in', ['cancel', 'draft']),
        ]
        if canales_ids:
            facturas_domain.append(('team_id', 'in', canales_ids))

        facturas = self.env['account.move'].sudo().search(facturas_domain)
        self.register_ids(facturas, 'facturas')

        facturas_del_dia_ids = set(facturas.ids)
        ids_facturas = set()
        facturas_ganancia = self.env['account.move']
        lines_by_journal = {
            line.journal_id.id: line for line in self.cierre_line_ids if not line.credito and line.journal_id
        }
        line_values = {
            line.id: {
                'facturado': line.facturado,
                'cobrado': line.cobrado,
            }
            for line in lines_by_journal.values()
        }

        for pago in pagos:
            line = lines_by_journal.get(pago.journal_id.id)
            if not line:
                continue

            related_invoices = self._get_payment_related_invoices(pago)
            if canales_ids:
                related_invoices = related_invoices.filtered(lambda invoice: invoice.team_id.id in canales_ids)
            if not related_invoices:
                continue

            facturado_diario = 0.0
            cobrado_cxc = 0.0
            related_day_invoices = related_invoices.filtered(
                lambda invoice: invoice.id in facturas_del_dia_ids
            )
            self.register_ids(related_day_invoices, f'facturas de pago {pago.id}')

            for factura in related_invoices:
                paid_amount = self._get_paid_amount_for_invoice(pago, factura)
                if not paid_amount:
                    continue

                if factura.id in facturas_del_dia_ids:
                    facturado_diario += paid_amount
                    facturas_ganancia |= factura
                    if not self._is_credit_invoice(factura):
                        ids_facturas.add(factura.id)
                else:
                    cobrado_cxc += paid_amount

            line_values[line.id]['facturado'] += facturado_diario
            line_values[line.id]['cobrado'] += cobrado_cxc

        if line_values:
            self.write({
                'cierre_line_ids': [(1, line_id, values) for line_id, values in line_values.items()]
            })

        self.register_list(list(ids_facturas), 'ids_facturas')
        for factura in facturas:
            if factura.amount_residual > 0 and not self._is_credit_invoice(factura):
                self.write({
                    'facturas_ids': [(4, factura.id)]
                })

        credit_line = self.cierre_line_ids.filtered('credito')[:1]
        credit_total = credit_line.facturado if credit_line else 0.0
        for factura in facturas:
            if factura.id not in ids_facturas and self._is_credit_invoice(factura):
                credit_total += factura.amount_total_signed

        if credit_line:
            self.write({
                'cierre_line_ids': [(1, credit_line.id, {
                    'facturado': credit_total
                })]
            })
        
        ganancia_total = 0
        for factura in facturas_ganancia:
            costo_total = sum(line.product_id.standard_price * line.quantity for line in factura.invoice_line_ids)
            ganancia_factura = factura.amount_total - costo_total
            ganancia_total += ganancia_factura
        self.ganancia_diaria = ganancia_total
        
        self.procesar_promedio_mensual()
        time.sleep(1)
        self.procesar_promedio_anual()
        
        self.write({
            'state': 'proccess'
        })
        
    def procesar_promedio_mensual(self):
        canales_ids = self._get_region_team_ids()

        dia = self.date.day
        mes = self.date.month
        año = self.date.year
        
        #fecha para promedio mensual
        fecha_init_mensual = date(año, mes, 1)

        facturas_domain = [
            ('invoice_date', '>=', fecha_init_mensual),
            ('invoice_date', '<=', self.date),
            ('company_id', '=', self.company_id.sudo().id),
            ('move_type', '=', 'out_invoice'),
            ('state', 'not in', ['cancel', 'draft']),
        ]
        if canales_ids:
            facturas_domain.append(('team_id', 'in', canales_ids))

        facturas = self.env['account.move'].sudo().search(facturas_domain)

        # Recorrer las facturas y sumar los totales
        total_ventas = sum(factura.amount_total for factura in facturas)
        
        promedio = total_ventas / dia
        self.write({
            'promedio_mensual': promedio
        })
            
    def procesar_promedio_anual(self):
        canales_ids = self._get_region_team_ids()

        dia = self.date.day
        mes = self.date.month
        año = self.date.year

        #fecha para el promedio anual
        fecha_init_anual = date(año, 1, 1)

        facturas_domain = [
            ('invoice_date', '>=', fecha_init_anual),
            ('invoice_date', '<=', self.date),
            ('company_id', '=', self.company_id.sudo().id),
            ('move_type', '=', 'out_invoice'),
            ('state', 'not in', ['cancel', 'draft']),
        ]
        if canales_ids:
            facturas_domain.append(('team_id', 'in', canales_ids))

        facturas = self.env['account.move'].sudo().search(facturas_domain)
        
        # Recorrer las facturas y sumar los totales
        total_ventas = sum(factura.amount_total for factura in facturas)
        
        promedio = total_ventas / mes
        self.write({
            'promedio_anual': promedio
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

            for i in ids:
                # principal_emails = "lmoran@megatk.com,jmoran@meditekhn.com,dvasquez@megatk.com,erodriguez@megatk.com"
                # cc_mega = "yalvarado@megatk.com"
                # cc_meditek = "nfuentes@meditekhn.com"
                principal_emails = "areyes@megatk.com"
                cc_mega = "areyes@megatk.com"
                cc_meditek = "areyes@megatk.com"
                cierre = self.sudo().browse(i)
                cierre.iniciar_cierre()
                time.sleep(1)
                cierre.procesar_cierre()
                time.sleep(1)
                
                if cierre.company_id.sudo().id in [8, 12]:
                    time.sleep(1)
                    if cierre.sudo().region == 'San Pedro Sula':
                        # cc_mega += ",vmoran@megatk.com"
                        # cc_meditek += "dgarcia@meditekhn.com"
                        cc_mega += ",areyes@megatk.com"
                        cc_meditek += "areyes@megatk.com"
                    cierre.send_email(principal_emails, cc_mega)
                if cierre.company_id.sudo().id in [9]:
                    time.sleep(1)
                    cierre.send_email(principal_emails, cc_meditek) #Meditek
                time.sleep(1)

    def go_to_view_tree(self):
        return {
            'name': 'Cierre Diario',
            'type': 'ir.actions.act_window',
            'res_model': 'account.cierre',
            'view_type': 'form',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
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
