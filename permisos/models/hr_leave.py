# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, time, date, timedelta
import pytz
import logging

from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


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
    justificacion = fields.Text('Motivo', copy=False,)
    formulario_entregado = fields.Boolean(string='Formulario entregado', default=False, copy=False,)
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
    
    request_hour_from = fields.Float(string='Hour from')
    
    request_hour_from_1 = fields.Selection([
            ('6', '6:00 AM'), ('6.25', '6:15 AM'), ('6.5', '6:30 AM'), ('6.75', '6:45 AM'),
            ('7', '7:00 AM'), ('7.25', '7:15 AM'), ('7.5', '7:30 AM'), ('7.75', '7:45 AM'),
            ('8', '8:00 AM'), ('8.25', '8:15 AM'), ('8.5', '8:30 AM'), ('8.75', '8:45 AM'),
            ('9', '9:00 AM'), ('9.25', '9:15 AM'), ('9.5', '9:30 AM'), ('9.75', '9:45 AM'),
            ('10', '10:00 AM'), ('10.25', '10:15 AM'), ('10.5', '10:30 AM'), ('10.75', '10:45 AM'),
            ('11', '11:00 AM'), ('11.25', '11:15 AM'), ('11.5', '11:30 AM'), ('11.75', '11:45 AM'),
            ('12', '12:00 PM'), ('12.25', '12:15 PM'), ('12.5', '12:30 PM'), ('12.75', '12:45 PM'),
            ('13', '1:00 PM'), ('13.25', '1:15 PM'), ('13.5', '1:30 PM'), ('13.75', '1:45 PM'),
            ('14', '2:00 PM'), ('14.25', '2:15 PM'), ('14.5', '2:30 PM'), ('14.75', '2:45 PM'),
            ('15', '3:00 PM'), ('15.25', '3:15 PM'), ('15.5', '3:30 PM'), ('15.75', '3:45 PM'),
            ('16', '4:00 PM'), ('16.25', '4:15 PM'), ('16.5', '4:30 PM'), ('16.75', '4:45 PM'),
            ('17', '5:00 PM'), ('17.25', '5:15 PM'), ('17.5', '5:30 PM'), ('17.75', '5:45 PM'),
            ('18', '6:00 PM')
        ],
        string='Hour from',
        default='7',
    )

    
    request_hour_to = fields.Float(string='Hour to')
    
    request_hour_to_1 = fields.Selection([
        ('6', '6:00 AM'), ('6.25', '6:15 AM'), ('6.5', '6:30 AM'), ('6.75', '6:45 AM'),
        ('7', '7:00 AM'), ('7.25', '7:15 AM'), ('7.5', '7:30 AM'), ('7.75', '7:45 AM'),
        ('8', '8:00 AM'), ('8.25', '8:15 AM'), ('8.5', '8:30 AM'), ('8.75', '8:45 AM'),
        ('9', '9:00 AM'), ('9.25', '9:15 AM'), ('9.5', '9:30 AM'), ('9.75', '9:45 AM'),
        ('10', '10:00 AM'), ('10.25', '10:15 AM'), ('10.5', '10:30 AM'), ('10.75', '10:45 AM'),
        ('11', '11:00 AM'), ('11.25', '11:15 AM'), ('11.5', '11:30 AM'), ('11.75', '11:45 AM'),
        ('12', '12:00 PM'), ('12.25', '12:15 PM'), ('12.5', '12:30 PM'), ('12.75', '12:45 PM'),
        ('13', '1:00 PM'), ('13.25', '1:15 PM'), ('13.5', '1:30 PM'), ('13.75', '1:45 PM'),
        ('14', '2:00 PM'), ('14.25', '2:15 PM'), ('14.5', '2:30 PM'), ('14.75', '2:45 PM'),
        ('15', '3:00 PM'), ('15.25', '3:15 PM'), ('15.5', '3:30 PM'), ('15.75', '3:45 PM'),
        ('16', '4:00 PM'), ('16.25', '4:15 PM'), ('16.5', '4:30 PM'), ('16.75', '4:45 PM'),
        ('17', '5:00 PM'), ('17.25', '5:15 PM'), ('17.5', '5:30 PM'), ('17.75', '5:45 PM'),
        ('18', '6:00 PM')
    ], string='Hour to', default='16',)
    
    #campos heredados
    holiday_status_id = fields.Many2one(
        "hr.leave.type", compute='_compute_from_employee_id', store=True, string="Time Off Type", required=True, readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]},
        domain="[('company_id', '=?', employee_company_id)]", tracking=True)
    
    number_of_days_display = fields.Float(
    string='Días calculados',
    compute='_compute_number_of_days_display',
    store=True
    )

    # En Odoo 18 ya no existe number_of_hours_display en hr.leave,
    # lo recreamos para soportar la lógica personalizada de este módulo.
    number_of_hours_display = fields.Float(
        string='Horas calculadas',
        compute='_compute_number_of_hours_display',
        store=False,
    )
    
    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def _check_holidays(self):
        for holiday in self:
            # 🛑 Si el tipo de permiso permite saldo negativo, omitir validación
            if holiday.holiday_status_id.allow_negative_balance:
                continue

            if (
                (not holiday.employee_id)
                or holiday.holiday_status_id.requires_allocation == 'no'
            ):
                continue

            requested_days = holiday.number_of_days or holiday.number_of_days_display or 0.0
            employees = holiday.employee_id

            unallocated_employees = []
            for employee in employees:
                leave_type_ctx = holiday.holiday_status_id.with_context(employee_id=employee.id)

                remaining_leaves = leave_type_ctx.remaining_leaves if 'remaining_leaves' in leave_type_ctx._fields else None
                virtual_remaining_leaves = leave_type_ctx.virtual_remaining_leaves if 'virtual_remaining_leaves' in leave_type_ctx._fields else None

                if remaining_leaves is None or virtual_remaining_leaves is None:
                    max_leaves = leave_type_ctx.max_leaves if 'max_leaves' in leave_type_ctx._fields else 0.0
                    leaves_taken = leave_type_ctx.leaves_taken if 'leaves_taken' in leave_type_ctx._fields else 0.0
                    remaining_leaves = max_leaves - leaves_taken
                    virtual_remaining_leaves = remaining_leaves

                if float_compare(remaining_leaves, requested_days, precision_digits=2) == -1 \
                        or float_compare(virtual_remaining_leaves, requested_days, precision_digits=2) == -1:
                    unallocated_employees.append(employee.name)

            if unallocated_employees:
                raise ValidationError(_(
                    'No hay suficientes días disponibles para este tipo de permiso.\n'
                    'Por favor revise también los permisos pendientes de validación.\n'
                    'Los empleados sin días asignados son:\n%s'
                ) % (', '.join(unallocated_employees)))
    
    @api.onchange('request_hour_from_1')
    def _onchange_request_hour_from_1(self):
        self.request_hour_from = float(self.request_hour_from_1) if self.request_hour_from_1 else False
        
    @api.onchange('request_hour_to_1')
    def _onchange_request_hour_to_1(self):
        self.request_hour_to = float(self.request_hour_to_1) if self.request_hour_to_1 else False
                
    @api.onchange('request_date_from', 'request_date_to', 'request_unit_half', 'request_date_from_period', 'request_unit_hours', 'holiday_status_id', 'request_hour_to', 'request_hour_from')
    def _onchange_request_datetm_ft(self):
        
        if not self.request_unit_half:
            
            if self.request_unit_hours:
                # Para permisos por horas personalizadas
                horas_display = self.number_of_hours_display
                valor_hora = int(horas_display)
                valor_minutos_decimal = horas_display - valor_hora
                
                # Convertir minutos decimales a enteros
                minutos_enteros = 0
                if valor_minutos_decimal == 0.25:
                    minutos_enteros = 15
                elif valor_minutos_decimal == 0.5:
                    minutos_enteros = 30
                elif valor_minutos_decimal == 0.75:
                    minutos_enteros = 45
                
                if self.is_saturday(self.request_date_from):
                    # Sábado: convertir horas display a horas físicas y luego a equivalentes
                    _logger.warning("Es sábado - calculando horas equivalentes")
                    
                    # Las horas display ya vienen duplicadas, obtener las físicas
                    horas_fisicas = valor_hora / 2
                    minutos_fisicos = minutos_enteros / 2
                    
                    # Convertir a horas equivalentes usando la función auxiliar
                    horas_equiv, minutos_equiv = self.calculate_saturday_equivalent_hours(
                        horas_fisicas, minutos_fisicos)
                    
                    self.dias = 0
                    self.horas = horas_equiv
                    self.minutos = minutos_equiv
                else:
                    # Día normal
                    self.dias = 0
                    self.horas = valor_hora
                    self.minutos = minutos_enteros
                    
            elif self.request_date_from and self.request_date_to:
                # Para permisos por días completos
                if self.is_saturday(self.request_date_from) and self.request_date_from == self.request_date_to:
                    # Sábado completo = 4 horas físicas = 8 horas equivalentes
                    self.dias = 0
                    self.horas = 8  # Día completo de sábado equivale a 8 horas
                    self.minutos = 0
                elif self.request_date_to >= self.request_date_from:
                    self.dias = self.number_of_days_display
                    self.horas = 0
                    self.minutos = 0
                else:
                    self.dias = 0
                    self.horas = 0
                    self.minutos = 0
                    if hasattr(self.env.user, 'notify_warning'):
                        self.env.user.notify_warning(
                            message='La fecha final debe ser mayor o igual a la inicial')        
        else:
            # Para medio día
            if self.request_unit_half and self.request_date_from:
                if self.is_saturday(self.request_date_from):
                    # Medio día sábado = 2 horas físicas = 4 horas equivalentes
                    self.dias = 0
                    self.horas = 4
                    self.minutos = 0
                else:
                    # Medio día normal = 4 horas
                    self.dias = 0
                    self.horas = int(self.number_of_hours_display)
                    self.minutos = 0
                    
        _logger.warning("RESULTADO FINAL - Días: %s, Horas: %s, Minutos: %s (Fecha: %s, Es sábado: %s)" % 
                       (self.dias, self.horas, self.minutos, 
                        self.request_date_from, 
                        self.is_saturday(self.request_date_from)))
                
    def is_saturday(self, fecha):
        """Verifica si una fecha es sábado"""
        return fecha and fecha.weekday() == 5
    
    def calculate_saturday_equivalent_hours(self, horas_fisicas, minutos_fisicos=0):
        """
        Convierte horas físicas de sábado a horas equivalentes
        Sábado: 4 horas físicas = 8 horas equivalentes (factor x2)
        """
        total_minutos_fisicos = (horas_fisicas * 60) + minutos_fisicos
        total_minutos_equivalentes = total_minutos_fisicos * 2  # Factor x2 para sábado
        
        horas_equivalentes = total_minutos_equivalentes // 60
        minutos_equivalentes = total_minutos_equivalentes % 60
        
        return int(horas_equivalentes), int(minutos_equivalentes)
    
    @api.model
    def validate_leave_calculation(self, dias, horas, minutos):
        """
        Valida que el cálculo de permiso sea correcto
        Retorna True si es válido, False si hay errores
        """
        # Verificar que no haya mezcla de positivos y negativos (inconsistente)
        signos = [1 if x >= 0 else -1 for x in [dias, horas, minutos] if x != 0]
        if len(set(signos)) > 1:
            _logger.error("Mezcla de valores positivos y negativos detectada - Días: %s, Horas: %s, Minutos: %s" % (dias, horas, minutos))
            return False
        
        # Verificar que los minutos estén en rango válido
        if abs(minutos) >= 60:
            _logger.warning("Minutos fuera de rango detectados: %s" % minutos)
            return False
        
        # Verificar que las horas estén en rango válido (si no hay días)
        if abs(horas) >= 8 and dias == 0:
            _logger.info("Se detectaron 8+ horas que podrían convertirse a días")
            
        # Log para valores negativos (saldo deudor)
        if dias < 0 or horas < 0 or minutos < 0:
            _logger.info("Saldo deudor detectado - Días: %s, Horas: %s, Minutos: %s" % (dias, horas, minutos))
            
        return True
    
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

    def vacaciones_restantes_empl(self, operacion, employee_id, leave):
        _logger.warning("Calculando vacaciones restantes - Operación: %s" % operacion)
        _logger.warning("Empleado actual - Días: %s, Horas: %s, Minutos: %s" % 
                       (employee_id.permisos_dias, employee_id.permisos_horas, employee_id.permisos_minutos))
        _logger.warning("Permiso solicitado - Días: %s, Horas: %s, Minutos: %s" % 
                       (leave.dias, leave.horas, leave.minutos))
        
        # Convertir todo a minutos para hacer el cálculo
        # 1 día = 8 horas = 480 minutos
        minutos_actuales = (employee_id.permisos_dias * 480) + (
            employee_id.permisos_horas * 60) + employee_id.permisos_minutos
        minutos_solicitados = (leave.dias * 480) + \
            (leave.horas * 60) + leave.minutos
            
        _logger.warning("Minutos actuales: %s, Minutos solicitados: %s" % 
                       (minutos_actuales, minutos_solicitados))
        
        # Realizar la operación
        if operacion == 'resta':
            minutos_resultante = minutos_actuales - minutos_solicitados
        else:  # suma
            minutos_resultante = minutos_actuales + minutos_solicitados
            
        _logger.warning("Minutos resultante: %s" % minutos_resultante)
        
        # Convertir de vuelta a días, horas y minutos
        dias = 0
        horas = 0
        
        if minutos_resultante >= 0:
            # CASO POSITIVO: Lógica original
            # Calcular días completos (480 minutos = 1 día)
            if minutos_resultante >= 480:
                dias = int(minutos_resultante / 480)
                minutos_resultante = minutos_resultante - (dias * 480)
            
            # Calcular horas completas (60 minutos = 1 hora)
            if minutos_resultante >= 60:
                horas = int(minutos_resultante / 60)
                minutos_resultante = minutos_resultante - (horas * 60)
            
            # Los minutos restantes
            minutos_restantes = int(minutos_resultante)
            
        else:
            # CASO NEGATIVO: Lógica para valores negativos
            _logger.warning("Procesando saldo negativo: %s minutos" % minutos_resultante)
            
            # Trabajar con el valor absoluto para hacer los cálculos
            minutos_absolutos = abs(minutos_resultante)
            
            # Calcular días completos negativos (480 minutos = 1 día)
            if minutos_absolutos >= 480:
                dias = -int(minutos_absolutos / 480)  # Negativo
                minutos_absolutos = minutos_absolutos - (abs(dias) * 480)
            
            # Calcular horas completas negativas (60 minutos = 1 hora)
            if minutos_absolutos >= 60:
                horas = -int(minutos_absolutos / 60)  # Negativo
                minutos_absolutos = minutos_absolutos - (abs(horas) * 60)
            
            # Los minutos restantes (negativos si quedan)
            if minutos_absolutos > 0:
                minutos_restantes = -int(minutos_absolutos)  # Negativo
            else:
                minutos_restantes = 0
            
            _logger.warning("Saldo negativo convertido - Días: %s, Horas: %s, Minutos: %s" % 
                           (dias, horas, minutos_restantes))
        
        _logger.warning("Resultado final - Días: %s, Horas: %s, Minutos: %s" % 
                       (dias, horas, minutos_restantes))

        # Validar el resultado antes de retornar
        if not self.validate_leave_calculation(dias, horas, minutos_restantes):
            _logger.error("Error en la validación del cálculo de vacaciones")

        return dias, horas, minutos_restantes

    def action_validate(self, check_state=True):
        for leave in self:
            if leave.holiday_status_id.vacaciones:
                # Determinar qué empleados procesar (compatibilidad entre versiones)
                if 'employee_ids' in leave._fields and leave.employee_ids:
                    employees_to_process = leave.employee_ids
                else:
                    employees_to_process = leave.employee_id
                
                for employee_id in employees_to_process:
                    if employee_id:  # Verificar que el empleado existe
                        dias, horas, minutos_resultante = self.vacaciones_restantes_empl(
                            'resta', employee_id, leave)
                        employee_id.sudo().write({'permisos_dias': dias,
                                                    'permisos_horas': horas,
                                                    'permisos_minutos': minutos_resultante})
                        _logger.warning("Permiso validado - Empleado: %s, Nuevos saldos - Días: %s, Horas: %s, Minutos: %s" % 
                                       (employee_id.name, dias, horas, minutos_resultante))
                        
                self.env.user.notify_success(message='Permiso de vacaciones aprobado y descontado del saldo')
            else:
                self.env.user.notify_success(message='Permiso aprobado')
                
        return super(HrLeave, self).action_validate(check_state=check_state)
        
    def action_refuse(self):
        for leave in self:
            if leave.state == 'validate':
                if leave.holiday_status_id.vacaciones:
                    # Determinar qué empleados procesar (compatibilidad entre versiones)
                    if 'employee_ids' in leave._fields and leave.employee_ids:
                        employees_to_process = leave.employee_ids
                    else:
                        employees_to_process = leave.employee_id
                    
                    for employee_id in employees_to_process:
                        if employee_id:  # Verificar que el empleado existe
                            dias, horas, minutos_resultante = self.vacaciones_restantes_empl(
                                'suma', employee_id, leave)
                            employee_id.sudo().write({'permisos_dias': dias,
                                                        'permisos_horas': horas,
                                                        'permisos_minutos': minutos_resultante})
                            _logger.warning("Permiso rechazado - Empleado: %s, Saldos restaurados - Días: %s, Horas: %s, Minutos: %s" % 
                                           (employee_id.name, dias, horas, minutos_resultante))
                            
                    self.env.user.notify_success(message='Permiso de vacaciones denegado y saldo restaurado')
                else:
                    self.env.user.notify_success(message='Permiso denegado')
                    
        return super(HrLeave, self).action_refuse()
    
    """def create(self, vals):
        vals['']
        vals['number_of_days_display'] = 
        return super(HrLeave, self).create(vals)"""
    
    @api.depends('request_date_from', 'request_date_to', 'request_unit_half', 'request_unit_hours')
    def _compute_number_of_hours_display(self):
        for leave in self:
            hours = 0.0

            # Permisos por horas personalizadas
            if leave.request_unit_hours and leave.request_date_from and leave.request_date_to:
                delta = leave.request_date_to - leave.request_date_from
                hours = delta.total_seconds() / 3600.0

            # Medio día
            elif leave.request_unit_half:
                hours = 4.0

            # Permisos por días completos
            elif leave.request_date_from and leave.request_date_to:
                delta_days = (leave.request_date_to - leave.request_date_from).days + 1
                hours = float(delta_days) * 8.0

            # Sábado: duplicar horas para mostrar equivalentes
            if leave.request_date_from and leave.request_date_from.weekday() == 5:
                hours *= 2

            leave.number_of_hours_display = hours
    @api.depends('request_date_from', 'request_date_to', 'request_unit_half', 'request_unit_hours')
    def _compute_number_of_days_display(self):
        for leave in self:
            if leave.request_unit_half:
                leave.number_of_days_display = 0.5
            elif leave.request_unit_hours:
                leave.number_of_days_display = leave.number_of_hours_display / 8.0 if leave.number_of_hours_display else 0
            elif leave.request_date_from and leave.request_date_to:
                delta = (leave.request_date_to - leave.request_date_from).days + 1
                leave.number_of_days_display = float(delta)
            else:
                leave.number_of_days_display = 0
