# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import calendar
import datetime
import pytz

import logging

_logger = logging.getLogger(__name__)

class HrPermisos(models.Model):
    _name = 'hr.employee.permisos'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Permisos Generales"

    # @api.model
    def solicitante(self):
        try:
            ctx = self._context
            obj_prestamo = self.env[ctx["active_model"]].browse(
                ctx['active_id'])
            return obj_prestamo.id
        except Exception as e:
            return 0

    name = fields.Char('Permiso', copy=False)
    fecha_inicio = fields.Datetime(string='Desde: ', required=True)
    fecha_inicio_txt = fields.Char(string='Desde')
    fecha_fin = fields.Datetime(string='Hasta: ', required=True)
    fecha_fin_txt = fields.Char(string='Hasta')
    cargo = fields.Selection([('vaciones', 'Vacaciones'), ('deduccion', 'Dedución de sueldo'), ('sincargo', 'Sin cargo'), (
        'incapacidad', 'Incapacidad')], default='vaciones', copy=False, required=True, track_visibility='onchange')
    reporto = fields.Selection([('anticipado', 'Anticipado'), ('llamada', 'Llamada'), ('mensaje', 'Mensaje'), (
        'noreporto', 'No reporto')], default='anticipado', copy=False, required=True, track_visibility='onchange')
    employe_id = fields.Many2one('hr.employee', string='Solicitante',
                                 default=solicitante, required=True, track_visibility='onchange')
    cubierto_employe_id = fields.Many2one(
        'hr.employee', string='Ausencia cubierta', copy=False,)
    justificacion = fields.Text('Motivo', copy=False)
    state = fields.Selection([('draft', 'Borrador'), ('pendiente', 'Pendiente'), ('aprobado', 'Aprobado'), ('denegado',
                             'Denegado'), ('cancelado', 'Cancelado')], string="Estado", default='draft', copy=False, track_visibility='onchange')
    dias = fields.Integer(string='Días', default=0)
    horas = fields.Integer(string='Horas', default=0)
    minutos = fields.Integer(string='Minutos', default=0)
    department_id = fields.Integer(string="Departamento")
    sequence_id = fields.Many2one('ir.sequence', "Prestamo")
    por_empresa = fields.Boolean('Por Empresa:', default=False)
    hora_prueba = fields.Datetime('Hora')

    @api.onchange('fecha_fin', 'fecha_inicio')
    def _onchange_fechafin(self):
        if self.fecha_fin and self.fecha_inicio:
            user_tz = pytz.timezone(
                self.env.context.get('tz') or self.env.user.tz)
            fecha_inicial = pytz.utc.localize(
                self.fecha_inicio).astimezone(user_tz)
            fecha_fin = pytz.utc.localize(self.fecha_fin).astimezone(user_tz)

            if fecha_fin >= fecha_inicial:
                permiso = self.calcularPermisos(fecha_inicial, fecha_fin)
                if not isinstance(permiso, str):
                    self.dias = permiso['D']
                    self.horas = permiso['H']
                    self.minutos = permiso['M']
                    self.fecha_inicio_txt = str(
                        fecha_inicial.strftime("%d-%m-%Y %H:%M:%S"))
                    self.fecha_fin_txt = str(
                        fecha_fin.strftime("%d-%m-%Y %H:%M:%S"))
            else:
                self.dias = 0
                self.horas = 0
                self.minutos = 0
                self.env.user.notify_UserError(
                    message='La fecha final debe ser mayor o igual a la inicial')

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
                res['D'], res['H'], res['M'] = days, hour, minutes
        if dateInit != dateEnd and timeInit == timeEnd:
            rang = self.rangeDate(dateInit=dateInit, dateEnd=dateEnd)
            if rang == 0:
                return "Error en las fechas."
            else:
                res['D'], res['H'], res['M'] = rang, 0, 0
        if dateInit != dateEnd and timeInit != timeEnd:
            rang = self.rangeDate(dateInit=dateInit, dateEnd=dateEnd)
            if rang < 0:
                return "Error en las fechas."
            rang = rang - 1
            sab = 0
            if (dateEnd.weekday() == 5 or dateEnd.weekday() == 6) and timeEnd.hour > 12:
                sab = timeEnd.hour - 12
            sab = timeEnd.hour - sab
            H1 = 16 - timeInit.hour
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
                res['D'], res['H'], res['M'] = rang, time, minutes
        return res

    def solicitar(self):
        if self.dias != 0 or self.minutos != 0 or self.horas != 0:
            if not self.name:
                if not self.sequence_id.id:
                    obj_sequence = self.env["ir.sequence"].search(
                        [('name', '=', 'permisos')], limit=1)
                    if not obj_sequence.id:
                        values = {'name': 'permisos',
                                  'prefix': 'Permiso ',
                                  'padding': 4, }
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
                'note': _('Solicitación de permiso'),
                'res_id': self.id,
                'res_model_id': self.env.ref('permisos.model_hr_employee_permisos').id,
                'user_id': self.employe_id.parent_id.user_id.id,
            })
            # activity._onchange_activity_type_id()
            self.write({'state': 'pendiente'})
            template = self.env.ref(
                'permisos.email_template_permiso_solicitud')
            email_values = {'email_to': self.employe_id.work_email}
            template.send_mail(
                self.id, email_values=email_values, force_send=True)

            self.env.user.notify_success(
                message='Solicitud enviada correctamente')

            template_jefe = self.env.ref(
                'permisos.email_template_permiso_solicitud_jefe')
            email_values_jefe = {
                'email_to': self.sudo().employe_id.parent_id.work_email}
            template_jefe.send_mail(
                self.id, email_values=email_values_jefe, force_send=True)
        else:
            self.env.user.notify_UserError(
                message='Verificar fechas, no puede solicitar 0 dias, 0 horas, 0 minutos')

    def vacaciones_restantes(self, operacion):
        minutos_actuales = (self.employe_id.permisos_dias * 480) + (
            self.employe_id.permisos_horas * 60) + self.employe_id.permisos_minutos
        minutos_solicitados = (self.dias * 480) + \
            (self.horas * 60) + self.minutos
        minutos_resultante = minutos_actuales - \
            minutos_solicitados if operacion == 'resta' else minutos_actuales + minutos_solicitados
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

    def aprobar(self, tipo='personal'):
        self.write({'state': 'aprobado'})
        if self.cargo == 'vaciones':
            dias, horas, minutos_resultante = self.vacaciones_restantes(
                'resta')
            self.employe_id.sudo().write({'permisos_dias': dias,
                                          'permisos_horas': horas,
                                          'permisos_minutos': minutos_resultante})
        if tipo == 'personal':
            self.env.user.notify_success(message='Permiso aprobado')

        template_jefe = self.env.ref(
            'permisos.email_template_permiso_solicitud_aprobado')
        email_values_jefe = {'email_to': 'erodriguez@megatk.com'}
        template_jefe.send_mail(
            self.id, email_values=email_values_jefe, force_send=True)

    def rechazar(self):
        template = self.env.ref(
            'permisos.email_template_permiso_solicitud_denegar')
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
                raise UserError(
                    _('El permiso solo puede ser eliminado en estado de borrador'))

    def vacaciones_restantes1(self, minutos_actuales, minutos_solicitados):
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

    def _enviar_correo_vacaciones_automaticas(self, employe_id, destinatarios, body_html):
        template = self.env.ref(
            'permisos.email_template_vaciones_automaticas', raise_if_not_found=False)
        asunto = "Vacaciones aplicadas a %s" % employe_id.name

        try:
            if template and self.ids:
                template.sudo().send_mail(
                    self.ids[0],
                    email_values={
                        'email_to': destinatarios,
                        'subject': asunto,
                        'body_html': body_html,
                    },
                    force_send=True)
            else:
                mail_values = {
                    'subject': asunto,
                    'body_html': body_html,
                    'email_to': destinatarios,
                }
                email_from = self.env.user.email_formatted or self.env.company.email or False
                if email_from:
                    mail_values['email_from'] = email_from
                self.env['mail.mail'].sudo().create(mail_values).send()
        except Exception:
            _logger.exception(
                'No se pudo enviar el correo de vacaciones automáticas para %s', employe_id.name)

    def _obtener_tipo_vacaciones_ley(self):
        leave_type_model = self.env['hr.leave.type'].sudo()
        leave_type_id = leave_type_model.search([
            ('vacaciones', '=', True),
            ('active', '=', True),
        ], limit=1)

        if not leave_type_id:
            leave_type_id = leave_type_model.search([
                ('active', '=', True),
                ('name', 'ilike', 'vac'),
            ], limit=1)
            if leave_type_id:
                valores = {'vacaciones': True}
                if 'allow_negative_balance' in leave_type_id._fields:
                    valores['allow_negative_balance'] = True
                if 'requires_allocation' in leave_type_id._fields:
                    valores['requires_allocation'] = 'no'
                leave_type_id.write(valores)
                _logger.warning(
                    'Se marcó automáticamente el tipo de ausencia %s como vacaciones para compatibilidad con el cron.',
                    leave_type_id.display_name)

        return leave_type_id

    def _fecha_segura(self, year, month, day):
        ultimo_dia = calendar.monthrange(year, month)[1]
        return datetime.date(year, month, min(day, ultimo_dia))

    @api.model
    def vacaciones_por_ley(self):
        _logger.warning('Iniciando proceso de asignación automática de vacaciones por ley')

        hoy = fields.Date.context_today(self)
        employee_ids = self.env['hr.employee'].sudo().search([('active', '=', True)])
        allocation_model = self.env['hr.leave.allocation'].sudo()
        leave_type_id = self._obtener_tipo_vacaciones_ley()

        if not leave_type_id:
            _logger.error(
                'No se encontró un tipo de ausencia activo para vacaciones. Configure un hr.leave.type y marque la casilla Vacaciones.')
            return False

        procesados = 0

        for employe_id in employee_ids:
            try:
                if not employe_id.country_of_birth or not employe_id.fecha_ingreso:
                    continue

                fecha_ingreso = fields.Date.to_date(employe_id.fecha_ingreso)
                if fecha_ingreso > hoy:
                    continue

                codigo_pais = (employe_id.country_of_birth.code or '').upper()
                if codigo_pais not in ('HN', 'NI'):
                    continue

                anios_cumplidos = hoy.year - fecha_ingreso.year - (
                    (hoy.month, hoy.day) < (fecha_ingreso.month, fecha_ingreso.day)
                )
                minutos_otorgados = 0
                allocation_name = False
                destinatarios = False

                if codigo_pais == 'HN':
                    if anios_cumplidos < 1:
                        continue

                    aniversario_actual = self._fecha_segura(
                        hoy.year, fecha_ingreso.month, fecha_ingreso.day)
                    if aniversario_actual > hoy:
                        continue

                    if anios_cumplidos == 1:
                        minutos_otorgados = 10 * 480
                    elif anios_cumplidos == 2:
                        minutos_otorgados = 12 * 480
                    elif anios_cumplidos == 3:
                        minutos_otorgados = 15 * 480
                    else:
                        minutos_otorgados = 20 * 480

                    allocation_name = 'Asignación de vacaciones por ley - HN - %s año(s)' % anios_cumplidos
                    destinatarios = 'dzuniga@megatk.com, erodriguez@megatk.com, dvasquez@megatk.com'

                else:
                    if fecha_ingreso >= hoy:
                        continue

                    corte_mes = self._fecha_segura(hoy.year, hoy.month, fecha_ingreso.day)
                    if corte_mes > hoy:
                        continue

                    minutos_otorgados = int(2.5 * 480)
                    allocation_name = 'Asignación de vacaciones por ley - NI - %s' % hoy.strftime('%Y-%m')
                    destinatarios = 'dzuniga@megatk.com'

                allocation_domain = [
                    ('holiday_status_id', '=', leave_type_id.id),
                    ('asig_auto', '=', True),
                    ('name', '=', allocation_name),
                ]
                if 'employee_ids' in allocation_model._fields:
                    allocation_domain.append(('employee_ids', 'in', employe_id.id))
                elif 'employee_id' in allocation_model._fields:
                    allocation_domain.append(('employee_id', '=', employe_id.id))

                leave_allocation = allocation_model.search(allocation_domain, limit=1)
                if leave_allocation:
                    _logger.info(
                        'El empleado %s ya tiene la asignación automática %s',
                        employe_id.name, allocation_name)
                    continue

                number_of_days = minutos_otorgados / 480.0
                allocation_vals = {
                    'holiday_status_id': leave_type_id.id,
                    'name': allocation_name,
                    'asig_auto': True,
                }

                if 'holiday_type' in allocation_model._fields:
                    allocation_vals['holiday_type'] = 'employee'

                if 'employee_ids' in allocation_model._fields:
                    allocation_vals['employee_ids'] = [(6, 0, [employe_id.id])]
                elif 'employee_id' in allocation_model._fields:
                    allocation_vals['employee_id'] = employe_id.id

                if 'number_of_days_display' in allocation_model._fields:
                    allocation_vals['number_of_days_display'] = number_of_days
                else:
                    allocation_vals['number_of_days'] = number_of_days

                leave_allocation = allocation_model.create(allocation_vals)
                if hasattr(leave_allocation, 'action_validate'):
                    leave_allocation.action_validate()
                elif hasattr(leave_allocation, 'action_confirm'):
                    leave_allocation.action_confirm()
                elif hasattr(leave_allocation, 'action_approve'):
                    leave_allocation.action_approve()

                minutos_actuales = (employe_id.permisos_dias * 480) + \
                    (employe_id.permisos_horas * 60) + employe_id.permisos_minutos
                dias, horas, minutos_resultante = self.vacaciones_restantes1(
                    minutos_actuales, minutos_otorgados)
                employe_id.sudo().write({
                    'permisos_dias': dias,
                    'permisos_horas': horas,
                    'permisos_minutos': minutos_resultante,
                })
                procesados += 1

                if destinatarios:
                    if codigo_pais == 'HN':
                        body_html = (
                            "Estimado Sr(a) <b>Rodriguez</b>.<br/><br/>"
                            "Se notifica que las vacaciones han sido aplicadas.<br/><br/>"
                            "<b>Años cumplidos</b>: %s<br/>"
                            "<b>Vacaciones disponibles</b>: %s dias, %s horas, %s minutos"
                        ) % (anios_cumplidos, dias, horas, minutos_resultante)
                    else:
                        body_html = (
                            'Estimado Sr(a) <b>Rodriguez</b>.<br/><br/>'
                            'Se notifica que las vacaciones han sido aplicadas.<br/><br/>'
                            '<b>2.5 dias</b> por mes cumplido.<br/>'
                            '<b>Vacaciones disponibles</b>: %s dias, %s horas, %s minutos'
                        ) % (dias, horas, minutos_resultante)

                    self._enviar_correo_vacaciones_automaticas(
                        employe_id, destinatarios, body_html)

            except Exception:
                _logger.exception(
                    'Error asignando vacaciones por ley al empleado %s (%s)',
                    employe_id.name, employe_id.id)

        _logger.warning('Proceso de vacaciones por ley finalizado. Empleados procesados: %s', procesados)
        return True
