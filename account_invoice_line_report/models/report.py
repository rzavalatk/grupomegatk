# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api


class AccountInvoiceReport(models.Model):
	_name = "account.move.report.line"
	_description = "Productos vendidos"
	_auto = False
	_rec_name = 'date'
	
	@api.depends('currency_id', 'date', 'price_total', 'price_average', 'amount_residual')
	def _compute_amounts_in_user_currency(self):
		"""Compute the amounts in the currency of the user
		"""
		user_currency_id = self.env.user.company_id.currency_id
		currency_rate_id = self.env['res.currency.rate'].search([
			('rate', '=', 1), 
			'|', ('company_id', '=', self.env.user.company_id.id), ('company_id', '=', False)], limit=1)
		base_currency_id = currency_rate_id.currency_id
		for record in self:
			date = record.date or fields.Date.today()
			company = record.company_id
			record.user_currency_price_total = base_currency_id._convert(record.price_total, user_currency_id, company, date)
			record.user_currency_price_average = base_currency_id._convert(record.price_average, user_currency_id, company, date)
			record.user_currency_amount_residual = base_currency_id._convert(record.amount_residual, user_currency_id, company, date)

	number = fields.Char('Factura #', readonly=True)
	date = fields.Date(readonly=True, string="Fecha")
	product_id = fields.Many2one('product.product', string='Producto', readonly=True)
	marca_id = fields.Many2one('product.marca', string='Marca',)
	product_qty = fields.Float(string='Cantidad', readonly=True)
	costo = fields.Float(string='Costo', readonly=True)
	uom_name = fields.Char(string='Reference Unit of Measure', readonly=True)
	payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term', readonly=True)
	fiscal_position_id = fields.Many2one('account.fiscal.position', oldname='fiscal_position', string='Fiscal Position', readonly=True)
	currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
	categ_id = fields.Many2one('product.category', string='Product Category', readonly=True)
	journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
	partner_id = fields.Many2one('res.partner', string='Cliente', readonly=True)
	commercial_partner_id = fields.Many2one('res.partner', string='Partner Company', help="Commercial Entity")
	company_id = fields.Many2one('res.company', string='Company', readonly=True)
	invoice_user_id = fields.Many2one('res.users', string='Responsable', readonly=True)
	price_total = fields.Float(string='Sub total', readonly=True)
	user_currency_price_total = fields.Float(string="Total Without Tax in Currency", compute='_compute_amounts_in_user_currency', digits=0)
	price_average = fields.Float(string='P.U.', readonly=True, group_operator="avg")
	user_currency_price_average = fields.Float(string="Average Price in Currency", compute='_compute_amounts_in_user_currency', digits=0)
	currency_rate = fields.Float(string='Currency Rate', readonly=True, group_operator="avg", groups="base.group_multi_currency")
	nbr = fields.Integer(string='Line Count', readonly=True)  # TDE FIXME master: rename into nbr_lines
	invoice_origin = fields.Many2one('account.move', readonly=True)
	move_type = fields.Selection([
		('out_invoice', 'Customer Invoice'),
		('in_invoice', 'Vendor Bill'),
		('out_refund', 'Customer Credit Note'),
		('in_refund', 'Vendor Credit Note'),
		], readonly=True)
	state = fields.Selection([
		('draft', 'Draft'),
		('open', 'Open'),
		('paid', 'Paid'),
		('cancel', 'Cancelled')
		], string='Invoice Status', readonly=True)
	invoice_date_due = fields.Date(string='Due Date', readonly=True)
	account_id = fields.Many2one('account.account', string='Receivable/Payable Account', readonly=True, domain=[('deprecated', '=', False)])
	account_line_id = fields.Many2one('account.account', string='Revenue/Expense Account', readonly=True, domain=[('deprecated', '=', False)])
	partner_bank_id = fields.Many2one('res.partner.bank', string='Bank Account', readonly=True)
	amount_residual = fields.Float(string='Due Amount', readonly=True)
	user_currency_residual = fields.Float(string="Total Residual", compute='_compute_amounts_in_user_currency', digits=0)
	country_id = fields.Many2one('res.country', string="Partner Company's Country")
	account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', groups="analytic.group_analytic_accounting")
	amount_total = fields.Float(string='Total', readonly=True)

	_order = 'date desc'

	_depends = {
		'account.move': [
			'amount_total_signed', 'commercial_partner_id', 'company_id',
			'currency_id', 'invoice_date_due', 'fiscal_position_id',
			'journal_id', 'name', 'partner_bank_id', 'partner_id', 'invoice_payment_term_id',
			'amount_residual', 'state', 'move_type',
		],
		'account.move.line': [
			'account_id', 'move_id', 'product_id',
			'quantity', 'product_uom_id',
		],
		'product.product': ['product_tmpl_id'],
		'product.template': ['categ_id'],
		'product.template': ['marca_id'],
		'uom.uom': ['category_id', 'factor', 'name', 'uom_type'],
		'res.currency.rate': ['currency_id', 'name'],
		'res.partner': ['country_id'],
	}

	#Migracion campos marca y costo real
	def _select(self):
		select_str = """
			SELECT sub.id, sub.number, sub.date, sub.product_id, sub.partner_id, sub.country_id,
				sub.invoice_payment_term_id AS payment_term_id, sub.uom_name, sub.currency_id, sub.journal_id,
				sub.fiscal_position_id, sub.invoice_user_id, sub.company_id, sub.nbr,  sub.move_type, sub.state,
				sub.categ_id, sub.marca_id, sub.costo, sub.invoice_date_due, sub.account_line_id, sub.partner_bank_id,
				sub.product_qty, sub.price_total as price_total, sub.price_average as price_average, sub.amount_total / COALESCE(cr.rate, 1) as amount_total,
				COALESCE(cr.rate, 1) as currency_rate, sub.residual as residual, sub.commercial_partner_id as commercial_partner_id
		"""
		return select_str

	def _sub_select(self):
		select_str = """
				SELECT ail.id AS id,
					ai.invoice_date AS date,
					ai.name as number,
					ail.product_id, ai.partner_id, ai.invoice_payment_term_id, 
					u2.name AS uom_name,
					ai.currency_id, ai.journal_id, ai.fiscal_position_id, ai.invoice_user_id, ai.company_id,
					1 AS nbr,
					ai.id AS invoice_origin, ai.move_type, ai.state, pt.categ_id, pt.marca_id, 
					CASE 
						WHEN pt.x_costo_real > 0 
							THEN pt.x_costo_real 
							
						END AS costo, 
					ai.invoice_date_due, ail.move_id AS account_line_id,
					ai.partner_bank_id,
					SUM ((invoice_type.sign_qty * ail.quantity) / COALESCE(u.factor,1) * COALESCE(u2.factor,1)) AS product_qty,
					SUM(ail.price_subtotal* invoice_type.sign) AS price_total,
					SUM(ail.price_total * invoice_type.sign_qty) AS amount_total,
					SUM(ABS(ail.price_subtotal)) / CASE
							WHEN SUM(ail.quantity / COALESCE(u.factor,1) * COALESCE(u2.factor,1)) <> 0::numeric
							   THEN SUM(ail.quantity / COALESCE(u.factor,1) * COALESCE(u2.factor,1))
							   ELSE 1::numeric
							END AS price_average,
					ai.amount_residual_signed / (SELECT count(*) FROM account_move_line l where CAST(invoice_origin AS integer) = ai.id) *
					count(*) * invoice_type.sign AS residual,
					ai.commercial_partner_id as commercial_partner_id,
					coalesce(partner.country_id, partner_ai.country_id) AS country_id
		"""
		return select_str

	def _from(self):
		from_str = """
				FROM account_move_line ail
				JOIN account_move ai ON ai.id = ail.move_id
				JOIN res_partner partner ON ai.commercial_partner_id = partner.id
				JOIN res_partner partner_ai ON ai.partner_id = partner_ai.id
				LEFT JOIN product_product pr ON pr.id = ail.product_id
				left JOIN product_template pt ON pt.id = pr.product_tmpl_id
				LEFT JOIN uom_uom u ON u.id = ail.product_uom_id
				LEFT JOIN uom_uom u2 ON u2.id = pt.uom_id
				JOIN (
					-- Temporary table to decide if the qty should be added or retrieved (Invoice vs Credit Note)
					SELECT id,(CASE
						 WHEN ai.move_type::text = ANY (ARRAY['in_refund'::character varying::text, 'in_invoice'::character varying::text])
							THEN -1
							ELSE 1
						END) AS sign,(CASE
						 WHEN ai.move_type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
							THEN -1
							ELSE 1
						END) AS sign_qty
					FROM account_move ai
				) AS invoice_type ON invoice_type.id = ai.id
		"""
		return from_str

	def _group_by(self):
		group_by_str = """
				GROUP BY ail.id, ail.product_id, ai.invoice_date, ai.id,
					ai.partner_id, ai.invoice_payment_term_id, u2.name, u2.id, ai.currency_id, ai.journal_id,
					ai.fiscal_position_id, ai.invoice_user_id, ai.company_id, ai.id, ai.move_type, invoice_type.sign, ai.state, pt.categ_id, 
					pt.marca_id, pt.x_costo_real, ai.invoice_date_due, ail.account_id, ai.partner_bank_id, ai.amount_residual_signed,
					ai.amount_total_signed, ai.commercial_partner_id, coalesce(partner.country_id, partner_ai.country_id)
		"""
		return group_by_str

	def init(self):
		# self._table = account_invoice_report
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			WITH currency_rate AS (%s)
			%s
			FROM (
				%s %s WHERE ail.account_id IS NOT NULL %s
			) AS sub
			LEFT JOIN currency_rate cr ON
				(cr.currency_id = sub.currency_id AND
				 cr.company_id = sub.company_id AND
				 cr.date_start <= COALESCE(sub.date, NOW()) AND
				 (cr.date_end IS NULL OR cr.date_end > COALESCE(sub.date, NOW())))
		)""" % (
					self._table, self.env['res.currency']._select_companies_rates(),
					self._select(), self._sub_select(), self._from(), self._group_by()))

