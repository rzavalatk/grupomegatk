# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def unlink(self):
        if self.state == 'done':
            raise UserError(_('No se puede eliminar un movimiento de inventario validado'))
        return super(StockPicking, self).unlink()


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.multi
    def unlink(self):
    	for x in self:
            if x.move_id.picking_type_id.code == 'outgoing':
                x.write({'state': 'confirmed'})
                Quant = self.env['stock.quant'].search([('product_id','=',x.product_id.id),('location_id','=',x.location_id.id)])
                Quant.write({'quantity': x.qty_done + Quant.quantity})
    	return super(StockMoveLine, self).unlink()


class StockPickingLine(models.Model):
    _inherit = "stock.move"

    x_series = fields.Text(related = 'sale_line_id.x_series', string = "Series" )

    @api.multi
    def _action_cancel(self):
    	for x in self:
            if x.state == 'done' and x.picking_type_id.code == 'outgoing':
                x.write({'state': 'confirmed'})
                x.sale_line_id.write({'qty_delivered': 0})
    	return super(StockPickingLine, self)._action_cancel()

class Stock(models.Model):
    _inherit = "stock.warehouse"

    x_ubicacion = fields.Selection([('1','NIC'),('2','SPS'),('3','TGU')], string='Ubicación')

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	@api.model
	def _default_warehouse_i(self):
		company = self.env.user.company_id.id
		warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company),('x_ubicacion','=',self.env.user.ubicacion_vendedor)], limit=1)
		if not warehouse_ids.name:
			warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
		return warehouse_ids

	warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, default=_default_warehouse_i)
