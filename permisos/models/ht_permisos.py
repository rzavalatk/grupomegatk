# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import Warning
import datetime
import pytz

class HrPermisos(models.Model):
	_name = 'hr.employee.permiso'
	_order = "id desc"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = "description"
	

	#@api.model
	def solicitante(self):
		try:
			ctx = self._context
			obj_prestamo = self.env[ctx["active_model"]].browse(ctx['active_id'])
			return obj_prestamo.id
		except Exception as e:
			return 0

	name = fields.Char('Permiso', copy=False)
	fecha_inicio = fields.Datetime(string='Desde', required=True ) 
	fecha_inicio_txt = fields.Char(string='Desde' ) 
	fecha_fin = fields.Datetime(string='Hasta', required=True )
	fecha_fin_txt = fields.Char(string='Hasta')
	cargo = fields.Selection([('vaciones', 'Vacaciones'),('deduccion', 'Dedución de sueldo'),('sincargo', 'Sin cargo'),('incapacidad', 'Incapacidad')], default= 'vaciones', copy=False, required=True, track_visibility='onchange')
	reporto = fields.Selection([('anticipado', 'Anticipado'),('llamada', 'Llamada'),('mensaje', 'Mensaje'),('noreporto', 'No reporto')], default= 'anticipado', copy=False, required=True, track_visibility='onchange')
	employe_id = fields.Many2one('hr.employee', string='Solicitante', default = solicitante, required=True, track_visibility='onchange')
	cubierto_employe_id = fields.Many2one('hr.employee', string='Ausencia cubierta', copy=False,)
	justificacion = fields.Text('Motivo' ,copy=False)
	state = fields.Selection( [('draft', 'Borrador'), ('pendiente', 'Pendiente'), ('aprobado', 'Aprobado'), ('denegado', 'Denegado'), ('cancelado', 'Cancelado')], string="Estado", default='draft',copy=False, track_visibility='onchange')
	dias = fields.Integer(string='Días', default=0)
	horas = fields.Integer(string='Horas', default=0)
	minutos = fields.Integer(string='Minutos', default=0)
	department_id = fields.Integer(string="Departamento")
	sequence_id = fields.Many2one('ir.sequence', "Prestamo")
	por_empresa = fields.Boolean('Por Empresa:', default=False)

	
	@api.onchange('employe_id')
	def _onchange_employe(self):
		self.department_id = self.employe_id.department_id.id

	@api.onchange('fecha_fin','fecha_inicio')
	def _onchange_fechafin(self):
		if self.fecha_fin and self.fecha_inicio:
			user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
			fecha_inicial = pytz.utc.localize(self.fecha_inicio).astimezone(user_tz)
			fecha_fin = pytz.utc.localize(self.fecha_fin).astimezone(user_tz)
			
			if fecha_fin >= fecha_inicial:
				permiso = self.calcularPermisos(fecha_inicial,fecha_fin)
				if not isinstance(permiso,str):
					self.dias = permiso['D']
					self.horas = permiso['H']
					self.minutos = permiso['M']
					self.fecha_inicio_txt = str(fecha_inicial.strftime("%d-%m-%Y %H:%M:%S"))
					self.fecha_fin_txt = str(fecha_fin.strftime("%d-%m-%Y %H:%M:%S"))
			else:
				self.dias = 0
				self.horas = 0
				self.minutos = 0
				self.env.user.notify_warning(message='La fecha final debe ser mayor o igual a la inicial')

	def rangeDate(self, dateInit, dateEnd):
		dates = [
			dateInit + datetime.timedelta(n) for n in range(int((dateEnd - dateInit).days))
		]
		datesClear = []
		for date in dates:
			if date.weekday() != 6:
				datesClear.append(date)
		return len(datesClear)

	def calcularPermisos(self, datetimeInit, datetimeEnd):
		dateInit = datetimeInit.date()
		dateEnd = datetimeEnd.date()
		timeInit = datetimeInit.time()
		timeEnd = datetimeEnd.time()
		res = {
			'D': 0,
			'H': 0,
			'M': 0
		}
		if dateInit == dateEnd and timeInit == timeEnd:
			return res
		if dateInit == dateEnd and timeInit != timeEnd:
			days = 0
			hour = timeEnd.hour - timeInit.hour
			if timeEnd.hour > 12 and timeInit.hour <= 12:
				hour = hour - 1
			if hour < 0:
				return "Error en las Horas."
			else:
				hour = hour - 1
				minutes = timeEnd.minute - timeInit.minute
				if minutes < 0 and hour >= 0:
					minutesInit = 60 - timeInit.minute
					minutes = timeEnd.minute + minutesInit
				elif minutes < 0 and hour < 0:
					return "Error en los Minutos."
				else:
					hour = hour + 1
				if dateInit.weekday() == 5:
					hour = hour * 2
					minutes = minutes * 2
					while minutes >= 60:
						minutes = minutes - 60
						hour = hour + 1
				while hour >= 8:
					hour = hour - 8
					days = days + 1
				if timeEnd.hour == 12:
					minutes = 0
				res['D'],res['H'],res['M'] = days,hour,minutes
		if dateInit != dateEnd and timeInit == timeEnd:
			rang = self.rangeDate(dateInit=dateInit, dateEnd=dateEnd)
			if rang == 0:
				return "Error en las fechas."
			else:
				res['D'],res['H'],res['M'] = rang,0,0
		if dateInit != dateEnd and timeInit != timeEnd:
			rang = self.rangeDate(dateInit=dateInit, dateEnd=dateEnd)
			if rang < 0:
				return "Error en las fechas."
			rang = rang - 1
			sab = 0
			if (dateEnd.weekday() == 5 or dateEnd.weekday() == 6) and timeEnd.hour > 12:
				sab = timeEnd.hour - 12
			sab = timeEnd.hour - sab
			H1 = 17 - timeInit.hour
			H2 = sab - 8
			if timeInit.hour <= 12:
				H1 = H1 - 1
			if sab > 12:
				H2 = H2 - 1
			time = H1 + H2
			while time >= 8:
				rang = rang + 1
				time = time - 8
				if (dateEnd.weekday() == 5 or dateEnd.weekday() == 6) and time < 8:
					time = time * 2
			time = time - 1
			minutes = timeEnd.minute - timeInit.minute
			if minutes < 0:
				minutesInit = 60 - timeInit.minute
				minutes = timeEnd.minute + minutesInit
			else:
				time = time + 1
			if dateEnd.weekday() == 6:
				rang = rang - 1
			if rang < 0:
				return "Error en las fechas."
			else:
				res['D'],res['H'],res['M'] = rang,time,minutes
		return res
	
	def solicitar(self):
		if self.dias != 0 or self.minutos != 0 or self.horas != 0:
			if not self.name:
				if not self.sequence_id.id:
					obj_sequence = self.env["ir.sequence"].search([('name','=','permisos')])
					if not obj_sequence.id:
						values = {'name': 'permisos',
							'prefix': 'Permiso ',
							'padding':4,}
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

			activity = self.env['mail.activity'].sudo().create({
				'activity_type_id': self.env.ref('permisos.mail_activity_permiso').id,
				'note': _('Prueba'),
				'res_id': self.id,
				'res_model_id': self.env.ref('permisos.model_hr_employee_permisos').id,
				'user_id': self.sudo().employe_id.parent_id.user_id.id or false,
			})
			activity._onchange_activity_type_id()
			self.write({'state': 'pendiente'})
			template = self.env.ref('permisos.email_template_permiso_solicitud')
			email_values = {'email_to': self.employe_id.work_email}
			template.send_mail(self.id, email_values=email_values, force_send=True)

			self.env.user.notify_success(message='Solicitud enviada correctamente')

			template_jefe = self.env.ref('permisos.email_template_permiso_solicitud_jefe')
			email_values_jefe = {'email_to': self.sudo().employe_id.parent_id.work_email}
			template_jefe.send_mail(self.id, email_values=email_values_jefe, force_send=True)
		else:
			self.env.user.notify_warning(message='Verificar fechas, no puede solicitar 0 dias, 0 horas, 0 minutos')

	def vacaciones_restantes(self,operacion):
		minutos_actuales = (self.employe_id.permisos_dias * 480) + (self.employe_id.permisos_horas * 60 ) + self.employe_id.permisos_minutos
		minutos_solicitados = (self.dias * 480 ) + (self.horas * 60 ) + self.minutos
		minutos_resultante = minutos_actuales - minutos_solicitados if operacion == 'resta'  else minutos_actuales + minutos_solicitados
		dias = 0
		horas = 0
		if minutos_resultante % 480 == 0:
			dias = minutos_resultante / 480
			minutos_resultante = 0
		else:
			dias = int(minutos_resultante / 480)
			minutos_resultante = minutos_resultante - (dias * 480)

		if minutos_resultante % 60 == 0:
			horas = minutos_resultante / 60
			minutos_resultante = 0
		else:
			horas = int(minutos_resultante / 60)
			minutos_resultante = minutos_resultante - (horas * 60)

		return dias, horas, minutos_resultante
			
	def aprobar(self,tipo='personal'):
		self.write({'state': 'aprobado'})
		if self.cargo == 'vaciones':
			dias, horas, minutos_resultante = self.vacaciones_restantes('resta')
			self.employe_id.sudo().write({'permisos_dias': dias,
							'permisos_horas': horas,
							'permisos_minutos': minutos_resultante})
		if tipo == 'personal':
			self.env.user.notify_success(message='Permiso aprobado')

		template_jefe = self.env.ref('permisos.email_template_permiso_solicitud_aprobado')
		email_values_jefe = {'email_to': 'erodriguez@megatk.com'}
		template_jefe.send_mail(self.id, email_values=email_values_jefe, force_send=True)

	def rechazar(self):
		template = self.env.ref('permisos.email_template_permiso_solicitud_denegar')
		email_values = {'email_to': self.employe_id.work_email}
		template.send_mail(self.id, email_values=email_values, force_send=True)
		self.write({'state': 'denegado'})
		self.env.user.notify_danger(message='Permiso denegado')


	def cancelar(self):
		dias, horas, minutos_resultante = self.vacaciones_restantes('suma')

		self.write({'state': 'cancelado'})
		self.employe_id.sudo().write({'permisos_dias': dias,
							'permisos_horas': horas,
							'permisos_minutos': minutos_resultante})
		self.env.user.notify_danger(message='Permiso cancelado')

	def back_draft(self):
		self.cancelar()
		self.write({'state': 'draft'})


	def unlink(self):
		for rec in self:
			if rec.state == 'draft':
				return super(HrPermisos, self).unlink()
			else:
				raise Warning(_('El permiso solo puede ser eliminado en estado de borrador'))

	def vacaciones_restantes1(self,minutos_actuales,minutos_solicitados):
		minutos_resultante = minutos_actuales + minutos_solicitados
		dias = 0
		horas = 0
		if minutos_resultante % 480 == 0:
			dias = minutos_resultante / 480
			minutos_resultante = 0
		else:
			dias = int(minutos_resultante / 480)
			minutos_resultante = minutos_resultante - (dias * 480)

		if minutos_resultante % 60 == 0:
			horas = minutos_resultante / 60
			minutos_resultante = 0
		else:
			horas = int(minutos_resultante / 60)
			minutos_resultante = minutos_resultante - (horas * 60)

		return dias, horas, minutos_resultante

	def vacaciones_por_ley(self):
		año1 = 10 * 480
		año2 = 12 * 480
		año3 = 15 * 480
		añomas = 20 * 480
		nic = 2.5 * 480
		dias = 0
		horas = 0 
		minutos_resultante = 0
		hoy = fields.Date.context_today(self)
		employee_ids = self.env["hr.employee"].sudo().search([])
		for employe_id in employee_ids:
			minutos_actuales = (employe_id.permisos_dias * 480) + (employe_id.permisos_horas * 60 ) + employe_id.permisos_minutos
			if employe_id.country_of_birth:
				if employe_id.country_of_birth.code == 'HN':
					if employe_id.fecha_ingreso:
						if employe_id.fecha_ingreso.day == hoy.day and employe_id.fecha_ingreso.month == hoy.month:
							if hoy.year - employe_id.fecha_ingreso.year == 1:
								dias, horas, minutos_resultante = self.vacaciones_restantes1(minutos_actuales, año1)
							elif hoy.year - employe_id.fecha_ingreso.year == 2:
								dias, horas, minutos_resultante = self.vacaciones_restantes1(minutos_actuales, año2)
							elif hoy.year - employe_id.fecha_ingreso.year == 3:
								dias, horas, minutos_resultante = self.vacaciones_restantes1(minutos_actuales, año3)
							else:
								dias, horas, minutos_resultante = self.vacaciones_restantes1(minutos_actuales, añomas)
							employe_id.sudo().write({'permisos_dias': dias,
								'permisos_horas': horas,
								'permisos_minutos': minutos_resultante})
							template = self.env.ref('permisos.email_template_vaciones_automaticas')
							email_values = {'email_to': 'erodriguez@megatk.com',
											'subject': "Vacaciones aplicadas a " + str(employe_id.name),
											'body_html': "Estimado Sr(a) <b>Rodriguez</b>.<br/><br/> Se notifica que las vacaciones han sido aplicadas<br/><br/> <b>Años cumplidos</b>: " + str(hoy.year - employe_id.fecha_ingreso.year) + '<br/>'+
											'<b>Vacaciones disponibles</b>: ' + str(dias) + ' dias, ' + str(horas) + ' horas, ' + str(minutos_resultante) + ' minutos' }
							template.send_mail(self.id, email_values=email_values, force_send=True)
				elif employe_id.country_of_birth.code == 'NI':
					if employe_id.fecha_ingreso:
						if employe_id.fecha_ingreso.day == hoy.day:
							dias, horas, minutos_resultante = self.vacaciones_restantes1(minutos_actuales, nic)
							employe_id.sudo().write({'permisos_dias': dias,
								'permisos_horas': horas,
								'permisos_minutos': minutos_resultante})
							template = self.env.ref('permisos.email_template_vaciones_automaticas')
							email_values = {'email_to': 'erodriguez@megatk.com',
											'subject': "Vacaciones aplicadas a " + str(employe_id.name),
											'body_html': 'Estimado Sr(a) <b>Rodriguez</b>.<br/><br/> Se notifica que las vacaciones han sido aplicadas <br/><br/><b>2.5 dias</b> por mes cumplido <br/>' +
													'<b>Vacaciones disponibles</b>: ' + str(dias) + ' dias, ' + str(horas) + ' horas, ' + str(minutos_resultante) + ' minutos' }
							template.send_mail(self.id, email_values=email_values, force_send=True)