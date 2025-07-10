# -*- coding: utf-8 -*-
from odoo import fields, models
from datetime import datetime, time
from pytz import timezone, utc

import logging

_logger = logging.getLogger(__name__)


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    
    def vacaciones_restantes_empl(self, operacion, employee_id, allocation):
        _logger.warning("Prueba de vacaciones restantes empl")
        
        minutos_actuales = (employee_id.permisos_dias * 480) + (
            employee_id.permisos_horas * 60) + employee_id.permisos_minutos
        minutos_solicitados = allocation.number_of_days_display * 480
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
    def action_confirm(self): 
        for allocation in self:
            if allocation.holiday_status_id.vacaciones:    
                if allocation.employee_ids:
                    for employee_id in allocation.employee_ids:
                        dias, horas, minutos_resultante = self.vacaciones_restantes_empl(
                        'suma', employee_id, allocation)
                        employee_id.sudo().write({'permisos_dias': dias,
                                                    'permisos_horas': horas,
                                                    'permisos_minutos': minutos_resultante})
                elif allocation.employee_id:
                    employee_id = allocation.employee_id
                    dias, horas, minutos_resultante = self.vacaciones_restantes_empl(
                    'suma', employee_id, allocation)
                    employee_id.sudo().write({'permisos_dias': dias,
                                                'permisos_horas': horas,
                                                'permisos_minutos': minutos_resultante})
            else:
                self.env.user.notify_success(message='Asignación aprobada')
            return super(HrLeaveAllocation, self).action_confirm()
    
    def action_refuse(self):
        for allocation in self:
            if allocation.holiday_status_id.vacaciones:    
                if allocation.employee_ids:
                    for employee_id in allocation.employee_ids:
                        dias, horas, minutos_resultante = self.vacaciones_restantes_empl(
                        'resta', employee_id, allocation)
                        employee_id.sudo().write({'permisos_dias': dias,
                                                    'permisos_horas': horas,
                                                    'permisos_minutos': minutos_resultante})
                elif allocation.employee_id:
                    employee_id = allocation.employee_id
                    dias, horas, minutos_resultante = self.vacaciones_restantes_empl(
                    'resta', employee_id, allocation)
                    employee_id.sudo().write({'permisos_dias': dias,
                                                'permisos_horas': horas,
                                                'permisos_minutos': minutos_resultante})
            else:
                self.env.user.notify_success(message='Asignación rechazada')
            return super(HrLeaveAllocation, self).action_refuse()
        
    