# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	#_rec_name = 'name_mostrar'
	#_description = "Configuracion y parametros de los prestamos"
	#_order = "name_mostrar desc"
	#_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

	account_id = fields.Many2one('account.account', 'Cuenta de desembolso', required=True, )
	account_redes_id = fields.Many2one('account.account', 'Cuenta de redescuento', required=True, )
	recibir_pagos = fields.Many2one("account.journal", "Recibir pagos",  required=True, domain=[('type','=','bank'), ])
	producto_gasto_id = fields.Many2one('product.product', string='Cuenta de gasto', required=True, domain=[('sale_ok', '=', True)],)
	producto_interes_id = fields.Many2one('product.product', string='Cuenta de interes', required=True,  domain=[('sale_ok', '=', True)],)
	interes_id = fields.Many2one("account.account", "Recibir depósito", required=True, domain="[ ('user_type_id.type', '=', 'other')]")



	@api.model
	def get_values(self):
		res = super(ResConfigSettings, self).get_values()
		res.update(
			account_id=float(self.env['ir.config_parameter'].sudo().get_param('prestamos.account_id')),
			account_redes_id=float(self.env['ir.config_parameter'].sudo().get_param('prestamos.account_redes_id')),
			recibir_pagos=float(self.env['ir.config_parameter'].sudo().get_param('prestamos.recibir_pagos')),
			producto_gasto_id=float(self.env['ir.config_parameter'].sudo().get_param('prestamos.producto_gasto_id')),
			producto_interes_id=float(self.env['ir.config_parameter'].sudo().get_param('prestamos.producto_interes_id')),
			interes_id=float(self.env['ir.config_parameter'].sudo().get_param('prestamos.interes_id'))

		)
		return res
		
	@api.multi
	def set_values(self):
		super(ResConfigSettings, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param('prestamos.account_id', self.account_id.id)
		self.env['ir.config_parameter'].sudo().set_param('prestamos.account_redes_id', self.account_redes_id.id)
		self.env['ir.config_parameter'].sudo().set_param('prestamos.recibir_pagos', self.recibir_pagos.id)
		self.env['ir.config_parameter'].sudo().set_param('prestamos.producto_gasto_id', self.producto_gasto_id.id)
		self.env['ir.config_parameter'].sudo().set_param('prestamos.producto_interes_id', self.producto_interes_id.id)
		self.env['ir.config_parameter'].sudo().set_param('prestamos.interes_id', self.interes_id.id)