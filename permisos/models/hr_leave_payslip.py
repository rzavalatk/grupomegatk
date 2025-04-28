# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, time
from odoo import api, fields, models, tools, _
import logging
from pytz import timezone
from pytz import utc
import pytz

# obtenemos la zona horaria de Honduras
honduras_tz = pytz.timezone('America/Tegucigalpa')

_logger = logging.getLogger(__name__)


class LeaveRuleInput(models.Model):
    _inherit = 'hr.payslip'
    
    def get_inputs(self, contract_ids, date_from, date_to):
        """This Compute the other inputs to employee payslip.
                           """
        res = super(LeaveRuleInput, self).get_inputs(contract_ids, date_from, date_to)
        contract_obj = self.env['hr.contract']
        contract_id = contract_obj.browse(contract_ids[0].id)
        emp_id = contract_obj.browse(contract_ids[0].id).employee_id
        
        day_from = datetime.combine(fields.Date.from_string(date_from),
                                        time.min)
        day_to = datetime.combine(fields.Date.from_string(date_to),
                                    time.max)
        
        day_leave_intervals = []

        # compute leave days
        leaves = {}
        calendar = contract_id.resource_calendar_id
        tz = timezone(calendar.tz)
        
        day_leave_intervals = contract_id.employee_id.list_leaves(day_from,
                                                                day_to,
                                                                calendar=contract_id.resource_calendar_id)
        
        multi_leaves = []
        for day, hours, leave in day_leave_intervals:
            work_hours = calendar.get_work_hours_count(
                tz.localize(datetime.combine(day, time.min)),
                tz.localize(datetime.combine(day, time.max)),
                compute_leaves=False,
            )
            if len(leave) > 1:
                for each in leave:
                    if each.id:
                        multi_leaves.append(each.holiday_id)
            else:
                if leave[0].holiday_id.holiday_status_id.deducciones:
                    for result in res:
                        costo_dia = contract_id.wage/30
                        costo_hora = contract_id.wage/8
                        
                        """if result.get('code') == 'DED_LLT':
                            result['amount'] += amount"""
        return res
                
                
    
        
        
        
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
                    if result.get('code') == 'DED_LLT':
                        result['amount'] += amount
        return res