# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	def unlink(self):
		for line in self:
			if line.state == 'done':
				raise UserError(_('No se puede eliminar un movimiento de inventario validado'))
			return super(StockPicking, self).unlink()

	def button_validate(self):
		message=''
		if self.picking_type_id.code == 'internal' or self.picking_type_id.code == 'outgoing':
			for move in self.move_ids:
				for line in move.move_line_ids:
					stock_quant = self.env['stock.quant'].search([('product_id.id', '=', line.product_id.id),('location_id.id','=',self.location_id.id)])
					if stock_quant:
						if stock_quant.quantity < line.quantity:
							if stock_quant.quantity > 0:
								message +=  _('\nPlanea vender %s Unidad(es) de %s pero solo tiene %s Unidad(es) disponible(s) en el almacén %s.') % \
									(line.quantity, line.product_id.name, stock_quant.quantity, self.location_id.name)
							if stock_quant.quantity <= 0:
								message += ('\nPlanea vender %s Unidad(es) de %s pero no tiene cantidades disponible(s) en el almacén %s.') % \
									(line.quantity, line.product_id.name, self.location_id.name)
					else:
						message += ('\nPlanea vender %s Unidad(es) de %s pero no tiene cantidades disponible(s) en el almacén %s.') % \
								(line.quantity, line.product_id.name, self.location_id.name)
			if message != '':
				raise UserError(_(message))
		return super(StockPicking, self).button_validate()

	def button_borrador(self):
		self.write({'state': 'draft'})
		for move in self.move_ids:
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

class Stock(models.Model):
	_inherit = "stock.warehouse"

	x_ubicacion = fields.Selection([('1','NIC'),('2','SPS'),('3','TGU')], string='Ubicación')

	@api.model_create_multi
	def create(self, vals_list):
		warehouses = super().create(vals_list)
		warehouses._sync_related_company_ids()
		return warehouses

	def write(self, vals):
		result = super().write(vals)
		if not self.env.context.get('skip_company_sync'):
			self._sync_related_company_ids()
		return result

	def _sync_related_company_ids(self, company=False):
		picking_type_model = self.env['stock.picking.type']
		warehouse_location_fields = [
			'view_location_id',
			'lot_stock_id',
			'wh_input_stock_loc_id',
			'wh_qc_stock_loc_id',
			'wh_output_stock_loc_id',
			'wh_pack_stock_loc_id',
		]
		location_fields = [
			field_name
			for field_name, field in picking_type_model._fields.items()
			if getattr(field, 'comodel_name', None) == 'stock.location'
		]

		for warehouse in self.sudo():
			target_company = warehouse.company_id or company
			if target_company and not getattr(target_company, '_name', False):
				target_company = self.env['res.company'].browse(target_company)
			if not target_company:
				continue

			picking_types = picking_type_model.search([('warehouse_id', '=', warehouse.id)])
			locations = self.env['stock.location']
			for field_name in warehouse_location_fields:
				if field_name in warehouse._fields:
					locations |= warehouse[field_name]
			for field_name in location_fields:
				locations |= picking_types.mapped(field_name)
			sequences = picking_types.mapped('sequence_id')

			for records in (locations, picking_types, sequences):
				records_to_fix = records.filtered(
					lambda record: 'company_id' in record._fields and record.company_id != target_company
				)
				if records_to_fix:
					records_to_fix.with_context(skip_company_sync=True).write({'company_id': target_company.id})
					_logger.info(
						"Synchronized company_id to %s for %s linked to warehouse %s",
						target_company.display_name,
						records_to_fix._name,
						warehouse.display_name,
					)


class StockPickingType(models.Model):
	_inherit = "stock.picking.type"

	@api.model_create_multi
	def create(self, vals_list):
		if not self.env.context.get('skip_company_sync'):
			for vals in vals_list:
				warehouse = False
				target_company = False
				warehouse_id = vals.get('warehouse_id')
				if warehouse_id:
					warehouse = self.env['stock.warehouse'].browse(warehouse_id).exists()

				company_id = vals.get('company_id')
				if warehouse and warehouse.company_id:
					target_company = warehouse.company_id
					if company_id != target_company.id:
						vals['company_id'] = target_company.id
				elif company_id:
					target_company = self.env['res.company'].browse(company_id)

				if warehouse:
					warehouse._sync_related_company_ids(company=target_company)

				if target_company:
					for field_name, field in self._fields.items():
						if getattr(field, 'comodel_name', None) != 'stock.location':
							continue
						location_id = vals.get(field_name)
						if not location_id:
							continue
						location = self.env['stock.location'].browse(location_id).exists()
						if location and location.company_id != target_company:
							location.sudo().with_context(skip_company_sync=True).write({
								'company_id': target_company.id,
							})

		picking_types = super().create(vals_list)
		if not self.env.context.get('skip_company_sync'):
			picking_types.mapped('warehouse_id')._sync_related_company_ids()
		return picking_types

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	@api.onchange('partner_id')
	def _default_warehouse_i(self):
		company = self.env.user.company_id.id
		warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company),('x_ubicacion','=',self.env.user.ubicacion_vendedor)], limit=1)
		if not warehouse_ids.name:
			warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
		self.warehouse_id = warehouse_ids