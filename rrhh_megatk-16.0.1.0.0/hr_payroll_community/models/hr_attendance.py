# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, time
from odoo import models, fields
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
            
            if (str(days_of_week) == str(dia_permiso)):
                if (day_period == 'morning'): 
                    #calcular deducciones
                    start_time = datetime.strptime(str(str(int(start_time))+":00:00"), '%H:%M:%S').time()
                    start_time = datetime.combine(datetime.today(), start_time)
                    
                    if in_time > (start_time + timedelta(minutes=7)).time() and in_time < (start_time + timedelta(minutes=15)).time():
                        deduccion = costo_hora/2
                    elif in_time > (start_time + timedelta(minutes=16)).time() and in_time < (start_time + timedelta(minutes=30)).time():
                        deduccion = costo_hora
                    elif in_time > (start_time + timedelta(minutes=31)).time() and in_time < (start_time + timedelta(minutes=60)).time():
                        deduccion = costo_hora*2
                    elif in_time > (start_time + timedelta(minutes=61)).time() and in_time < (start_time + timedelta(minutes=90)).time():
                        deduccion = costo_hora*4
        
        return deduccion
            
    
    def get_inputs(self, contract_ids, date_from, date_to):
        """This Compute the other inputs to employee payslip.
                           """
        res = super(AttendanceRuleInput, self).get_inputs(contract_ids, date_from, date_to)
        
        
        
        contract_obj = self.env['hr.contract']
        contract_id = contract_obj.browse(contract_ids[0].id)
        emp_id = contract_obj.browse(contract_ids[0].id).employee_id
        attendances = self.env['hr.attendance'].search([('employee_id', '=', emp_id.id),('check_in', '>=', date_from),('check_out', '<=', date_to)])
        
        day_from = datetime.combine(fields.Date.from_string(date_from),
                                        time.min)
        day_to = datetime.combine(fields.Date.from_string(date_to),
                                    time.max)
        
        costo_dia = contract_id.wage/30
        costo_hora = costo_dia/8
        costo_minuto = costo_hora/60
        
        day_leave_intervals = []
        
        day_leave_intervals = contract_id.employee_id.list_leaves(day_from,
                                                                day_to,
                                                                calendar=contract_id.resource_calendar_id)
        
        multi_leaves = []
        for day, hours, leave in day_leave_intervals:
            
            if len(leave) > 1:
                for each in leave:
                    if each.id:
                        multi_leaves.append(each.holiday_id)
            else:
                if leave[0].holiday_id.holiday_status_id.deducciones:
                    for result in res:
                        if result.get('code') == 'DED_PRM':
                            total = leave[0].holiday_id.dias * costo_dia + leave[0].holiday_id.horas * costo_hora + leave[0].holiday_id.minutos * costo_minuto
                            result['amount'] += total
                            
        
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
                    if result.get('code') == 'DED_LLT':
                        result['amount'] += amount
        return res