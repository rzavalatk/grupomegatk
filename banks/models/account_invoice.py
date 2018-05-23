# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    numero_factura = fields.Char('Número de factura', help='Número de factura')
    cai_suplidor = fields.Char("CAI de Proveedor")