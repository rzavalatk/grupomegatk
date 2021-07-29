# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	@api.multi
	def unlink(self):
		for line in self:
			if line.state == 'done':
				raise UserError(_('No se puede eliminar un movimiento de inventario validado'))
			return super(StockPicking, self).unlink()

	@api.multi
	def button_validate(self):
		message=''
		if self.picking_type_id.code == 'internal' or self.picking_type_id.code == 'outgoing':
			for move in self.move_lines:
				for line in move.move_line_ids:
					stock_quant = self.env['stock.quant'].search([('product_id.id', '=', line.product_id.id),('location_id.id','=',self.location_id.id)])
					if stock_quant:
						if stock_quant.quantity < line.qty_done:
							if stock_quant.quantity > 0:
								message +=  _('\nPlanea vender %s Unidad(es) de %s pero solo tiene %s Unidad(es) disponible(s) en el almacén %s.') % \
									(line.qty_done, line.product_id.name, stock_quant.quantity, self.location_id.name)
							if stock_quant.quantity <= 0:
								message += ('\nPlanea vender %s Unidad(es) de %s pero no tiene cantidades disponible(s) en el almacén %s.') % \
									(line.qty_done, line.product_id.name, self.location_id.name)
					else:
						message += ('\nPlanea vender %s Unidad(es) de %s pero no tiene cantidades disponible(s) en el almacén %s.') % \
								(line.qty_done, line.product_id.name, self.location_id.name)
			if message != '':
				raise UserError(_(message))
		return super(StockPicking, self).button_validate()

	@api.multi
	def button_borrador(self):
		self.write({'state': 'draft'})
		for move in self.move_lines:
			 move.write({'state': 'draft'})

#class StockMoveLine(models.Model):
 #   _inherit = "stock.move.line"
#
 #   @api.multi
  #  def unlink(self):
   # 	for x in self:
	#        if x.move_id.picking_type_id.code == 'outgoing' and x.product_id.type=='product':
	 #           x.write({'state': 'confirmed'})
	  #          Quant = self.env['stock.quant'].search([('product_id','=',x.product_id.id),('location_id','=',x.location_id.id)])
	   #         if Quant:
		#            Quant.write({'quantity': x.qty_done + Quant.quantity})
		 #       else:
		  #          valores = {
		   #             'product_id': x.product_id.id,
			#            'product_tmpl_id': x.product_id.product_tmpl_id.id,
			 #           'location_id': x.location_id.id,
			  #          'quantity': x.qty_done,
			   #         'reserved_quantity': 0,
				#        'company_id': self.env.user.company_id.id,
				 #       }
				  #  Quant.create(valores)
			#elif x.move_id.picking_type_id.code == 'incoming' and x.product_id.type=='product':
			 #   x.write({'state': 'confirmed'})
			  #  Quant = self.env['stock.quant'].search([('product_id','=',x.product_id.id),('location_id','=',x.location_dest_id.id)])
			   # if Quant:
				#    if Quant.quantity < x.qty_done:
				 #       message = ('El item %s resultaría negativo') % \
				  #          (x.product_id.name)
				   #     raise UserError(_(message))
					#if Quant.quantity > 0:
					 #   Quant.write({'quantity': Quant.quantity - x.qty_done })
		#return super(StockMoveLine, self).unlink()


class StockPickingLine(models.Model):
	_inherit = "stock.move"

	x_series = fields.Text(related = 'sale_line_id.x_series', string = "Series" )
	x_codigo = fields.Char(related='product_id.barcode', string="Codigo")

	#@api.multi
	#def _action_cancel(self):
	 #   for x in self:
	  #      if x.state == 'done' and x.picking_type_id.code != 'internal':
	   #         x.write({'state': 'confirmed'})
		#        x.sale_line_id.write({'qty_delivered': 0})
		#return super(StockPickingLine, self)._action_cancel()

class Stock(models.Model):
	_inherit = "stock.warehouse"

	x_ubicacion = fields.Selection([('1','NIC'),('2','SPS'),('3','TGU')], string='Ubicación')

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	@api.onchange('partner_id')
	def _default_warehouse_i(self):
		company = self.env.user.company_id.id
		warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company),('x_ubicacion','=',self.env.user.ubicacion_vendedor)], limit=1)
		if not warehouse_ids.name:
			warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
		self.warehouse_id = warehouse_ids