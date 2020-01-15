# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError

class Account(models.Model):
	_inherit = 'account.account'
	
	analytic_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica",)

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	@api.multi
	def cancel(self):
		if not self.invoice_ids:
			super(AccountPayment, self).cancel()
			for rec in self:
				for move in rec.move_line_ids.mapped('move_id'):
					moveline = self.env['account.move.line']
					line = moveline.search( [('move_id', '=', move.id)])
					line.unlink()
		else:
			message='Pago aplicado a Factura(s):'
			for x in self.invoice_ids:
				message +=  _(' %s, ') % \
        	(x.number)
			raise UserError(_(message))
			
		

class AccountInvoice(models.Model):
	_inherit = "account.move.line"

	@api.model
	def create(self,values):
		account = self.env['account.account'].browse(values['account_id'])
		if account.user_type_id.id == 16 or account.user_type_id.id == 17:
			if not 'analytic_account_id' in values:
				values['analytic_account_id']=account.analytic_id.id
			if not values['analytic_account_id']:
				if account.analytic_id:
					values['analytic_account_id']=account.analytic_id.id
				else:
					raise Warning(_('Cuenta analitica requerida en la linea con cuenta: '+ account.code+' '+account.name+' descripción: '+values['name']))
		
		return super(AccountInvoice, self).create(values)
