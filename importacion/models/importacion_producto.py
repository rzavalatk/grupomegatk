# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.addons import decimal_precision as dp

class ImportacionProducto(models.Model):
	_name='import.product.mega'
	_order = "name desc"

	name = fields.Char(string="Name")
	descripcion = fields.Char("Descripción")
	stock_pick_ids = fields.Many2many(comodel_name="stock.picking",relation="x_stockpicking_impor_product_mega",column1="stock_picking_id",column2="import_mega_id",string="Transferencias",required=True,)
	import_line_id = fields.One2many("import.product.mega.line.purchase", "import_product_id", "Detalle de transferencia")
	import_gsto_id = fields.One2many("import.product.mega.line.gasto", "import_product_id", "Detalle de transferencia")
	currency_id = fields.Many2one('res.currency', 'Moneda', default=lambda self: self.env.user.company_id.currency_id.id)
	company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, default=lambda self: self.env.user.company_id)
	amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='always')
	amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
	amount_total = fields.Monetary(string='Total Facturación', store=True, readonly=True, compute='_amount_all')
	costo_id = fields.One2many("product.ponderacion", "ponderacion_id", "Ponderación por productos")

	amount_total_gasto = fields.Monetary(string='Total Gasto', store=True, readonly=True, compute='_amount_gasto')
	state = fields.Selection( [('draft', 'Borrador'), ('validado', 'Validado'), ('cancelado', 'Cancelado')], string="Estado", default='draft')
	sequence_id = fields.Many2one('ir.sequence', "Fiscal Number")

	total = fields.Float(string='Total', store=True, readonly=True,)
	porcentaje = fields.Float(string='Ponderación %', store=True, readonly=True,)

	res_parner_id = fields.Many2one('res.partner', string='Agente aduanero',domain=[('supplier','=',True), ])
	res_country = fields.Many2one('res.country', string='Pais',)
	res_country_state = fields.Many2one('res.country.state', string='Estado',)

	transpor_medio = fields.Selection( [('aereo', 'Aéreo'), ('courier', 'Courier Express'), ('maritimo', 'Marítimo')], string="Transporte",)
	puerto = fields.Selection( [('hodumares', 'Hondumares'),('puertocortes','Puerto Cortés'), ('swissport', 'Swissport'), ('san_lorenzo', 'San Lorenzo')], string="Puerto",)
	incoterms = fields.Selection( [('exw','EXW'),('fca','FCA'),('fas','FAS'),('fob','FOB'),('cfr','CFR'),('cif','CIF'),('cpt','CPT'),('cip','CIP'),('dat','DAT'),('dap','DAP'),('ddp','DDP')], string='Incoterms')

	@api.multi
	def unlink(self):
		if not self.state == 'draft':
			raise Warning(_('No se puede borrar las ponderaciones validadas'))
		res = super(ImportacionProducto, self).unlink()
		return res

	@api.multi
	def cancelar_impor(self):
		if self.costo_id:
			for lis in self.costo_id:
				lis.unlink()
		self.write({'state': 'cancelado'})

	@api.multi
	def back_draft(self):
		if self.costo_id:
			for lis in self.costo_id:
				lis.unlink()
		recepciones=self.stock_pick_ids
		for recepcion in recepciones:
			recepcion.write({
				'ponderacion':False,
				})
		self.write({'state': 'draft'})

	@api.multi
	def validar(self):
		if not self.import_line_id:
			raise Warning(_('No existe detalle de facturación'))

		if not self.import_gsto_id:
			raise Warning(_('No existe detalle de gastos'))

		ponderaciones = self.env["import.product.mega"].search([('company_id','=',self.company_id.id)])
		for ponderacion in ponderaciones:
			if not ponderacion.sequence_id.id:
				obj_sequence = self.env["ir.sequence"].search([('company_id','=',self.company_id.id),('name','=','Ponderacion')])
				if not obj_sequence.id:
					values = {'name': 'Ponderacion',
                  		'prefix': 'POND. ',
                  		'company_id': self.company_id.id,
                  		'padding':8,}
					sequence_id = obj_sequence.create(values)
				else:
					sequence_id = obj_sequence	
				self.write({'sequence_id': sequence_id.id})

				new_name = self.sequence_id.with_context().next_by_id()
				self.write({'name': new_name})

				break
			else:
				self.write({'sequence_id': ponderacion.sequence_id.id})
				new_name = self.sequence_id.with_context().next_by_id()
				self.write({'name': new_name})
				break
		
		self.total =  self.amount_total_gasto + self.amount_total
		self.porcentaje = 100 * (self.amount_total_gasto / self.amount_total)

		recepciones = self.stock_pick_ids
		for recepcion in recepciones:
			recepcion.write({
				'ponderacion':True,
				})

		line = self.import_line_id
		for product in line:
			producto = product.product_id
			costo_real = product.price_unit + (product.price_unit * (self.amount_total_gasto / self.amount_total)) 
			ponderacion_producto = self.porcentaje
			producto.write({
				'x_costo_real':costo_real,
				'x_ponderacion':ponderacion_producto,
				})
			obj_precio = self.env["product.ponderacion"]
			valores = {
            	'product_id': producto.id,
            	'ponderacion_id': self.id,
            	'fecha_recepcion': product.fecha_done,
            	'ponderacion': ponderacion_producto,
            	'costo_real': costo_real,
            }
			id_precio = obj_precio.create(valores)
		self.write({'state': 'validado'})



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
				subtotal = lineas.quantity_done * lineas.price_unit
				tax = subtotal * lineas.tax_id.amount / 100
				total = tax + subtotal
				print(lineas.date)
				vals = {
						'import_product_id': self.id,
						'product_id': lineas.product_id.product_tmpl_id.id,
						'name': lineas.name,
						'price_total': total,
						'price_tax': tax,
						'taxes_id': lineas.tax_id,
						'price_unit': lineas.price_unit,
						'price_subtotal': subtotal,
						'currency_id': self.currency_id.id,
						'quantity': lineas.quantity_done,
						'company_id': self.company_id.id,
						'fecha_done': lineas.date,}
				ponderaciones.new(vals)

	@api.depends('import_line_id.price_total')
	def _amount_all(self):
		for order in self:
			amount_untaxed = amount_tax = 0.0
			for line in order.import_line_id:
				amount_untaxed += line.price_subtotal
				amount_tax += line.price_tax
			order.update({
				'amount_untaxed': order.currency_id.round(amount_untaxed),
				'amount_tax': order.currency_id.round(amount_tax),
				'amount_total': amount_untaxed + amount_tax,
			})

	@api.depends('import_gsto_id.amount')
	def _amount_gasto(self):
		for order in self:
			amount_untaxed = 0.0
			for line in order.import_gsto_id:
				amount_untaxed += line.amount_hnl
			order.update({
				'amount_total_gasto': amount_untaxed,
			})
			for line in order.import_gsto_id:
				if line.amount_hnl:
					line.update({'porcentaje':line.amount_hnl/self.amount_total_gasto})
	
class LinePurchaseImport(models.Model):
	_name = 'import.product.mega.line.purchase'

	import_product_id = fields.Many2one('import.product.mega', string='Impor Product Reference', index=True, required=True, ondelete='cascade')
	name = fields.Text(string='Descripción', required=True)
	origin = fields.Char(string='Source Document', help="Reference of the document that produced this invoice.")
	product_id = fields.Many2one('product.template', string='Producto', ondelete='restrict', index=True)
	price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('P.U.'))

	price_subtotal = fields.Monetary(string='Subtotal', store=True)
	price_total = fields.Monetary(string='Total', store=True)
	price_tax = fields.Float(string='ISV', store=True)

	fecha_done = fields.Datetime(string='Fecha Validado',)
	quantity = fields.Float(string='Cantidad', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)

	taxes_id = fields.Many2many('account.tax', string='ISV', domain=['|', ('active', '=', False), ('active', '=', True)])
	company_id = fields.Many2one('res.company', string='Compañia', related='import_product_id.company_id', store=True, readonly=True, related_sudo=False)
	currency_id = fields.Many2one('res.currency', related='import_product_id.currency_id', readonly=True, related_sudo=False)

class LinePurchaseImport(models.Model):
	_name = 'import.product.mega.line.gasto'

	import_product_id = fields.Many2one('import.product.mega', string='Impor Product Reference', index=True, required=True, ondelete='cascade')
	gasto_id = fields.Many2one('import.gasto.mega', 'Gasto')
	name = fields.Char('Descripción')
	amount = fields.Monetary('Monto', required=True,)
	amount_hnl = fields.Float('Monto')
	currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=lambda self: self.env.user.company_id.currency_id.id)
	porcentaje = fields.Float(string='%') 
		
	@api.onchange('amount','currency_id')
	def _onchange_amount(self):
		self.amount_hnl= self.amount / self.currency_id.rate

