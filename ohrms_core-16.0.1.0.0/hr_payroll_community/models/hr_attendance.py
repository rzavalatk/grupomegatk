# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models
import logging
import pytz

# obtenemos la zona horaria de Honduras
honduras_tz = pytz.timezone('America/Tegucigalpa')

_logger = logging.getLogger(__name__)


class AttendanceRuleInput(models.Model):
    _inherit = 'hr.payslip'

    def calcular_llegadat(self, in_time, dia_permiso, calendario_id, salario):
        #Calcular costo por dia y hora en base al salario
        costo_dia = salario/30
        costo_hora = costo_dia/8
        deduccion = 0
        
        # obtenemos el horario de trabajo del contrato
        working_hours = self.env['resource.calendar.attendance'].search([('calendar_id', '=', calendario_id)])
        for hours in working_hours:
            # obtenemos la información del horario de trabajo
            start_time = hours.hour_from
            day_period = hours.day_period
            days_of_week = hours.dayofweek
            
            _logger.warning("Horario: %s, %s, %s, %s", start_time, day_period, days_of_week, dia_permiso)
            
            if (days_of_week == dia_permiso):
                _logger.warning("SI entre al if 1")
                if (day_period == 'morning'): 
                    #calcular deducciones
                    _logger.warning("SI entre al if")
                    _logger.warning("1.Limites de hora: %s, %s", start_time + datetime.timedelta(minutes=7), start_time + datetime.timedelta(minutes=15))
                    if in_time > start_time + datetime.timedelta(minutes=7) and in_time < start_time + datetime.timedelta(minutes=15):
                        deduccion = costo_hora/2
                        _logger.warning("Limites de hora: %s, %s", start_time + datetime.timedelta(minutes=7), start_time + datetime.timedelta(minutes=15))
                    elif in_time > start_time + datetime.timedelta(minutes=16) and in_time < start_time + datetime.timedelta(minutes=30):
                        deduccion = costo_hora
                        _logger.warning("Limites de hora: %s, %s", start_time + datetime.timedelta(minutes=16), start_time + datetime.timedelta(minutes=30))
                    elif in_time > start_time + datetime.timedelta(minutes=31) and in_time < start_time + datetime.timedelta(minutes=60):
                        deduccion = costo_hora*2
                        _logger.warning("Limites de hora: %s, %s", start_time + datetime.timedelta(minutes=31), start_time + datetime.timedelta(minutes=60))
                    elif in_time > start_time + datetime.timedelta(minutes=61) and in_time < start_time + datetime.timedelta(minutes=90):
                        deduccion = costo_hora*4
                        _logger.warning("Limites de hora: %s, %s", start_time + datetime.timedelta(minutes=61), start_time + datetime.timedelta(minutes=90))
        
        return deduccion
    
    def get_inputs(self, contract_ids, date_from, date_to):
        """This Compute the other inputs to employee payslip.
                           """
        res = super(AttendanceRuleInput, self).get_inputs(contract_ids, date_from, date_to)
        contract_obj = self.env['hr.contract']
        contract_id = contract_obj.browse(contract_ids[0].id)
        emp_id = contract_obj.browse(contract_ids[0].id).employee_id
        attendances = self.env['hr.attendance'].search([('employee_id', '=', emp_id.id),('check_in', '>=', date_from),('check_out', '<=', date_to)])
        for attendance in attendances:
            check_in_utc6 = attendance.check_in.astimezone(honduras_tz)
            check_out_utc6 = attendance.check_out.astimezone(honduras_tz)
            in_date = check_in_utc6.date()
            out_date = check_out_utc6.date()
            if in_date >= date_from and out_date <= date_to:
                in_time = check_in_utc6.time()
                out_time = check_out_utc6.time()
                amount = self.calcular_llegadat(in_time, in_date.weekday(), contract_id.resource_calendar_id.id, contract_id.wage)
                for result in res:
                    if result.get('code') == 'ATTD':
                        result['amount'] += amount
        return res