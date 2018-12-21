# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPickingLine(models.Model):
    _inherit = "stock.move"

    x_series = fields.Text(related = 'sale_line_id.x_series', string = "Series" )


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
