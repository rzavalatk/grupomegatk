# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Account(models.Model):
	_inherit = 'account.account'
	
	analytic_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica",)

class AccountMove(models.Model):
	_inherit = "account.move.line"

	@api.model_create_multi
	def create(self, vals_list):
		# Keep analytic optional: only preload a default analytic account when configured on the account.
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
					has_analytic = vals.get('analytic_distribution') or vals.get('analytic_account_id')
					if not has_analytic and account.analytic_id:
						if 'analytic_distribution' in self._fields:
							vals['analytic_distribution'] = {account.analytic_id.id: 100.0}
						elif 'analytic_account_id' in self._fields:
							vals['analytic_account_id'] = account.analytic_id.id
		return super(AccountMove, self).create(vals_list)
	




