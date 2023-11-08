# -*- encoding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime
from odoo.exceptions import Warning


class Quotationrfq(models.TransientModel):
    _name = 'rfq.diadema.wizard'
    _description = "description"

    def _get_prestamo(self):
        contexto = self._context
        if 'active_id' in contexto:
            loan_obj = self.env["comercial.loan.management"].browse(contexto['active_id'])
            return loan_obj

    def get_currency(self):
        return self.env.user.company_id.currency_id.id
    def get_total(self):
        self.monto_pagado_total = self.monto + self.mora_pagar


    partner_id = fields.Many2one("res.partner", "Proveedor", domain=[('supplier', '=', )])

    liquidar_capital = fields.Boolean("Liquidar Préstamo")
    #capital_prestamo = fields.Float("Capital de Prestamo", readonly=True, related="prestamo_id.total_capital")
    saldo_pendiente_prestamo = fields.Float("Saldo de Préstamo", readonly=True, related="prestamo_id.saldo_pendiente")

    # Mora de Prestamo
    currency_id = fields.Many2one("res.currency", "Moneda", domain=[('active', '=', True)], default=get_currency)