# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountInvoice(models.Model):
	_inherit = "account.move"

	numero_factura = fields.Char('Número de factura', help='Número de factura')
	cai_proveedor = fields.Char("Cai Proveedor")