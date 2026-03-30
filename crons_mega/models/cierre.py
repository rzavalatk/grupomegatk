# -*- coding: utf-8 -*-
from logging import config

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
        region_map = {
            'San Pedro Sula': ['San Pedro Sula', 'SPS'],
            'Tegucigalpa': ['Tegucigalpa', 'TGU'],
        }
        return region_map.get(self.region, [self.region])

    def _get_canales_ids(self):
        if self.region == self.regions_list[1][0]:
            return [35, 36, 37, 38, 39, 45, 47, 53]
        if self.region == self.regions_list[0][0]:
            return [43, 41, 46, 58, 44]
        return [50, 49]

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
        journal_ids = self.env['account.cierre.config'].sudo().get_journal_ids(
            self.company_id.id)

        _logger.warning(
            "iniciar_cierre (company_id=%s): journal_ids desde config=%s",
            self.company_id.id,
            journal_ids,
        )
        
        config = self.env['account.cierre.config'].search([('company_id', '=', self.company_id.id)])
        _logger.warning(f"Configuración encontrada para company_id={self.company_id.id}: {config}")
        
        journals = self.env['account.journal'].search([
        ('company_id', '=', self.company_id.id),
        ('type', 'in', ['bank', 'cash'])])

        _logger.warning(f"Diarios de tipo 'bank' o 'cash' para company_id={self.company_id.id}: {[j.name for j in journals]}")
        
        if not journal_ids:
            journal_names = [
                'Efectivo',
                'Cheques',
                'Transferencia',
                'Tarjeta de Credito',
                'Tarjeta de Crédito',
                'Pendiente de Deposito',
                'Pendiente de Depósito',
            ]
            journal_ids = self.env['account.journal'].sudo().search([
                ('company_id', '=', self.company_id.id),
                ('name', 'in', journal_names),
            ]).ids

        if not journal_ids:
            journal_ids = self.env['account.journal'].sudo().search([
                ('company_id', '=', self.company_id.id),
                ('type', 'in', ['bank', 'cash']),
            ]).ids

        if not journal_ids:
            _logger.warning(
                "iniciar_cierre (company_id=%s): no se encontraron diarios para crear lineas de cierre.",
                self.company_id.id,
            )
        else:
            journal_names = self.env['account.journal'].sudo().browse(journal_ids).mapped('name')
            _logger.warning(
                "iniciar_cierre (company_id=%s): diarios finales para cierre=%s",
                self.company_id.id,
                journal_names,
            )

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
        canales_ids = self._get_canales_ids()
        region_values = self._get_region_values()

        # FIX Odoo 18: 'state' en account.payment es campo computed no almacenado;
        # hay que filtrar por move_id.state para que el ORM haga el JOIN correctamente.
        pagos = self.env['account.payment'].sudo().search([
            ('date', '=', self.date),
            ('company_id', '=', self.company_id.id),
            ('region', 'in', region_values),
            ('partner_type', '=', 'customer'),
            ('move_id.state', '=', 'posted'),
        ])

        # Diagnóstico: si sigue en 0, loguear cuántos hay sin cada filtro para aislar cuál falla.
        if not pagos:
            pagos_sin_state = self.env['account.payment'].sudo().search([
                ('date', '=', self.date),
                ('company_id', '=', self.company_id.id),
                ('region', 'in', region_values),
                ('partner_type', '=', 'customer'),
            ])
            pagos_sin_partner = self.env['account.payment'].sudo().search([
                ('date', '=', self.date),
                ('company_id', '=', self.company_id.id),
                ('region', 'in', region_values),
                ('move_id.state', '=', 'posted'),
            ])
            pagos_solo_fecha = self.env['account.payment'].sudo().search([
                ('date', '=', self.date),
                ('company_id', '=', self.company_id.id),
                ('region', 'in', region_values),
            ])
            _logger.warning(
                "DIAG pagos (company=%s, region=%s, date=%s): "
                "con_todos_filtros=0 | sin_state=%s | sin_partner_type=%s | solo_fecha_company_region=%s",
                self.company_id.id, self.region, self.date,
                len(pagos_sin_state), len(pagos_sin_partner), len(pagos_solo_fecha),
            )
            for p in pagos_solo_fecha[:10]:
                _logger.warning(
                    "  pago id=%s region=%s partner_type=%s move_state=%s date=%s amount=%s journal=%s",
                    p.id, p.region, p.partner_type, p.move_id.state, p.date, p.amount, p.journal_id.name,
                )

        self.register_ids(pagos, 'pagos')

        facturas = self.env['account.move'].sudo().search([
            ('invoice_date', '=', self.date),
            ('company_id', '=', self.company_id.sudo().id),
            ('team_id', 'in', canales_ids),
            ('move_type', '=', 'out_invoice'),
            ('state', 'not in', ('cancel', 'draft')),
        ])
        self.register_ids(facturas, 'facturas')

        _logger.warning(f"La region es {self.region}")
        _logger.warning(f"Iniciando cierre")
        _logger.warning(f"Canales ids: {canales_ids}")
        _logger.warning(f"Total de pagos encontrados: {len(pagos)}")
        _logger.warning(f"Total de facturas encontradas: {len(facturas)}")

        ids_facturas = set()
        facturas_ganancia = self.env['account.move']

        for pago in pagos:
            _logger.warning(f"Pago id={pago.id} journal={pago.journal_id.name} amount={pago.amount}")

            # Buscar la línea de diario correspondiente (excluir línea de crédito)
            journal_id_pago = pago.journal_id.id
            diario_linea = self.cierre_line_ids.filtered(
                lambda l, jid=journal_id_pago: not l.credito and l.journal_id.id == jid
            )[:1]
            if not diario_linea:
                _logger.warning(
                    "  Diario '%s' no estaba en cierre_line_ids; se crea linea dinamica para no perder el pago.",
                    pago.journal_id.name,
                )
                diario_linea = self.env['account.cierre.line'].sudo().create({
                    'cierre_id': self.id,
                    'journal_id': pago.journal_id.id,
                })

            # FIX Odoo 18: usar reconciled_invoice_ids en lugar de move_id.ids
            facturas_del_pago = pago.reconciled_invoice_ids.sudo().filtered(
                lambda f: f.move_type == 'out_invoice'
                and f.state not in ('cancel', 'draft')
                and f.company_id.id == self.company_id.id
                and f.team_id.id in canales_ids
            )
            # Sólo facturas de HOY → van a "Facturado"
            fecha_str = str(self.date)
            facturas_hoy = facturas_del_pago.filtered(
                lambda f, fs=fecha_str: str(f.invoice_date) == fs
            )
            _logger.warning(f"  reconciliadas region={len(facturas_del_pago)}, hoy={len(facturas_hoy)}")

            acumulado_factura = 0

            if facturas_hoy:
                for factura_id in facturas_hoy:
                    payments_widget = factura_id.invoice_payments_widget or {}
                    payments_list = (
                        payments_widget.get("content", [])
                        if isinstance(payments_widget, dict) else []
                    )
                    for pay in payments_list:
                        pay_id_match = (
                            (pay.get('account_payment_id') and pay.get('account_payment_id') == pago.id)
                            or (pay.get('move_id') and pay.get('move_id') == pago.move_id.id)
                        )
                        if str(pay.get('date') or '') == fecha_str and pay_id_match:
                            acumulado_factura += pay.get('amount') or 0
                            ids_facturas.add(factura_id.id)
                            facturas_ganancia |= factura_id

                # Fallback: widget no devolvió match pero sí hay facturas reconciliadas de hoy
                if acumulado_factura == 0:
                    acumulado_factura = pago.amount
                    for factura_id in facturas_hoy:
                        ids_facturas.add(factura_id.id)
                        facturas_ganancia |= factura_id
                    _logger.warning(f"  Widget sin match, usando pago.amount={pago.amount} como fallback")

                diario_linea.write({
                    'facturado': diario_linea.facturado + acumulado_factura,
                })

                # Si el pago excede lo facturado hoy, el remanente corresponde a CxC antigua.
                remanente_cxc = (pago.amount or 0.0) - (acumulado_factura or 0.0)
                if remanente_cxc > 0:
                    diario_linea.write({
                        'cobrado': diario_linea.cobrado + remanente_cxc,
                    })
            else:
                # Pago para facturas antiguas (CXC) de esta región → "Cobrado CXC"
                diario_linea.write({
                    'cobrado': diario_linea.cobrado + pago.amount,
                })

        self.register_list(list(ids_facturas), 'ids_facturas')

        # Facturas al contado sin pago → registro de pendientes
        for factura in facturas:
            if factura.payment_state == 'not_paid' and factura.invoice_payment_term_id.sudo().name == 'Contado':
                self.write({'facturas_ids': [(4, factura.id)]})

        # Facturas no cobradas hoy → línea de crédito
        for factura in facturas:
            if factura.id not in ids_facturas:
                # Si no quedo marcada en ids_facturas pero ya tiene pagos, no mandarla a credito.
                if factura.payment_state in ('not_paid', 'partial') and factura.amount_residual == factura.amount_total:
                    if factura.invoice_payment_term_id.sudo().name != 'Contado':
                        for item in self.cierre_line_ids:
                            if item.credito:
                                item.write({
                                    'facturado': item.facturado + factura.amount_total_signed,
                                })
                                break

        ganancia_total = 0
        for factura in facturas_ganancia:
            costo_total = sum(
                line.product_id.standard_price * line.quantity
                for line in factura.invoice_line_ids
            )
            ganancia_factura = factura.amount_total - costo_total
            ganancia_total += ganancia_factura
        self.ganancia_diaria = ganancia_total

        self.procesar_promedio_mensual()
        time.sleep(1)
        self.procesar_promedio_anual()

        self.write({'state': 'proccess'})
        
    def procesar_promedio_mensual(self):
        canales_ids = self._get_canales_ids()

        dia = self.date.day
        mes = self.date.month
        año = self.date.year
        
        #fecha para promedio mensual
        fecha_init_mensual = date(año, mes, 1)

        facturas = self.env['account.move'].sudo().search([
            '&',
            '&',
            '&',
            '&',
            '&',
            '&',
            ('invoice_date', '>=', fecha_init_mensual),
            ('invoice_date', '<=', self.date),
            ('company_id', '=', self.company_id.sudo().id),
            ('team_id', 'in', canales_ids),
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel'),
            ('state', '!=', 'draft'),
        ])

        # Recorrer las facturas y sumar los totales
        total_ventas = sum(factura.amount_total for factura in facturas)
        
        promedio = total_ventas / dia
        self.write({
            'promedio_mensual': promedio
        })
            
    def procesar_promedio_anual(self):
        canales_ids = self._get_canales_ids()

        dia = self.date.day
        mes = self.date.month
        año = self.date.year

        #fecha para el promedio anual
        fecha_init_anual = date(año, 1, 1)

        facturas = self.env['account.move'].sudo().search([
            '&',
            '&',
            '&',
            '&',
            '&',
            '&',
            ('invoice_date', '>=', fecha_init_anual),
            ('invoice_date', '<=', self.date),
            ('company_id', '=', self.company_id.sudo().id),
            ('team_id', 'in', canales_ids),
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel'),
            ('state', '!=', 'draft'),
        ])
        
        # Recorrer las facturas y sumar los totales
        total_ventas = sum(factura.amount_total for factura in facturas)
        
        promedio = total_ventas / mes
        self.write({
            'promedio_anual': promedio
        })
                   
    def send_email(self, email, cc=""):
        if not email:
            _logger.warning("send_email (cierre %s): email_to vacío, se omite envío.", self.id)
            return False
        template = self.env.ref(
            'crons_mega.email_template_cierre_diario_1', raise_if_not_found=False)
        if not template:
            _logger.error("send_email (cierre %s): template 'email_template_cierre_diario_1' no encontrada.", self.id)
            return False
        email_values = {
            'email_from': 'megatk.no_reply@megatk.com',
            'email_to': email,
            'email_cc': cc or '',
        }
        try:
            template.send_mail(self.id, email_values=email_values, force_send=True)
            self.write({'state': 'done'})
        except Exception as e:
            _logger.error("send_email (cierre %s) falló al enviar a '%s': %s", self.id, email, e)
            return False
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
                principal_emails = "lmoran@megatk.com,jmoran@meditekhn.com,dvasquez@megatk.com,erodriguez@megatk.com"
                cc_mega = "yalvarado@megatk.com"
                cc_meditek = "nfuentes@meditekhn.com"
                # principal_emails = "areyes@megatk.com"
                # cc_mega = "areyes@megatk.com"
                # cc_meditek = "areyes@megatk.com"
                cierre = self.sudo().browse(i)
                cierre.iniciar_cierre()
                time.sleep(1)
                cierre.procesar_cierre()
                time.sleep(1)
                
                if cierre.company_id.sudo().id in [8, 12]:
                    time.sleep(1)
                    if cierre.sudo().region == 'San Pedro Sula':
                        cc_mega += ",vmoran@megatk.com"
                        cc_meditek += "dgarcia@meditekhn.com"
                        # cc_mega += ",areyes@megatk.com"
                        # cc_meditek += "areyes@megatk.com"
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
