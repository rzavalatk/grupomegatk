# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, time
from odoo import api, fields, models, tools, _
from pytz import pytz, timezone, utc

import logging
# obtenemos la zona horaria de Honduras
honduras_tz = pytz.timezone('America/Tegucigalpa')

_logger = logging.getLogger(__name__)


class LeaveRuleInput(models.Model):
    _inherit = 'hr.payslip'
    
    def get_inputs(self, contract_ids, date_from, date_to):
        
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
                        _logger.warning('Numero de dias y horas: %s , %s', leave[0].holiday_id.number_of_days_display, leave[0].holiday_id.number_of_hours_display)
                        
                        if result.get('code') == 'DED_PRM':
                            if leave[0].holiday_id.number_of_hours_display:
                                result['amount'] += leave[0].holiday_id.number_of_hours_display * costo_hora
                            else:
                                result['amount'] += leave[0].holiday_id.number_of_days_display * costo_dia
                        
        return res