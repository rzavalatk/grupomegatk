# -*- coding: utf-8 -*-

from odoo import models, api, fields
import datetime
from datetime import time


class ModuleEmployees(models.Model):
    _inherit = "hr.employee"

    marking_ids = fields.One2many(
        'hr.employee.markings', 'employee', string='Marcaciones')


class ModuleMarkings(models.Model):
    _name = "hr.employee.markings"

    def _name_employee(self):
        self.name = self.employee.name
        
        
    def _arr_to_time(self,timer):
        return time(int(timer[0]),int(timer[1]),int(timer[2]))
        
        
    def _diff_hours(self, a, b):
        dateTimeA = datetime.datetime.combine(datetime.date.today(), a)
        dateTimeB = datetime.datetime.combine(datetime.date.today(), b)
        dateTimeDifference = dateTimeB - dateTimeA
        return (datetime.datetime.min + dateTimeDifference).time()
    
    def hour_extra(self,enter,exit):
        try:
            ref_hour_enter = time(8,6,0)
            ref_hour_exit = time(17,6,0)
            ref_hour = self._diff_hours(ref_hour_enter,ref_hour_exit)
            hourEnter = enter.split(':')
            hourExit = exit.split(':')
            time1 = self._arr_to_time(hourEnter)
            time2 =  self._arr_to_time(hourExit)
            dateTimeDifference = self._diff_hours(time1,time2)
            pre_final = self._diff_hours(ref_hour,dateTimeDifference)
            return pre_final
        except:
            return "No hay horas"

    name = fields.Char(compute=_name_employee)
    employee = fields.Many2one("hr.employee", string="Empleado")
    date = fields.Date(string="Fecha")
    hour = fields.Char(string="Hora", default="00:00:00")
    
    
    @api.model
    def open_wizard(self):
        return {
            'name': "Ingreso masivo de marcaciones",
            'type': "ir.actions.act_window",
            'res_model': "making.inside",
            'views': [[False, 'form']],
            'target': "new",
            'view_mode': "form",
            'view_type': "form",
        }
    
    @api.model
    def open_generate_hours_xtra(self):
        return {
            'name': "Gererar horas extra",
            'type': "ir.actions.act_window",
            'res_model': "hours.xtras",
            'views': [[False, 'form']],
            'target': "new",
            'view_mode': "form",
            'view_type': "form",
        }

    @api.model
    def csv_download(self,filter=[]):
        data = self.env['hr.employee.markings'].search(filter)
        res = data.export_data(
            ['id', 'employee/name', 'date', 'hour'], True)
        data_res = []
        col = ["ID_Externo","Empleado","Fecha","Hora"]
        if len(res['datas']) > 0:
            for row in res['datas']:
                data_row = {}
                i = 0
                while i<4:
                    data_row[col[i]] = row[i]
                    i+=1
                data_res.append(data_row)
        return data_res
