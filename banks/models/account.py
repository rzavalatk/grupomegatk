# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError

class Account(models.Model):
	_inherit = 'account.account'
	
	analytic_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica",)

class AccountMove(models.Model):
	_inherit = "account.move.line"

	@api.model
	def create(self,values):
		config = self.env['res.config.settings']
		listcon = config.search([('company_id','=',self.env.user.company_id.id)])
		acti = ""

		for anali in listcon:
			acti = anali.group_analytic_accounting
    	
		if acti:
			account_id = values.get('account_id')
			if account_id:
				account = self.env['account.account'].browse(account_id)
				if account.user_type_id.id == 16 or account.user_type_id.id == 17:
					if 'analytic_account_id' not in values or not values['analytic_account_id']:
						if account.analytic_id:
							values['analytic_account_id'] = account.analytic_id.id
						else:
							raise Warning(_('Cuenta analítica requerida en la línea con cuenta: ' + account.code + ' ' + account.name + ' descripción: ' + values['name']))
		
		return super(AccountMove, self).create(values)
	




