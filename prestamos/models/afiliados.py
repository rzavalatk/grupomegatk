# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.addons import decimal_precision as dp
import math

class Afiliados(models.Model):
	_name = 'prestamos.afiliados'
	_rec_name = 'name_mostrar'
	_description = "Prestamos Afiliados"
	_order = "name_mostrar desc"
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
	_sql_constraints = [
		('partner_unic', 'unique (res_partner_prov_id)', _('El afiliado debe ser unico')),
		('saldo_inicial', 'unique (res_partner_prov_id)', _('El afiliado debe ser unico')),
	]

	@api.onchange("res_partner_prov_id")
	def onchangeafiliado(self):
		self.name_mostrar=self.res_partner_prov_id.name

	def _get_invoiced(self):
		y = len(set(self.payment_ids.ids))
		z = 0
		for invoice in self.invoice_cxc_ids:
			if(invoice.type == 'in_invoice'):
				z = z + 1
		self.invoice_count_cxp = z
		
	name_mostrar = fields.Char('Nombre', copy=False)
	res_partner_prov_id = fields.Many2one('res.partner', string='Afiliado', readonly=True, states={'draft': [('readonly', False)]},)
	cuenta = fields.Char('Numero de cuenta', copy=False, readonly=True, states={'draft': [('readonly', False)]},)
	currency_id = fields.Many2one('res.currency', 'Moneda', default=lambda self: self.env.user.company_id.currency_id.id, readonly=True, states={'draft': [('readonly', False)]},)
	imagen = fields.Binary(related='res_partner_prov_id.image', string="Imegen")
	company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, default=lambda self: self.env.user.company_id, readonly=True, states={'draft': [('readonly', False)]},)
	state = fields.Selection( [('draft', 'Borrador'), ('cancelado', 'Cancelado'),('validado', 'Validado'),], string="Estado", default='draft',copy=False, track_visibility='onchange', )

	active = fields.Boolean(string='Activo', default=True, )
	movimientos_line = fields.One2many("prestamos.afiliados.movimientos", "moviminetos_id", "Detalle de moviminetos")

	saldo_inicial = fields.Float(string='Ultimo depósito', copy=False, readonly=True, )
	saldo_real = fields.Float(string='Saldo real', compute='_credit_debit_get', copy=False, readonly=True, )
	fecha_apertura = fields.Date(string='Fecha de apertura', readonly=True, required=True, states={'draft': [('readonly', False)]},)
	
	user_id = fields.Many2one('res.users', string='Responsable', index=True,  default=lambda self: self.env.user,readonly=True, states={'draft': [('readonly', False)]},)
	invoice_cxc_ids = fields.Many2many("account.invoice", string='Facturas cxc', readonly=True, copy=False)
	invoice_count_cxp = fields.Integer(string='Factura Count', compute='_get_invoiced', readonly=True)
	payment_ids = fields.Many2many("account.payment", string="Pagos", copy=False,)

	pagos_id = fields.Many2one("account.account", "Recibir depósito", required=True, copy=True,)

	def back_draft(self):
		self.write({'state': 'draft'})
	def cancelar(self):
		self.write({'state': 'cancelado'})
	def actualizar(self):
		for move in self.movimientos_line:
			if not move.move_id:
				move.unlink()
			else:
				if move.move_id.state == 'draft':
					move.unlink()

		obj_move_id = self.env["account.move.line"].search([('date', '>=', self.fecha_apertura), ('account_id.internal_type', '=', 'payable'), 
			('company_id', '=', self.company_id.id), ('partner_id', '=', self.res_partner_prov_id.id), ('move_id.state', '=', 'posted'), ('id', 'not in', self.movimientos_line.mapped('move_line_id.id'))])

		for movimiento in obj_move_id:
			obj_line = self.env["prestamos.afiliados.movimientos"]
			vals = {
				'moviminetos_id': self.id,
				'move_id': movimiento.move_id.id,
				'move_line_id': movimiento.id,
				'partner_id': movimiento.partner_id.id,
				'date': movimiento.date,
				'currency_id': movimiento.currency_id.id,
				'es_conciliado': False,
				'name': movimiento.ref,
				#'analytic_id': movimiento.analytic_id.id,
				'importe_moneda': movimiento.amount_currency,
			}
			if movimiento.debit > 0:
				vals["debe"] = movimiento.debit
			if movimiento.credit > 0:
				vals["haber"] = movimiento.credit
			obj_line.create(vals)

	@api.one
	def _credit_debit_get(self):
		credit = 0
		debit = 0
		tables, where_clause, where_params = self.env['account.move.line'].with_context(state='posted', company_id=self.env.user.company_id.id)._query_get()
		where_params = [tuple(self.res_partner_prov_id.mapped('id'))] + where_params
		if where_clause:
			where_clause = 'AND ' + where_clause
		self._cr.execute("""SELECT account_move_line.partner_id, act.type, SUM(account_move_line.amount_residual)
					  FROM """ + tables + """
					  LEFT JOIN account_account a ON (account_move_line.account_id=a.id)
					  LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
					  WHERE act.type IN ('receivable','payable')
					  AND account_move_line.partner_id IN %s
					  AND account_move_line.reconciled IS FALSE
					  """ + where_clause + """
					  GROUP BY account_move_line.partner_id, act.type
					  """, where_params)
		for pid, type, val in self._cr.fetchall():
			partner = self.browse(pid)
			if type == 'receivable':
				credit = val
			elif type == 'payable':
				debit = -val
		self.saldo_real = credit + debit

	def action_view_invoice_cxp(self):
		invoices = self.mapped('invoice_cxc_ids')
		action = self.env.ref('account.action_vendor_bill_template').read()[0]
		if len(invoices) > 1:
			action['domain'] = [('id', 'in', invoices.ids),('type','=','in_invoice')]
		elif len(invoices) == 1:
			action['views'] = [(self.env.ref('account.invoice_supplier_form').id, 'form')]
			action['res_id'] = invoices.ids[0]
		else:
			action = {'type': 'ir.actions.act_window_close'}
		return action

class AfiliadosMovimientos(models.Model):
	_name = 'prestamos.afiliados.movimientos'
	_description = "Prestamos Afiliados Movimientos"
	_order = "date desc"

	@api.onchange("move_id")
	def onchangeafiliado(self):
		raise Warning(_('El monto debe ser mayor que cero.'))

	moviminetos_id = fields.Many2one('prestamos.afiliados', 'Conciliación')
	move_id = fields.Many2one("account.move", "Movimiento")
	move_line_id = fields.Many2one("account.move.line", "Linea de movimiento")
	partner_id = fields.Many2one('res.partner', 'Empresa')
	date = fields.Date(string="Fecha", help="Effective date for accounting entries", required=True)
	name = fields.Char('Descripción')
	debe = fields.Float('Debe')
	haber = fields.Float("Haber")
	currency_id = fields.Many2one('res.currency', string='Currency')
	analytic_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica")
	importe_moneda = fields.Float("Importe de moneda")
	impreso = fields.Boolean("Impreso")



	
