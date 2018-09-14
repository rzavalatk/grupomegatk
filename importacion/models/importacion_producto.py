# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.addons import decimal_precision as dp

class ImportacionProducto(models.Model):
	_name='import.product.mega'

	name = fields.Char(string="Name")
	descripcion = fields.Char("Descripción")
	stock_pick_ids = fields.Many2many(comodel_name="stock.picking",relation="x_stockpicking_impor_product_mega",column1="stock_picking_id",column2="import_mega_id",string="Recepciones")
	import_line_id = fields.One2many("import.product.mega.line.purchase", "import_product_id", "Detalle de transferencia")
	import_gsto_id = fields.One2many("import.product.mega.line.gasto", "import_product_id", "Detalle de transferencia")
	currency_id = fields.Many2one("res.currency", "Moneda", domain=[('active', '=', True)])
	company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, readonly=True, default=lambda self: self.env.user.company_id)

	@api.multi
	@api.onchange('stock_pick_ids')
	def _onchange_stock_pick_ids(self):
		recepciones=self.stock_pick_ids
		ponderaciones = self.env["import.product.mega.line.purchase"]
		dict_invoices = {}
		self.import_line_id = False
		for recepcion in recepciones:
			lineas_recesion = self.env['stock.move'].search([('picking_id','=',recepcion.id)])
			for lineas in lineas_recesion:
				vals = {
						'import_product_id': self.id,
						'product_id': lineas.product_id.id,
						'name': lineas.name,
						'price_unit': 1,
						'price_subtotal': 1,
						'currency_id': self.currency_id.id,
						'quantity': lineas.quantity_done,
						'company_id': self.company_id.id,}
				ponderaciones.new(vals)

	
	@api.constrains('name')
	def check_name(self):
		if not self.name:
			raise exceptions.UserError("cuidado1")

class LinePurchaseImport(models.Model):
	_name = 'import.product.mega.line.purchase'

	import_product_id = fields.Many2one('import.product.mega', string='Impor Product Reference', index=True, required=True, ondelete='cascade')
	product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', index=True)
	name = fields.Text(string='Description', required=True)
	price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
	price_subtotal = fields.Monetary(string='Amount', store=True, readonly=True, compute='_compute_price', help="Total amount without taxes")
	currency_id = fields.Many2one('res.currency', related='import_product_id.currency_id', store=True, related_sudo=False)
	quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
	company_id = fields.Many2one('res.company', string='Company', related='import_product_id.company_id', store=True, readonly=True, related_sudo=False)	

	def _compute_price(self):
			currency = self.import_product_id and self.import_product_id.currency_id or None
			price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
			taxes = False
			if self.invoice_line_tax_ids:
					taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.import_product_id.partner_id)
			self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
			self.price_total = taxes['total_included'] if taxes else self.price_subtotal
			if self.import_product_id.currency_id and self.import_product_id.currency_id != self.import_product_id.company_id.currency_id:
					price_subtotal_signed = self.import_product_id.currency_id.with_context(date=self.import_product_id._get_currency_rate_date()).compute(price_subtotal_signed, self.import_product_id.company_id.currency_id)
			sign = self.import_product_id.type in ['in_refund', 'out_refund'] and -1 or 1
			self.price_subtotal_signed = price_subtotal_signed * sign

	@api.onchange('product_id')
	def check_name(self):
			self.name = self.product_id.name
			print(self.product_id.id)



class LinePurchaseImport(models.Model):
	_name = 'import.product.mega.line.gasto'

	import_product_id = fields.Many2one('import.product.mega', string='Impor Product Reference', index=True, required=True, ondelete='cascade')
	partner_id = fields.Many2one('import.gasto.mega', 'Empresa')
	name = fields.Char('Descripción')
	amount = fields.Float('Monto', required=True)


		
