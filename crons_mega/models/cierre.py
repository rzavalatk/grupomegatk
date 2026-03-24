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

    def _get_region_values(self):
        """Devuelve variantes de la región para evitar filtros vacíos por formato."""
        self.ensure_one()
        values = {self.region}
        for key, label in self.regions_list:
            if self.region in (key, label):
                values.update([key, label])
                break
        return list(values)

    def _get_canales_ids(self):
        """Obtiene canales por región con fallback a configuración y valores históricos."""
        self.ensure_one()

        if self.region in ("San Pedro Sula", "SPS"):
            try:
                canales = self.env['res.config.settings'].sudo().get_values_teams_sps()
                if canales:
                    return canales
            except Exception:
                pass
            return [43, 41, 46, 58, 44]

        if self.region in ("Tegucigalpa", "TGU"):
            return [35, 36, 37, 38, 39, 45, 47, 53]

        return [50, 49]

    def _is_credit_term(self, payment_term):
        """Determina si un término de pago es crédito sin depender del nombre textual."""
        if not payment_term:
            return False

        if 'credit' in payment_term._fields:
            return bool(payment_term.credit)

        if payment_term.line_ids:
            return any(line.nb_days > 0 for line in payment_term.line_ids)

        name = (payment_term.name or '').strip().lower()
        return 'credito' in name or 'crédito' in name

    def _search_facturas_by_team(self, base_domain, canales_ids):
        """Busca facturas por canales y si no encuentra, hace fallback sin canal para evitar reportes vacíos."""
        self.ensure_one()

        factura_obj = self.env['account.move'].sudo()
        if not canales_ids:
            return factura_obj.search(base_domain)

        team_domain = ['|', ('team_id', 'in', canales_ids), ('team_id', '=', False)]
        facturas = factura_obj.search(base_domain + team_domain)
        if facturas:
            return facturas

        # Fallback controlado para detectar desalineación de canales configurados.
        facturas = factura_obj.search(base_domain)
        if facturas:
            self.write({
                'logs': self.logs + (
                    f"Advertencia: no hubo facturas con canales {canales_ids} para región {self.region}. "
                    "Se aplicó fallback sin filtro de team_id. Revisar canales de cierre.\n"
                )
            })
        return facturas

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

    def procesar_cierre(self):
        self.ensure_one()
        canales_ids = self._get_canales_ids()
        region_values = self._get_region_values()

        pagos = self.env['account.payment'].sudo().search([
            ('date', '=', self.date),
            ('company_id', '=', self.company_id.id),
            ('region', 'in', region_values),
            ('partner_type', '=', 'customer'),
            ('state', '=', 'posted'),
        ])
        self.write({
            'logs': self.logs + f"Región cierre: {self.region} | Valores usados: {region_values} | Canales usados: {canales_ids}\n"
        })
        self.register_ids(pagos, 'pagos')

        facturas_domain = [
            ('invoice_date', '=', self.date),
            ('company_id', '=', self.company_id.sudo().id),
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel'),
            ('state', '!=', 'draft'),
        ]
        facturas = self._search_facturas_by_team(facturas_domain, canales_ids)
        self.register_ids(facturas, 'facturas')

        ids_facturas = set()
        facturas_ganancia = []

        # Recorrer los pagos
        for pago in pagos:
            facturas_relacionadas = self.env['account.move']
            if 'reconciled_invoice_ids' in pago._fields:
                facturas_relacionadas = pago.reconciled_invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice')

            if not facturas_relacionadas:
                for factura in pago.move_id.sudo().ids:
                    factura_move = self.env['account.move'].sudo().browse(factura)
                    if factura_move.ref:
                        facturas_relacionadas |= self.env['account.move'].search([
                            ('name', '=', factura_move.ref),
                            ('move_type', '=', 'out_invoice'),
                        ])

            # Recorrer los diarios del cierre asignados
            for item in self.cierre_line_ids:
                # Compartar que pagos entran en los diarios de cierre
                if pago.journal_id.sudo().id == item.journal_id.sudo().id:
                    acumulado_factura = 0  # lo acumulado de facturas
                    # recorrer facturas de los pagos
                    for factura_id in facturas_relacionadas:
                        self.register_ids(factura_id, 'facturas de pagos')

                        if factura_id.invoice_date == self.date and factura_id.state != 'cancel':
                            try:
                                payments_widget = factura_id.invoice_payments_widget or {}
                                if isinstance(payments_widget, str):
                                    payments_widget = json.loads(payments_widget)
                                payments_list = payments_widget.get("content", [])
                            except Exception:
                                raise UserError(
                                    f'Valor de payments_widget {factura_id.invoice_payments_widget} de factura {factura_id.name} con id {factura_id.id}')

                            for pay in payments_list:
                                if pay.get('date') == self.date and pay.get('account_payment_id') == pago.id:
                                    acumulado_factura += pay.get('amount', 0)
                                    facturas_ganancia.append(factura_id)
                                    if not self._is_credit_term(factura_id.invoice_payment_term_id.sudo()):
                                        ids_facturas.add(factura_id.id)
                    self.write({
                        'cierre_line_ids': [(1, item.id, {
                            'facturado': acumulado_factura + item.facturado,
                            'cobrado': pago.amount + item.cobrado if acumulado_factura == 0 else item.cobrado
                        })]
                    })
        self.register_list(list(ids_facturas), 'ids_facturas')
        for factura in facturas:
            if factura.payment_state == 'not_paid' and not self._is_credit_term(factura.invoice_payment_term_id.sudo()):
                self.write({
                    'facturas_ids': [(4, factura.id)]
                })

        for factura in facturas:
            if factura.id not in ids_facturas:
                if self._is_credit_term(factura.invoice_payment_term_id.sudo()):
                    for item in self.cierre_line_ids:
                        if item.credito:
                            self.write({
                                'cierre_line_ids': [(1, item.id, {
                                    'facturado': factura.amount_total_signed + item.facturado
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
        self.ensure_one()
        canales_ids = self._get_canales_ids()

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
            ('state', '!=', 'cancel'),
            ('state', '!=', 'draft'),
        ]
        facturas = self._search_facturas_by_team(facturas_domain, canales_ids)

        # Recorrer las facturas y sumar los totales
        total_ventas = sum(factura.amount_total for factura in facturas)
        
        promedio = total_ventas / dia
        self.write({
            'promedio_mensual': promedio
        })
            
    def procesar_promedio_anual(self):
        self.ensure_one()
        canales_ids = self._get_canales_ids()

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
            ('state', '!=', 'cancel'),
            ('state', '!=', 'draft'),
        ]
        facturas = self._search_facturas_by_team(facturas_domain, canales_ids)
        
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
