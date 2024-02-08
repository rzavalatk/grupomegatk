# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
import math
from datetime import datetime
from odoo.exceptions import Warning


class Check(models.Model):
	_name = 'banks.check'
	_rec_name = 'number'
	_inherit = ['mail.thread']
	_order = 'date desc, number desc'
	_description = "description"

	#@api.model_create_multi
	def print_chek(self):
		if not self.princhek:
			self.princhek = True
			print = self.env.ref('banks.banks_check_print')\
				.with_context(discard_logo_check=True).report_action(self)
		else:
			print = self.env.ref('banks.banks_vaucher_print')\
				.with_context(discard_logo_check=True).report_action(self)
		return print

	def get_totalt(self):
		self.amount_total_text = ''

		if self.currency_id:
			self.amount_total_text = self.to_word(self.total)
		else:
			self.amount_total_text = self.to_word(self.total)
		return True

	def to_word(self,number):
		valor = number
		number = int(number)
		parte_decimal, parte_entera = math.modf(valor)
		centavos = round(parte_decimal * 100)

		UNIDADES = (
			'',
			'UN ',
			'DOS ',
			'TRES ',
			'CUATRO ',
			'CINCO ',
			'SEIS ',
			'SIETE ',
			'OCHO ',
			'NUEVE ',
			'DIEZ ',
			'ONCE ',
			'DOCE ',
			'TRECE ',
			'CATORCE ',
			'QUINCE ',
			'DIECISEIS ',
			'DIECISIETE ',
			'DIECIOCHO ',
			'DIECINUEVE ',
			'VEINTE '
		)

		DECENAS = (
			'VENTI',
			'TREINTA ',
			'CUARENTA ',
			'CINCUENTA ',
			'SESENTA ',
			'SETENTA ',
			'OCHENTA ',
			'NOVENTA ',
			'CIEN ')

		CENTENAS = (
			'CIENTO ',
			'DOSCIENTOS ',
			'TRESCIENTOS ',
			'CUATROCIENTOS ',
			'QUINIENTOS ',
			'SEISCIENTOS ',
			'SETECIENTOS ',
			'OCHOCIENTOS ',
			'NOVECIENTOS '
		)
		MONEDAS = (
			{'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
			{'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
			{'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
			{'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
			{'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
			{'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
			{'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
			)
				
		converted = ''
		if not (0 < number < 999999999):
			return 'No es posible convertir el numero a letras'

		number_str = str(number).zfill(9)
		millones = number_str[:3]
		miles = number_str[3:6]
		cientos = number_str[6:]

		if(millones):
			if(millones == '001'):
				converted += 'UN MILLON '
			elif(int(millones) > 0):
				converted += '%sMILLONES ' % self.convert_group(millones)

		if(miles):
			if(miles == '001'):
				converted += 'MIL '
			elif(int(miles) > 0):
				converted += '%sMIL ' % self.convert_group(miles)

		if(cientos):
			if(cientos == '001'):
				converted += 'UN '
			elif(int(cientos) > 0):
				converted += '%s ' % self.convert_group(cientos)
		if(centavos)>0:
			converted+= "con %2i/100 "%centavos
		return converted.capitalize()

	def convert_group(self,n):
		UNIDADES = (
			'',
			'UN ',
			'DOS ',
			'TRES ',
			'CUATRO ',
			'CINCO ',
			'SEIS ',
			'SIETE ',
			'OCHO ',
			'NUEVE ',
			'DIEZ ',
			'ONCE ',
			'DOCE ',
			'TRECE ',
			'CATORCE ',
			'QUINCE ',
			'DIECISEIS ',
			'DIECISIETE ',
			'DIECIOCHO ',
			'DIECINUEVE ',
			'VEINTE '
		)
		DECENAS = (
			'VEINTI',
			'TREINTA ',
			'CUARENTA ',
			'CINCUENTA ',
			'SESENTA ',
			'SETENTA ',
			'OCHENTA ',
			'NOVENTA ',
			'CIEN '
		)

		CENTENAS = (
			'CIENTO ',
			'DOSCIENTOS ',
			'TRESCIENTOS ',
			'CUATROCIENTOS ',
			'QUINIENTOS ',
			'SEISCIENTOS ',
			'SETECIENTOS ',
			'OCHOCIENTOS ',
			'NOVECIENTOS '
		)
		MONEDAS = (
			{'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
			{'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
			{'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
			{'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
			{'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
			{'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
			{'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
		)
		output = ''

		if(n == '100'):
			output = "CIEN "
		elif(n[0] != '0'):
			output = CENTENAS[int(n[0]) - 1]

		k = int(n[1:])
		if(k <= 20):
			output += UNIDADES[k]
		else:
			if((k > 30) & (n[2] != '0')):
				output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
			else:
				output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

		return output

	def get_sequence(self):
		if self.journal_id:
			for seq in self.journal_id.secuencia_ids:
				if seq.move_type == self.doc_type:
					return seq.id

	@api.onchange("currency_id")
	def onchangecurrency(self):
		if self.currency_id:
			if self.currency_id != self.company_id.currency_id:
				tasa = self.currency_id.with_context(date=self.date)
				self.currency_rate = 1 / tasa.rate 
				self.es_moneda_base = False
			else:
				self.currency_rate = 1
				self.es_moneda_base = True

	def update_seq(self):
		deb_obj = self.env["banks.check"].search([('state', '=', 'draft'), ('doc_type', '=', self.doc_type)])
		payment_obj = self.env["banks.payment.invoices.custom"].search([('state', '=', 'draft'), ('doc_type', '=', self.doc_type)])
		n = ""
		for seq in self.journal_id.secuencia_ids:
			if seq.move_type == self.doc_type:
				n = seq.prefix + '%%0%sd' % seq.padding % (seq.number_next_actual + 1)
		for pay in payment_obj:
			pay.write({'name': n})
		for db in deb_obj:
			db.write({'number': n})

	def get_fecha(self):
		mes = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
		year = self.date.strftime("%Y")
		month = self.date.strftime("%m")
		day = self.date.strftime("%d")
		self.fecha_string = str(day)+' de '+str(mes[int(month)-1])+', del '+str(year)

	def get_number(self):
		indixe = len(self.number)
		indixe = indixe - 8
		numer = self.number
		self.numero_chek = numer[indixe:indixe+8]

		
	"""def get_msg_number(self):
		if self.journal_id and self.state == 'draft':
			flag = False
			if not self.cheque_anulado:
				for seq in self.journal_id.secuencia_ids:
					#if seq.move_type == self.doc_type:
					if seq.move_type:
						self.number_calc = seq.prefix + '%%0%sd' % seq.padding % seq.number_next_actual
						flag = True
					if not flag:
						self.msg = "No existe numeración para este banco, verifique la configuración"
						self.number_calc = ""
					else:
						self.msg = """""
    
	def get_msg_number(self):
		if self.journal_id and self.state == 'draft':
			flag = False
			if not self.cheque_anulado:
				for seq in self.journal_id.secuencia_ids:
					if seq.move_type == self.doc_type:
						self.number_calc = seq.prefix + '%%0%sd' % seq.padding % seq.number_next_actual
						flag = True
				if not flag:
					self.msg = "No existe numeración para este banco, verifique la configuración"
					self.number_calc = ""
				else:
					self.msg = ""
			else:
				# ¿Qué debe suceder si self.cheque_anulado es True?
				# Asegúrate de manejar este caso según tus requisitos.
				pass
		else:
			# ¿Qué debe suceder si self.journal_id no está definido o self.state no es 'draft'?
			# Asegúrate de manejar estos casos según tus requisitos.
			pass

	def get_number_calc(self):
		if self.journal_id and self.state == 'draft':
			flag = False
			if not self.cheque_anulado:
				for seq in self.journal_id.secuencia_ids:
					if seq.move_type == self.doc_type:
						self.number_calc = seq.prefix + '%%0%sd' % seq.padding % seq.number_next_actual
						flag = True
						break  # Agregamos un break para salir del bucle cuando encontramos una secuencia válida
				if not flag:
					self.msg = "No existe numeración para este banco, verifique la configuración"
					self.number_calc = ""
				else:
					self.msg = ""
			else:
				self.msg = "El cheque está anulado"  # Mensaje adicional si el cheque está anulado
		else:
			#self.msg = "No se puede calcular el número en estado diferente a borrador o sin un banco asociado"
			self.number_calc = ""
			self.msg = ""



	def get_char_seq(self, journal_id, doc_type):
		jr = self.env["account.journal"].search([('id', '=', journal_id)])
		for seq in jr.secuencia_ids:
			if seq.move_type == "Cheques":
				return (seq.prefix + '%%0%sd' % seq.padding % seq.number_next_actual)

	journal_id = fields.Many2one("account.journal", "Banco", required=True)
	date = fields.Date(string="Fecha de Cheque ", required=True, default=fields.Date.context_today)
	total = fields.Float(string='Total', required=True)
	memo = fields.Text("Descripción", required=True)
	number = fields.Char("Número de cheque", copy=False)
	anulation_date = fields.Date("Fecha de Anulación")
	sequence_id = fields.Many2one("ir.sequence", "Chequera")
	currency_id = fields.Many2one('res.currency', string='Moneda')
	name = fields.Char("Pagar a", required=True)
	check_lines = fields.One2many("banks.check.line", "check_id", "Detalle de cheques", required=True)
	state = fields.Selection([('draft', 'Borrador'), ('validated', 'Validado'), ('postdated', 'Post-Fechado'), ('anulated', 'Anulado')], string='Estado', readonly=True, default='draft')
	currency_rate = fields.Float("Tasa de Cambio", digits=(12, 6))
	difference = fields.Float(string='Diferencia', compute='_compute_rest_credit')
	doc_type = fields.Selection([('check', 'Cheque'), ('transference', 'Transferencia')], string='Tipo de Transacción', required=True)
	msg = fields.Char("Error de configuración", compute=get_number_calc)
	number_calc = fields.Char("Número de Transacción", compute=get_number_calc)
	move_id = fields.Many2one('account.move', 'Apunte Contable', copy=False)
	company_id = fields.Many2one("res.company", "Empresa", default=lambda self: self.env.company, required=True)
	es_moneda_base = fields.Boolean("Es moneda base")
	plantilla_id = fields.Many2one("banks.template", "Plantilla",copy=False)
	cheque_anulado = fields.Boolean("Cheque anulado", copy=False)
	fecha_string = fields.Char(compute = "get_fecha", readonly=True, )
	amount_total_text = fields.Char("Amount Total", compute = 'get_totalt', default='Cero')
	numero_chek = fields.Char(compute = "get_number", readonly=True, )
	princhek = fields.Boolean(copy=False, default=False)

	@api.onchange("plantilla_id")
	def onchangeplantilla(self):
		if self.plantilla_id:
			self.company_id = self.plantilla_id.company_id.id
			self.journal_id = self.plantilla_id.journal_id.id
			self.name = self.plantilla_id.pagar_a
			self.memo = self.plantilla_id.memo
			self.total = self.plantilla_id.total
			#self.doc_type = self.plantilla_id.doc_type
			self.currency_id = self.plantilla_id.currency_id.id
			self.es_moneda_base = self.plantilla_id.es_moneda_base
			lineas = []
			for line in self.plantilla_id.detalle_lines:
				lineas.append((0, 0, {
					'partner_id': line.partner_id.id,
					'account_id': line.account_id.id,
					'name': line.name,
					'amount': line.amount,
					'currency_id': line.currency_id.id,
					'analytic_id': line.analytic_id.id,
					'move_type': line.move_type,
					'check_id': self.id,
				}))
			self.check_lines = lineas

	@api.model
	def create(self, vals):
		vals["number"] = self.get_char_seq(vals.get("journal_id"), vals.get("doc_type"))
		check = super(Check, self).create(vals)
		return check

	#@api.model_create_multi
	def unlink(self):
		for move in self:
			if move.state == 'validated' or move.state == 'anulated':
				raise Warning(_('No puede eliminar registros contabilizados'))
		return super(Check, self).unlink()


	@api.depends('check_lines.amount', 'total')
	def _compute_rest_credit(self):
		debit_line = 0
		credit_line = 0
		for lines in self.check_lines:
			if lines.move_type == 'debit':
				debit_line += lines.amount
			elif lines.move_type == 'credit':
				credit_line += lines.amount
			else:
				credit_line += 0
				debit_line += 0
		self.difference = self.total - (debit_line - credit_line)


	@api.onchange("journal_id")
	def onchangejournal(self):
		self.get_msg_number()
		if self.journal_id:
			if self.journal_id.currency_id:
				self.currency_id = self.journal_id.currency_id.id
			else:
				self.currency_id = self.company_id.currency_id.id

	#@api.model_create_multi
	def set_borrador(self):
		self.write({'state': 'draft'})

	#@api.model_create_multi
	def action_anulate(self):
		self.write({'state': 'anulated'})
		self.cheque_anulado = True
		if not self.cheque_anulado:
			#self.update_seq()
			self.number = self.env["ir.sequence"].search([('id', '=', self.get_sequence())]).next_by_id()

	#@api.model_create_multi
	def action_anulate_cheque(self):
		for move in self.move_id:
			move.write({'state': 'draft'})
			move.unlink()
		self.write({'state': 'anulated'})
		self.cheque_anulado = True

	#@api.model_create_multi
	def action_validate(self):
		if not self.cheque_anulado:
			if not self.number_calc:
				raise Warning(_("El banco no cuenta con configuraciones/parametros para registrar cheques de terceros"))
		if not self.check_lines:
			raise Warning(_("No existen detalles de movimientos a registrar"))
		if self.total < 0:
			raise Warning(_("El total debe de ser mayor que cero"))
		if not round(self.difference, 2) == 0:
			raise Warning(_("Existen diferencias entre el detalle y el total de la transacción a realizar"))

		self.write({'state': 'validated'})
		if not self.cheque_anulado:
			self.number = self.env["ir.sequence"].search([('id', '=', self.get_sequence())]).next_by_id()
		self.write({'move_id': self.generate_asiento()})
		#self.update_seq()
		self.cheque_anulado = False

	def generate_asiento(self):
		account_move = self.env['account.move']
		lineas = []
		vals_credit = {
			'debit': 0.0,
			'credit': self.total * self.currency_rate,
			'name': self.name,
			'account_id': self.journal_id.default_account_id.id,
			'date': self.date,
			#'company_id': self.company_id.id,
		}
		if self.currency_id:
			if self.journal_id.default_account_id.currency_id :
				if self.journal_id.default_account_id.currency_id  == self.currency_id:
					if self.currency_id == self.company_id.currency_id:
						vals_credit["amount_currency"] = 0.0
					else:
						vals_credit["currency_id"] = self.currency_id.id
						vals_credit["amount_currency"] = self.total * -1
				elif self.journal_id.default_account_id.currency_id  == self.company_id.currency_id:
					vals_credit["currency_id"] = self.currency_id.id
					vals_credit["amount_currency"] = self.total * -1
				else:
					vals_credit["currency_id"] = self.journal_id.default_account_id.currency_id.id
					tasa = self.journal_id.default_account_id.currency_id .with_context(date=self.date)
					vals_credit["amount_currency"] = self.total * tasa.rate * -1
			else:
				if self.currency_id == self.company_id.currency_id:
					vals_credit["amount_currency"] = 0.0
				else:
					vals_credit["currency_id"] = self.currency_id.id
					vals_credit["amount_currency"] = self.total * -1

		for line in self.check_lines:
			if line.move_type == 'debit':
				vals_debe = {
					'debit': line.amount * self.currency_rate,
					'credit': 0.0,
					'name': line.name or self.name,
					'account_id': line.account_id.id,
					'date': self.date,
					'partner_id': line.partner_id.id,
					'analytic_account_id': line.analytic_id.id,
				}
				if self.currency_id:
					if line.account_id.currency_id:
						if line.account_id.currency_id  == self.currency_id:
							if self.currency_id == self.company_id.currency_id:
								vals_debe["amount_currency"] = 0.0
							else:
								vals_debe["currency_id"] = self.currency_id.id
								vals_debe["amount_currency"] = line.amount
						elif line.account_id.currency_id  == self.company_id.currency_id:
							vals_debe["currency_id"] = self.currency_id.id
							vals_debe["amount_currency"] = line.amount
						else:
							vals_debe["currency_id"] = line.account_id.currency_id.id
							tasa = line.account_id.currency_id.with_context(date=self.date)
							vals_debe["amount_currency"] = line.amount * tasa.rate
					else:
						if self.currency_id == self.company_id.currency_id:
							vals_debe["amount_currency"] = 0.0
						else:
							vals_debe["currency_id"] = self.currency_id.id
							vals_debe["amount_currency"] = line.amount
				lineas.append((0, 0, vals_debe))
			if line.move_type == 'credit':
				vals_credit_line = {
					'debit': 0.0,
					'credit': line.amount * self.currency_rate,
					'name': line.name or self.name,
					'account_id': line.account_id.id,
					'date': self.date,
					'partner_id': line.partner_id.id,
					'analytic_account_id': line.analytic_id.id,
				}
				if self.currency_id:
					if line.account_id.currency_id:
						if line.account_id.currency_id  == self.currency_id:
							if self.currency_id == self.company_id.currency_id:
								vals_credit_line["amount_currency"] = 0.0
							else:
								vals_credit_line["currency_id"] = self.currency_id.id
								vals_credit_line["amount_currency"] = line.amount * -1
						elif line.account_id.currency_id  == self.company_id.currency_id:
							vals_credit_line["currency_id"] = self.currency_id.id
							vals_credit_line["amount_currency"] = line.amount * -1
						else:
							vals_credit_line["currency_id"] = line.account_id.currency_id.id
							tasa = line.account_id.currency_id.with_context(date=self.date)
							vals_credit_line["amount_currency"] = line.amount * tasa.rate * -1
					else:
						if self.currency_id == self.company_id.currency_id:
							vals_credit_line["amount_currency"] = 0.0
						else:
							vals_credit_line["currency_id"] = self.currency_id.id
							vals_credit_line["amount_currency"] = line.amount * -1
				lineas.append((0, 0, vals_credit_line))
		lineas.append((0, 0, vals_credit))
		values = {
			'journal_id': self.journal_id.id,
			'date': self.date,
			'ref': self.name,
			'line_ids': lineas,
			'state': 'draft',
			#'doc_type': self.doc_type,
		}

		if self.move_id:
			moveline = self.env['account.move.line']
			line = moveline.search( [('move_id', '=', self.move_id.id)])
			line.unlink()
			self.move_id.write(values)
			self.move_id.line_ids.create_analytic_lines()
			return self.move_id.id
		else:
			id_move = account_move.create(values)
			id_move.write({'name': str(self.number)})
			id_move.line_ids.create_analytic_lines()
			return id_move.id
		


class check_line(models.Model):
	_name = 'banks.check.line'
	_description = "description"

	check_id = fields.Many2one('banks.check', 'Check')
	partner_id = fields.Many2one('res.partner', 'Empresa', domain="[('company_id', '=', parent.company_id)]")
	account_id = fields.Many2one('account.account', 'Cuenta', required=True)
	name = fields.Char('Descripción')
	amount = fields.Float('Monto', required=True)
	currency_id = fields.Many2one('res.currency', string='Moneda')
	analytic_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica", domain="[('company_id', '=', parent.company_id)]")
	move_type = fields.Selection([('debit', 'Débito'), ('credit', 'Crédito')], 'Debit/Credit', default='debit', required=True)
