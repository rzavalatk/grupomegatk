# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Account_invoice(models.Model):
    _inherit = "account.invoice"

    x_comision = fields.Selection([('1','SI'),('2','NO')], string='Comisión Pagada', required=True, default='2')
