# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Account(models.Model):
	_inherit = 'account.account'
	
	analytic_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica",)

class AccountMove(models.Model):
	_inherit = "account.move.line"

	@api.model_create_multi
	def create(self, vals_list):
		config = self.env['res.config.settings']
		listcon = config.search([('company_id', '=', self.env.user.company_id.id)])
		acti = ""

		for anali in listcon:
			acti = anali.group_analytic_accounting

		if acti:
			for vals in vals_list:
				account_id = vals.get('account_id')
				if account_id:
					account = self.env['account.account'].browse(account_id)
					# En Odoo 16 ya no existe user_type_id; se usa account_type
					if account.account_type in ('asset_receivable', 'liability_payable'):
						if not vals.get('analytic_account_id'):
							if account.analytic_id:
								vals['analytic_account_id'] = account.analytic_id.id
							else:
								raise UserError(_(
									'Cuenta analítica requerida en la línea con cuenta: %s %s descripción: %s'
								) % (account.code, account.name, vals.get('name', '')))
		return super(AccountMove, self).create(vals_list)
	




