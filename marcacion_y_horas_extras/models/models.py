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
    _description = "description"

    def _name_employee(self):
        self.name = self.employee.name
        
        
    def _arr_to_time(self,timer):
        return time(int(timer[0]),int(timer[1]),int(timer[2]))
        
        
    def _diff_hours(self, a, b, typ=False):
        dateTimeA = datetime.datetime.combine(datetime.date.today(), a)
        dateTimeB = datetime.datetime.combine(datetime.date.today(), b)
        dateTimeDifference = dateTimeB - dateTimeA
        return (datetime.datetime.min + dateTimeDifference).time() if typ == False else  dateTimeDifference
    
    """def hour_extra(self,enter,exit):
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
            return "No hay horas"""

    name = fields.Char(compute=_name_employee)
    employee = fields.Many2one("hr.employee", string="Empleado")
    date = fields.Date(string="Fecha")
    hour = fields.Char(string="Hora", default="00:00:00")
    
    
    #@api.one
    def _search_in_out(self,refere):
        employee = self.env['hr.employee.markings'].search(['&',('employee','=',self.employee.id),('date','=',self.date)])
        res = {}
        temp = False
        for item in employee:
            t1 = self._arr_to_time(item.hour.split(':'))
            if temp:
                if temp < t1:
                    res['out'] = t1
                    res['in'] = temp
                else:
                    res['in'] = t1
                    res['out'] = temp
            else:
                temp = t1
        return res

    
    
    def filter_camaron_cuatrero(self,report):
        ref_hour_enter = time(8,7,0)
        ref_hour_exit = time(17,6,0)
        hour = self.hour.split(':')
        t1 = self._arr_to_time(hour)
        if report == 1:
            try:
                ht=self._diff_hours(ref_hour_enter,t1).strftime("%H:%M:%S")
            except:
                ht=self._diff_hours(t1,ref_hour_enter).strftime("%H:%M:%S")          
            ht = int(ht.split(':')[0])
            res = self._search_in_out(ref_hour_enter)[0]
            if len(res) == 2:
                if t1 > ref_hour_enter and ht < 8:
                    try:
                        if res['in'] == t1:
                            return True
                    except:
                        return False
                return False    
            else:
                return True
        elif report == 2:
            try:
                ht=self._diff_hours(ref_hour_exit,t1).strftime("%H:%M:%S")
            except:
                ht=self._diff_hours(t1,ref_hour_exit).strftime("%H:%M:%S")
            ht = int(ht.split(':')[0])
            res = self._search_in_out(ref_hour_exit)[0]
            if len(res) == 2:
                if t1 < ref_hour_exit and ht < 8:
                    try:
                        if res['out'] == t1:
                            return True
                    except:
                        return False
                return False    
            else:
                return True
            

    #@api.model
    def open_wizard(self):
        return {
            'name': "Ingreso masivo de marcaciones",
            'type': "ir.actions.act_window",
            'res_model': "making.inside",
            'views': [[False, 'form']],
            'target': "new",
            'view_mode': "form",
            #'view_type': "form",
        }
    
    #@api.model
    """def open_generate_hours_xtra(self):
        return {
            'name': "Gererar horas extra",
            'type': "ir.actions.act_window",
            'res_model': "hours.xtras",
            'views': [[False, 'form']],
            'target': "new",
            'view_mode': "form",
           #'view_type': "form",
        }"""
        
    #@api.model
    def open_generate_camaron_cuatrero(self):
        return {
            'name': "Llegadas tarde",
            'type': "ir.actions.act_window",
            'res_model': "camaro.cuatrero",
            'views': [[False, 'form']],
            'target': "new",
            'view_mode': "form",
            #'view_type': "form",
        }

    #@api.model
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
