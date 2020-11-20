# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResCompany(models.Model):
	_inherit = "res.company"

	account_sale_tax_id = fields.Many2one('account.tax', string="Default Sale Tax")
	account_purchase_tax_id = fields.Many2one('account.tax', string="Default Purchase Tax")
