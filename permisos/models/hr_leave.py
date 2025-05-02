# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, time, date, timedelta
import pytz
import logging


_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = "hr.leave"
    _description = "Permisos Generales"

    
    datetm_from = fields.Datetime('datetm_from')
    datetm_to = fields.Datetime('datetm_to')
    cubierto_employee_id = fields.Many2one(
        'hr.employee', string='Ausencia cubierta', copy=False,)
    reporto = fields.Selection([('anticipado', 'Anticipado'), ('llamada', 'Llamada'), ('mensaje', 'Mensaje'), (
        'noreporto', 'No reporto')], default='anticipado', copy=False, required=True, track_visibility='onchange')
    duracion_prm = fields.Text('Duración', copy=False,)
    justificacion = fields.Text('Motivo', copy=False,)
    dias = fields.Integer(string='Días', default=1)
    horas = fields.Integer(string='Horas', default=0)
    minutos = fields.Integer(string='Minutos', default=0)
    
    dias_empleado = fields.Integer(string='Dias de vacaciones disponibles', related='employee_id.permisos_dias', store=False)
    horas_empleado = fields.Integer(string='Horas de vacaciones disponibles', related='employee_id.permisos_horas', store=False)
    minutos_empleado = fields.Integer(string='Minutos de vacaciones disponibles', related='employee_id.permisos_minutos', store=False)
    
    entrada = time(7, 0, 0)
    medio_dia = time(12, 0, 0)
    tarde = time(13, 0, 0)
    salida = time(16, 0, 0)
    

    @api.onchange('datetm_from', 'datetm_to')
    def _onchange_datetm_ft(self):
        if self.datetm_from and self.datetm_to:
            user_tz = pytz.timezone(
                self.env.context.get('tz') or self.env.user.tz)
            fecha_inicial = pytz.utc.localize(
                self.datetm_from).astimezone(user_tz)
            fecha_fin = pytz.utc.localize(self.datetm_to).astimezone(user_tz)

            if fecha_fin >= fecha_inicial:
                if self.request_unit_hours: 
                    permiso = self.calcularPermiso(fecha_inicial, fecha_fin)
                    if not isinstance(permiso, str):
                        self.dias = permiso['D']
                        self.horas = permiso['H']
                        self.minutos = permiso['M']
                        self.duracion_prm = "Dias: " + str(self.dias) + " Horas: " + str(self.horas) + " Minutos: " + str(self.minutos)
                        _logger.warning("Dias: " + str(self.dias) + " Horas: " + str(self.horas) + " Minutos: " + str(self.minutos))
                        
            else:
                self.dias = 0
                self.horas = 0
                self.minutos = 0
                self.env.user.notify_warning(
                    message='La fecha final debe ser mayor o igual a la inicial')
                

    @api.onchange('request_date_from', 'request_date_to', 'request_unit_half', 'request_date_from_period')
    def _onchange_request_datetm_ft(self):
        
        if not self.request_unit_half:
            if self.request_date_from and self.request_date_to:
                if self.request_date_to >= self.request_date_from:
                    #self.sudo().write({'dias': self.number_of_days_display})
                    self.dias = self.number_of_days_display
                    self.horas = 0
                    self.minutos = 0
                    self.duracion_prm = "Dias: " + str(self.dias) + " Horas: " + str(self.horas) + " Minutos: " + str(self.minutos)
                    _logger.warning("dia completo: " + str(self.dias) + str(self.horas) + str(self.minutos))
                    
                else:
                    self.dias = 0
                    self.horas = 0
                    self.minutos = 0
                    self.duracion_prm = "Dias: " + str(self.dias) + " Horas: " + str(self.horas) + " Minutos: " + str(self.minutos)
                    self.env.user.notify_warning(
                        message='La fecha final debe ser mayor o igual a la inicial')
                    
        else:
            if self.request_unit_half and self.request_date_from:
                self.dias = 0
                self.horas = self.number_of_hours_display
                self.minutos = 0
                self.duracion_prm = "Dias: " + str(self.dias) + " Horas: " + str(self.horas) + " Minutos: " + str(self.minutos)
                _logger.warning("unit half: " + str(self.dias) + str(self.horas) + str(self.minutos))
                
                
                
    
    def rangeDateft(self, dateInit, dateEnd):
        dates = [
            dateInit + timedelta(n) for n in range(int((dateEnd - dateInit).days))
        ]
        datesClear = []
        for date in dates:
            if date.weekday() != 6:
                datesClear.append(date)
        return len(datesClear)

    def calcularPermiso(self, datetimeInit, datetimeEnd):
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
            rang = self.rangeDateft(dateInit=dateInit, dateEnd=dateEnd)
            if rang == 0:
                return "Error en las fechas."
            else:
                res['D'], res['H'], res['M'] = rang, 0, 0
        if dateInit != dateEnd and timeInit != timeEnd:
            rang = self.rangeDateft(dateInit=dateInit, dateEnd=dateEnd)
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

    def vacaciones_restantes_empl(self, operacion):
        _logger.warning("Prueba de vacaciones restantes empl")
        minutos_actuales = (self.employee_id.permisos_dias * 480) + (
            self.employee_id.permisos_horas * 60) + self.employee_id.permisos_minutos
        _logger.warning(self.employee_id.permisos_dias)
        _logger.warning(self.employee_id.permisos_horas)
        _logger.warning(self.employee_id.permisos_minutos)
        minutos_solicitados = (self.dias * 480) + \
            (self.horas * 60) + self.minutos
        _logger.warning("datos solicitados")
        _logger.warning(self.dias)
        _logger.warning(self.horas)
        _logger.warning(self.minutos)
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

    def action_approve(self):
        _logger.warning(self.holiday_status_id.vacaciones)
        if self.holiday_status_id.vacaciones:
            _logger.warning("Datos antes de vaciaciones restantes empl")
            _logger.warning(self.dias)
            _logger.warning(self.horas)
            _logger.warning(self.minutos)
            dias, horas, minutos_resultante = self.vacaciones_restantes_empl(
                'resta')
           
            """self.env['hr.employee'].sudo().write({'permisos_dias': dias,
                                                 'permisos_horas': horas,
                                                 'permisos_minutos': minutos_resultante})"""
            self.employee_id.sudo().write({'permisos_dias': dias,
                                           'permisos_horas': horas,
                                           'permisos_minutos': minutos_resultante})
        else:
            self.env.user.notify_success(message='Permiso aprobado')

        return super(HrLeave, self).action_approve()
        """template_jefe = self.env.ref('permisos.email_template_permiso_solicitud_aprobado')
        email_values_jefe = {'email_to': 'erodriguez@megatk.com'}
        template_jefe.send_mail(self.id, email_values=email_values_jefe, force_send=True)"""
        
