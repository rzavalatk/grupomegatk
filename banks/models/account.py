# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning

class AccountInvoice(models.Model):
    _inherit = "account.move.line"

    @api.model
    def create(self,values):
    	account = self.env['account.account'].browse(values['account_id'])
    	if (account.user_type_id.id == 16 or account.user_type_id.id == 17) and self.env.user.id!=1:
    		if not values['analytic_account_id']:
	    		raise Warning(_('Cuenta analitica requerida en la linea con cuenta: '+ account.code+' '+account.name+' descripción: '+values['name']))
    	return super(AccountInvoice, self).create(values)

