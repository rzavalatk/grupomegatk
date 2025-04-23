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

    def calcular_llegadat(self, in_time):
        pass
    
    def get_inputs(self, contract_ids, date_from, date_to):
        """This Compute the other inputs to employee payslip.
                           """
        res = super(AttendanceRuleInput, self).get_inputs(contract_ids, date_from, date_to)
        contract_obj = self.env['hr.contract']
        emp_id = contract_obj.browse(contract_ids[0].id).employee_id
        attendances = self.env['hr.attendance'].search([('employee_id', '=', emp_id.id),('check_in', '>=', date_from),('check_out', '<=', date_to)])
        _logger.warning("attendances %s",attendances)
        for attendance in attendances:
            check_in_utc6 = attendance.check_in.astimezone(honduras_tz)
            check_out_utc6 = attendance.check_out.astimezone(honduras_tz)
            in_date = check_in_utc6.date()
            out_date = check_out_utc6.date()
            _logger.warning("in_date %s out_date %s",in_date,out_date)
            _logger.warning("date_from %s date_to %s",date_from,date_to)
            if in_date >= date_from and out_date <= date_to:
                in_time = attendance.check_in.time()
                out_time = attendance.check_out.time()
                _logger.warning("in_time %s out_time %s",in_time,out_time)
                amount = self.calcular_llegadat(in_time)
                """for result in res:
                    if state == 'approve' and amount != 0 and result.get('code') == 'SAR':
                        result['amount'] = amount"""
        return res