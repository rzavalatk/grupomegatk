# -*- coding: utf-8 -*-

from odoo import models, api, fields
import datetime
from datetime import date, time


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
        dateTimeDifferenceInHours = dateTimeDifference.total_seconds() / 3600
        h = int(dateTimeDifferenceInHours)
        mt = (dateTimeDifferenceInHours - h) * 60
        m = int(round(mt,0))
        s = int((mt-int(mt))*60)
        print("/////////////",[h,m,s],'mt:',mt,'s:',s,"////////////")
        return [h,m,s]
    
    def _hour_extra(self):
        try:
            ref_hour_enter = time(8,6,0)
            ref_hour_exit = time(17,6,0)
            ref_hour = self._diff_hours(ref_hour_enter,ref_hour_exit)
            hourEnter = self.enter.split(':')
            hourExit = self.exit.split(':')
            time1 = self._arr_to_time(hourEnter)
            time2 =  self._arr_to_time(hourExit)
            dateTimeDifference = {}
            if time1 < ref_hour_enter:
                dateTimeDifference = self._diff_hours(ref_hour_enter,time2)
            else:
                dateTimeDifference = self._diff_hours(time1,time2)
            ref = self._arr_to_time(ref_hour)
            res = self._arr_to_time(dateTimeDifference)
            pre_final = self._diff_hours(ref,res)
            final=[]
            for item in pre_final:
                if item < 10:
                    final.append(f"0{item}")
                else:
                    final.append(f"{item}")
                    
            self.hour_extra = f"{final[0]}:{final[1]}:{final[2]}" 
        except:
            self.hour_extra = "No hay horas"

    name = fields.Char(compute=_name_employee)
    employee = fields.Many2one("hr.employee", string="Empleado")
    date = fields.Date(string="Fecha")
    enter = fields.Char(string="Entrada", default="00:00:00")
    exit = fields.Char(string="Salida", default="00:00:00")
    hour_extra = fields.Char("Horas extras",compute=_hour_extra)
    
    
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
    def csv_download(self,filter=[]):
        data = self.env['hr.employee.markings'].search(filter)
        res = data.export_data(
            ['id', 'employee/name', 'date', 'enter', 'exit'], True)
        csv = """ID externo,Empleado,Fecha,Entrada,Salida,\n"""
        if len(res['datas']) > 0:
            for row in res['datas']:
                csv_row = ""
                for item in row:
                    csv_row += "{},".format(item)
                csv += "{}\n".format(csv_row[:-1])
        return csv
