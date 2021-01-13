# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.addons import decimal_precision as dp
import math
import logging
_logger = logging.getLogger(__name__)

class Prestamos(models.Model):
	_name = 'prestamos'
	_description = "Prestamos"
	_order = "id desc"
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

	@api.onchange("payment_term_id")
	def onchangemes(self):
		if self.payment_term_id:
			meses = self.payment_term_id.name.split(' ')
			if meses[0].isdigit():
				pass
			self.meses_cred = meses[0] 

	def cuentas(self):
		self.write({'account_id':self.env['ir.config_parameter'].sudo().get_param('prestamos.account_id') or False,
			'account_redes_id':self.env['ir.config_parameter'].sudo().get_param('prestamos.account_redes_id') or False,
			'producto_gasto_id':self.env['ir.config_parameter'].sudo().get_param('prestamos.producto_gasto_id') or False,
			'producto_interes_id':self.env['ir.config_parameter'].sudo().get_param('prestamos.producto_interes_id') or False,
			'recibir_pagos':self.env['ir.config_parameter'].sudo().get_param('prestamos.recibir_pagos') or False
			})
		
	def _get_invoiced(self):
		w = len(set(self.cuotas_id.ids))
		y = len(set(self.payment_ids.ids))
		x = 0
		z = 0
		for invoice in self.invoice_cxc_ids:
			if(invoice.type == 'in_invoice'):
				z = z + 1
			else:
				x = x + 1
		self.invoice_count_cxp = z
		self.invoice_count_cxc = x
		self.payment_count = y
		self.cuotas_count= w

	name = fields.Char('Numero', copy=False)
	description = fields.Text('Descripción',readonly=True, states={'draft': [('readonly', False)]},copy=False)

	fecha_inicio = fields.Datetime(string='Fecha de inicio',readonly=True, states={'draft': [('readonly', False)]},)
	fecha_final = fields.Datetime(string='Fecha final',readonly=True, states={'draft': [('readonly', False)]}, index=True,)

	equipo = fields.Char('Equipo',readonly=True, states={'draft': [('readonly', False)]},)
	precio_a  = fields.Float(string='Precio A', readonly=True, states={'draft': [('readonly', False)]},)
	precio_m = fields.Float(string='Precio M', readonly=True, states={'draft': [('readonly', False)]},)
	prima = fields.Float(string='Prima', readonly=True, states={'draft': [('readonly', False)]},)

	utilidad = fields.Float(string='Utilidad', compute='_onchange_precioa_preciom', readonly=True, states={'draft': [('readonly', False)]},)
	monto_cxp = fields.Float(string='Monto a pagar', compute='_onchange_preciom_prima', readonly=True, states={'draft': [('readonly', False)]},)

	monto_cxc = fields.Float(string='Monto a financiar', compute='_onchange_precio',store=True, readonly=True, states={'draft': [('readonly', False)]},)
	monto_personal = fields.Float(string='Monto a financiar', store=True, readonly=True, states={'draft': [('readonly', False)]},)
	monto_finan = fields.Float(string='Monto a financiar', compute='_onchange_precioa_prima',store=True, readonly=True, states={'draft': [('readonly', False)]},)
	
	monto_restante = fields.Float(string='Capital restante', copy=False,)
	gasto_prestamo = fields.Float(string='Gasto', default=0,readonly=True, states={'draft': [('readonly', False)]},copy=False,)

	cuota_prestamo = fields.Float(string='Cuota', copy=False, readonly=True, states={'draft': [('readonly', False)]},)
	cuota_inicial = fields.Float(string='Cuota inicial', copy=False, readonly=True, states={'draft': [('readonly', False)]},)

	tasa = fields.Float(string='Tasa', digits=dp.get_precision('Product Price'), copy=False, readonly=True, states={'draft': [('readonly', False)]},)
	
	payment_term_id = fields.Many2one('account.payment.term', string='Plazo de pago', required=True,readonly=True, states={'draft': [('readonly', False)]},)
	meses_cred = fields.Integer(string='Mes', required=True,readonly=True, states={'draft': [('readonly', False)]})
	tipo_prestamo = fields.Selection( [('financiamiento', 'Financiamiento'),('personal', 'Personal')], default='financiamiento', )

	currency_id = fields.Many2one('res.currency', 'Moneda', default=lambda self: self.env.user.company_id.currency_id.id,readonly=True, states={'draft': [('readonly', False)]},)
	company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, default=lambda self: self.env.user.company_id,readonly=True, states={'draft': [('readonly', False)]},)
	
	res_partner_id = fields.Many2one('res.partner', string='Cliente', domain=[('customer','=',True), ], required=True, readonly=True, states={'draft': [('readonly', False)]},)
	res_partner_prov_id = fields.Many2one('res.partner', string='Proveedor', domain=[('supplier','=',True), ],)
	
	state = fields.Selection( [('draft', 'Borrador'), ('cancelado', 'Cancelado'),('validado', 'Validado'),('desembolso', 'Desembolsado'),('proceso', 'En proceso'),('finalizado', 'Finalizado')], string="Estado", default='draft',copy=False, track_visibility='onchange', )
	sequence_id = fields.Many2one('ir.sequence', "Fiscal Number")
	
	cuotas_id = fields.One2many("prestamos.cuotas", "cuotas_prestamo_id", "Cuotas de prestamo",copy=False,)
	banco_id = fields.Many2one("banks.check", "Cheque/Transferencia", copy=False,)

	invoice_cxc_ids = fields.Many2many("account.invoice", string='Facturas cxc', readonly=True, copy=False)

	payment_ids = fields.Many2many("account.payment", string="Pagos", copy=False,)
	
	recibir_pagos = fields.Many2one("account.journal", "Recibir pagos",  domain=[('type','=','bank')], )
	
	producto_gasto_id = fields.Many2one('product.product', string='Cuenta de gasto', domain=[('sale_ok', '=', True)],)
	producto_interes_id = fields.Many2one('product.product', string='Cuenta de interes', domain=[('sale_ok', '=', True)], )

	account_id = fields.Many2one('account.account', 'Cuenta de desembolso', )
	account_redes_id = fields.Many2one('account.account', 'Cuenta de redescuento', readonly=True, states={'draft': [('readonly', False)]},)
	
	user_id = fields.Many2one('res.users', string='Responsable', index=True,  default=lambda self: self.env.user,readonly=True, states={'draft': [('readonly', False)]},)
	
	invoice_count_cxc = fields.Integer(string='Factura Count', compute='_get_invoiced', readonly=True)
	invoice_count_cxp = fields.Integer(string='Factura Count', compute='_get_invoiced', readonly=True)
	payment_count = fields.Integer(string='Payment Count', compute='_get_invoiced', readonly=True)
	cuotas_count = fields.Integer(string='cuotas Count', compute='_get_invoiced', readonly=True)

	@api.onchange('monto_cxc')
	def _onchange_monto_cxc(self):
		self.monto_restante = self.monto_cxc

	@api.one
	@api.depends('precio_a','prima')
	def _onchange_precioa_prima(self):
		if self.precio_a != 0 and self.prima != 0:
			self.monto_finan = self.precio_a - self.prima

	@api.depends('monto_personal','monto_finan')
	def _onchange_precio(self):
		self.monto_cxc = self.monto_personal or self.monto_finan

	@api.depends('precio_m','prima')
	def _onchange_preciom_prima(self):
		if self.precio_m != 0 and self.prima != 0 :
			self.monto_cxp = self.precio_m - self.prima

	@api.depends('precio_m','precio_a')
	def _onchange_precioa_preciom(self):
		if self.precio_m != 0 and self.precio_a != 0:
			self.utilidad = self.precio_a - self.precio_m

	@api.onchange('payment_term_id', 'fecha_inicio')
	def _onchange_payment_term_fecha_inicio(self):
		fecha_inicio = self.fecha_inicio
		if not fecha_inicio:
			fecha_inicio = fields.Date.context_today(self)
		if self.payment_term_id:
			pterm = self.payment_term_id
			pterm_list = pterm.with_context(currency_id=self.company_id.currency_id.id).compute(value=1, date_ref=fecha_inicio)[0]
			self.fecha_final = max(line[0] for line in pterm_list)
		elif self.fecha_final and (fecha_inicio > self.fecha_final):
			self.fecha_final = fecha_inicio

	def validar(self):
		if self.monto_cxc < 0:
			raise Warning(_('No se puede procesar el prestamo'))
		if not self.name:
			if self.tipo_prestamo == 'financiamiento':
				if not self.sequence_id.id:
					obj_sequence = self.env["ir.sequence"].search([('company_id','=',self.company_id.id),('name','=','Financiamiento')])
					if not obj_sequence.id:
						values = {'name': 'Financiamiento',
							'prefix': 'FINAN. ',
							'company_id': self.company_id.id,
							'padding':6,}
						sequence_id = obj_sequence.create(values)
					else:
						sequence_id = obj_sequence  
					self.write({'sequence_id': sequence_id.id})

					new_name = self.sequence_id.with_context().next_by_id()
					self.write({'name': new_name})
				else:
					self.write({'sequence_id': self.sequence_id.id})
					new_name = self.sequence_id.with_context().next_by_id()
					self.write({'name': new_name})
				self._financiamiento()
			else:
				if not self.sequence_id.id:
					obj_sequence = self.env["ir.sequence"].search([('company_id','=',self.company_id.id),('name','=','Prestamos')])
					if not obj_sequence.id:
						values = {'name': 'Prestamos',
							'prefix': 'PER. ',
							'company_id': self.company_id.id,
							'padding':6,}
						sequence_id = obj_sequence.create(values)
					else:
						sequence_id = obj_sequence  
					self.write({'sequence_id': sequence_id.id})

					new_name = self.sequence_id.with_context().next_by_id()
					self.write({'name': new_name})
				else:
					self.write({'sequence_id': self.sequence_id.id})
					new_name = self.sequence_id.with_context().next_by_id()
					self.write({'name': new_name})
				self._personal()
		else:
			if self.tipo_prestamo == 'financiamiento':
				self._financiamiento()
			else:
				self._personal()

	def _financiamiento(self):
		monto = self.monto_cxc or self.monto_cxp
		monto_efectivo = self.precio_m - self.prima
		tasa = self.tasa/100
		cuotas = self.meses_cred
		cuota_ini = (monto_efectivo * ((tasa*((1+tasa)**cuotas))/(((1+tasa)**cuotas)-1)))

		cuotaf5 = (self.precio_a - self.prima) / cuotas
		montoa = (cuotaf5 * cuotas) + self.prima
		montob = (cuota_ini * cuotas) + self.prima
		if montob < montoa:
			cuota_ini = cuotaf5

		cuota_ini = math.ceil(cuota_ini)
		monto_final = cuotas * cuota_ini
		tasa_aprox = ((monto_final / monto)-1) / cuotas

		if tasa_aprox != 0:
			cuota_efec = (monto * ((tasa_aprox*((1+tasa_aprox)**cuotas))/(((1+tasa_aprox)**cuotas)-1)))
			#_logger.info("//////////////////////////////////////////")
			while cuota_ini != cuota_efec:
				tasa_aprox = tasa_aprox + 0.0000001
				cuota_efec = (monto * ((tasa_aprox*((1+tasa_aprox)**cuotas))/(((1+tasa_aprox)**cuotas)-1)))
				if cuota_efec > cuota_ini:
					break

		estado = 'desembolso'
		gasto = self.gasto_prestamo

		self._cuotas(monto,tasa_aprox,cuota_ini,gasto,0)

		self.write({'state': estado,
					'cuota_prestamo': cuota_ini,
					'cuota_inicial': cuota_ini + self.gasto_prestamo,
					'tasa': tasa_aprox * 100
					})

	def _personal(self):
		monto = self.monto_cxc or self.monto_cxp
		tasa = self.tasa/100
		cuotas = self.meses_cred
		cuota = (monto * ((tasa*((1+tasa)**cuotas))/(((1+tasa)**cuotas)-1)))
		estado = 'validado'
		gasto = self.gasto_prestamo

		self._cuotas(monto,tasa,cuota,gasto,0)

		self.write({'state': estado,
					'cuota_prestamo': cuota,
					'cuota_inicial': cuota + self.gasto_prestamo
					})

	def _cuotas(self,monto,tasa,cuota,gasto,monto_atrasado):
		cuotas_ids = self.env["prestamos.cuotas"].search([('cuotas_prestamo_id','=',self.id)])
		monto_atrasado1 = monto_atrasado
		x = 1
		if cuotas_ids:
			for cuotas in cuotas_ids:
				if cuotas.state == 'draft':
					cuotas.sudo().unlink()
				else:
					x = x + 1
		
		obj_precio = self.env["prestamos.cuotas"]
		saldo = 1
		fecha_inicial = self.fecha_inicio or fields.Date.context_today(self)
		dia = fecha_inicial.day
		mes = fecha_inicial.month + x - 1 if x > 1 else fecha_inicial.month
		year = fecha_inicial.year
		if mes==13: 
			mes = 1
			year = year + 1
		while saldo > 0.1:
			interes = monto * tasa
			saldo = monto + interes - cuota - monto_atrasado1
			mes = mes + 1
			if mes==13: 
				mes = 1
				year = year + 1
			if self.comprobar_fecha(year, mes, dia):
				fecha_pago = str(year) +'/'+ str(mes) +'/'+ str(dia)
			elif self.comprobar_fecha(year, mes, dia-1):
				fecha_pago = str(year) +'/'+ str(mes) +'/'+ str(dia-1)
			elif self.comprobar_fecha(year, mes, dia-2):
				fecha_pago = str(year) +'/'+ str(mes) +'/'+ str(dia-2)
			else:
				fecha_pago = str(year) +'/'+ str(mes) +'/'+ str(dia-3)

			valores = {
				'name': 'Cuota ' + str(x) ,
				'cuotas_prestamo_id': self.id,
				'cuota_prestamo': (cuota + gasto + monto_atrasado1) if (monto + interes) > cuota else (monto + interes + monto_atrasado1), 
				'cuota_interes': interes, 
				'cuota_capital': monto, 
				'saldo': saldo if saldo >= 0 else 0, 
				'interes_moratorio': monto_atrasado1, 
				'gastos': gasto, 
				'fecha_pago': fecha_pago,  
				'res_partner_id': self.res_partner_id.id,
			}
			monto_atrasado1= monto_atrasado1 - monto_atrasado1
			id_precio = obj_precio.create(valores)
			monto = saldo
			gasto = 0
			x = x + 1

	def comprobar_fecha(self,a, m, d):
		#Array que almacenara los dias que tiene cada mes (si el ano es bisiesto, sumaremos +1 al febrero)
		dias_mes = [31, 28, 31, 30,31, 30, 31, 31, 30, 31, 30, 31]
	 
		#Comprobar si el ano es bisiesto y anadir dia en febrero en caso afirmativo
		if((a%4 == 0 and a%100 != 0) or a%400 == 0):
			dias_mes[1] += 1
	 
		#Comprobar que el mes sea valido
		if(m < 1 or m > 12):
			return False
		 
		#Comprobar que el dia sea valido
		m -= 1
		if(d <= 0 or d > dias_mes[m]):
			return False
	 
		#Si ha pasado todas estas condiciones, la fecha es valida
		return True
 
	def cancelar(self):
		cuotas = self.env["prestamos.cuotas"].search([('cuotas_prestamo_id','=',self.id)])
		if cuotas:
			for cuota in cuotas:
				if cuota.state != 'draft':
					raise Warning(_('No se puede eliminar o cancelar un prestamo en estado de '+ self.state))
				cuota.sudo().unlink()

		if self.invoice_count_cxc > 1:
			raise Warning(_('No se puede eliminar o cancelar un prestamo en estado de '+ self.state))

		self.write({'state': 'cancelado',
					'cuota_prestamo': 0,
					'cuota_inicial': 0
					})
		
	def back_draft(self):
		self.write({'state': 'draft'})

	def unlink(self):
		for prestamo in self:
			if prestamo.state != 'draft':
				raise Warning(_('No se puede eliminar o cancelar una prestamo en estado '+ prestamo.state))
		return super(Prestamos, self).unlink()

	def crear_factura(self):
		self.cuentas()
		if not self.invoice_cxc_ids:
			self.crear_factura_cxc()
			if (self.tipo_prestamo == 'financiamiento'):
				self.crear_factura_cxp()
			self.write({
				'monto_restante': self.monto_cxc
			})

	def crear_factura_cxc(self):
		obj_factura = self.env["account.invoice"]
		lineas = []
		val_lineas = {
			'name': 'Capital prestado',
			'account_id': self.account_id.id,
			'price_unit': self.monto_cxc,
			'quantity': 1,
			'product_id': False,
			'x_user_id': self.env.user.id
		}
		lineas.append((0, 0, val_lineas))
		if self.gasto_prestamo > 0:
			val_lineas1 = {
				'name': 'Cargos administrativos',
				'account_id': self.producto_gasto_id.property_account_income_id.id or self.producto_gasto_id.categ_id.property_account_income_categ_id.id,
				'price_unit': self.gasto_prestamo,
				'quantity': 1,
				'product_id': self.producto_gasto_id.id or False,
				'x_user_id': self.env.user.id
			}
			lineas.append((0, 0, val_lineas1))
		company_id = self.company_id.id
		journal_id = (self.env['account.invoice'].with_context(company_id=company_id or self.env.user.company_id.id)
			.default_get(['journal_id'])['journal_id'])
		if not journal_id:
			raise UserError(_('Please define an accounting sales journal for this company.'))
		val_encabezado = {
			'name': '',
			'type': 'out_invoice',
			'account_id': self.res_partner_id.property_account_receivable_id.id,
			'partner_id': self.res_partner_id.id,
			'journal_id': journal_id,
			'currency_id': self.currency_id.id,
			'payment_term_id': self.payment_term_id.id,
			'company_id': company_id,
			'user_id': self.user_id and self.user_id.id,
			'invoice_line_ids': lineas,
		}
		
		account_invoice_id = obj_factura.create(val_encabezado)
		#id_move.action_validate()
		self.write({
			'invoice_cxc_ids' : [(6, 0, {account_invoice_id.id})],
			'state': 'proceso'
		})

	def crear_factura_cxp(self):
		obj_factura = self.env["account.invoice"]

		# product = self.product_id.with_context(force_company=self.company_id.id)
		# account = product.property_account_income_id or product.categ_id.property_account_income_categ_id

		lineas = []
		val_lineas = {
			'name': 'Capital prestado',
			'account_id': self.account_id.id,
			'price_unit': self.monto_cxc,
			'quantity': 1,
			'product_id': False,
		}
		lineas.append((0, 0, val_lineas))
		if self.monto_cxp != self.monto_cxc:
			val_lineas1 = {
				'name': 'Redescuento',
				'account_id': self.account_redes_id.id,
				'price_unit': (self.monto_cxc - self.monto_cxp) * -1,
				'quantity': 1,
				'product_id': False
			}
			lineas.append((0, 0, val_lineas1))
		company_id = self.company_id.id
		val_encabezado = {
			'name': '',
			'type': 'in_invoice',
			'account_id': self.res_partner_prov_id.property_account_payable_id.id,
			'partner_id': self.res_partner_prov_id.id,
			'currency_id': self.currency_id.id,
			'company_id': company_id,
			'user_id': self.user_id and self.user_id.id,
			'invoice_line_ids': lineas,
		}
		
		account_invoice_id = obj_factura.create(val_encabezado)
		#id_move.action_validate()
		self.write({
			'invoice_cxc_ids' : [(4,account_invoice_id.id,0)],
			'state': 'proceso'
		})

	def action_view_invoice(self):
		invoices = self.mapped('invoice_cxc_ids')
		action = self.env.ref('account.action_invoice_tree1').read()[0]
		if len(invoices) > 1:
			action['domain'] = [('id', 'in', invoices.ids),('type','=','out_invoice')]
		elif len(invoices) == 1:
			action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
			action['res_id'] = invoices.ids[0]
		else:
			action = {'type': 'ir.actions.act_window_close'}
		return action

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

	def action_view_payment(self):
		patment = self.mapped('payment_ids')
		action = self.env.ref('account.action_account_payments').read()[0]
		if len(patment) > 1:
			action['domain'] = [('id', 'in', patment.ids)]
		elif len(patment) == 1:
			action['views'] = [(self.env.ref('account.view_account_payment_form').id, 'form')]
			action['res_id'] = patment.ids[0]
		else:
			action = {'type': 'ir.actions.act_window_close'}
		return action