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

    def calcular_llegadat(self, in_time, salario):
        #Calcular costo por dia y hora en base al salario
        costo_dia = salario/30
        costo_hora = costo_dia/8
        deduccion = 0
        _logger.warning("costo_dia %s costo_hora %s",costo_dia,costo_hora)
        
        #calcular deducciones
        if in_time > datetime.strptime('07:05:00', '%H:%M:%S').time() and in_time < datetime.strptime('07:20:00', '%H:%M:%S').time():
            deduccion = costo_hora/2
        elif in_time > datetime.strptime('07:20:00', '%H:%M:%S').time() and in_time < datetime.strptime('07:35:00', '%H:%M:%S').time():
            deduccion = costo_hora
        elif in_time > datetime.strptime('07:35:00', '%H:%M:%S').time() and in_time < datetime.strptime('07:50:00', '%H:%M:%S').time():
            deduccion = costo_hora*2
        elif in_time > datetime.strptime('07:50:00', '%H:%M:%S').time() and in_time < datetime.strptime('08:00:00', '%H:%M:%S').time():
            deduccion = costo_hora*3
        elif in_time > datetime.strptime('08:00:00', '%H:%M:%S').time() and in_time < datetime.strptime('08:30:00', '%H:%M:%S').time():
            deduccion = costo_hora*4
        elif in_time > datetime.strptime('08:30:00', '%H:%M:%S').time() and in_time < datetime.strptime('16:00:00', '%H:%M:%S').time():
            deduccion = costo_dia
        
        return deduccion
    
    def get_inputs(self, contract_ids, date_from, date_to):
        """This Compute the other inputs to employee payslip.
                           """
        res = super(AttendanceRuleInput, self).get_inputs(contract_ids, date_from, date_to)
        contract_obj = self.env['hr.contract']
        contract_id = contract_obj.browse(contract_ids[0].id)
        emp_id = contract_obj.browse(contract_ids[0].id).employee_id
        attendances = self.env['hr.attendance'].search([('employee_id', '=', emp_id.id),('check_in', '>=', date_from),('check_out', '<=', date_to)])
        _logger.warning("attendances %s",attendances)
        for attendance in attendances:
            check_in_utc6 = attendance.check_in.astimezone(honduras_tz)
            check_out_utc6 = attendance.check_out.astimezone(honduras_tz)
            in_date = check_in_utc6.date()
            out_date = check_out_utc6.date()
            # obtenemos el horario de trabajo del contrato
            working_hours = contract_id.resource_calendar_id.working_hours

            for hours in working_hours:
                # obtenemos la información del horario de trabajo
                start_time = hours.hour_from
                end_time = hours.day_period
                days_of_week = hours.dayofweek
                _logger.warning("start_time %s day_period %s days_of_week %s",start_time,end_time,days_of_week)
            _logger.warning("in_date %s out_date %s",in_date,out_date)
            _logger.warning("date_from %s date_to %s",date_from,date_to)
            if in_date >= date_from and out_date <= date_to:
                in_time = check_in_utc6.time()
                out_time = check_out_utc6.time()
                _logger.warning("in_time %s out_time %s",in_time,out_time)
                amount = self.calcular_llegadat(in_time, contract_id.wage)
                _logger.warning("amount %s",amount)
                for result in res:
                    _logger.warning("result %s",result)
                    if result.get('code') == 'ATTD':
                        result['amount'] += amount
        _logger.warning("res %s",res)
        
        return res