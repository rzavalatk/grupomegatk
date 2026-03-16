# -*- coding: utf-8 -*-
from odoo import fields, models
from datetime import datetime, time
from pytz import timezone, utc

import logging

_logger = logging.getLogger(__name__)


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    
    asig_auto = fields.Boolean('Asignación automática')
    
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

    def _update_vacation_balances(self, operacion):
        for allocation in self:
            if operacion == 'suma' and allocation.asig_auto:
                continue
            if allocation.holiday_status_id.vacaciones:
                if allocation.employee_ids:
                    for employee_id in allocation.employee_ids:
                        dias, horas, minutos_resultante = self.vacaciones_restantes_empl(
                        operacion, employee_id, allocation)
                        employee_id.sudo().write({'permisos_dias': dias,
                                                    'permisos_horas': horas,
                                                    'permisos_minutos': minutos_resultante})
                elif allocation.employee_id:
                    employee_id = allocation.employee_id
                    dias, horas, minutos_resultante = self.vacaciones_restantes_empl(
                    operacion, employee_id, allocation)
                    employee_id.sudo().write({'permisos_dias': dias,
                                                'permisos_horas': horas,
                                                'permisos_minutos': minutos_resultante})

    def action_confirm(self):
        self._update_vacation_balances('suma')
        super_action_validate = getattr(super(HrLeaveAllocation, self), 'action_validate', None)
        if super_action_validate:
            return super_action_validate()
        super_action_confirm = getattr(super(HrLeaveAllocation, self), 'action_confirm', None)
        if super_action_confirm:
            return super_action_confirm()

    def action_validate(self):
        self._update_vacation_balances('suma')
        super_action_validate = getattr(super(HrLeaveAllocation, self), 'action_validate', None)
        if super_action_validate:
            return super_action_validate()
        super_action_confirm = getattr(super(HrLeaveAllocation, self), 'action_confirm', None)
        if super_action_confirm:
            return super_action_confirm()

    def action_refuse(self):
        self._update_vacation_balances('resta')
        super_action_refuse = getattr(super(HrLeaveAllocation, self), 'action_refuse', None)
        if super_action_refuse:
            return super_action_refuse()

        for allocation in self:
            if not allocation.holiday_status_id.vacaciones:
                else:
                self.env.user.notify_success(message='Asignación rechazada')
        return True
        
    