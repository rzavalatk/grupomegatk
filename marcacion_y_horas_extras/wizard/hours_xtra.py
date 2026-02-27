# -*- coding: utf-8 -*-
from operator import length_hint
from odoo import api, fields, models
from odoo.exceptions import UserError
import datetime
import pytz


class WizarCamaronCuatrero(models.TransientModel):
    _name = "camaro.cuatrero"
    _description = "description"

    date_init = fields.Date("Fecha inicial", required=True)
    date_end = fields.Date("Fecha final", required=True)
    tipo_reporte = fields.Selection([
        ("1", "Llegadas tarde"),
        ("2", "Posibles Cuatreros"),
    ], string="Tipo de reporte", required=True)

    def _rangeDate(self, dateInit, dateEnd):
        dates = [
            dateInit + datetime.timedelta(n) for n in range(int((dateEnd - dateInit).days)+1)
        ]
        datesClear = []
        for date in dates:
            if date.weekday() != 6:
                datesClear.append(date.strftime("%Y-%m-%d"))
        return datesClear

    def _create_excel(self, date, reporte):
        obj = self.env["hr.employee.markings"]
        data_res = []
        data = obj.search(
            [
                ("date", "=", date),
            ]
        )
        for i in data:
            if obj.browse(i.id).filter_camaron_cuatrero(reporte):
                temp = {
                    "Fecha": i.date,
                    "Empleado": i.employee.name,
                    "Hora": i.hour,
                }
                data_res.append(temp)
        return data_res

    @api.model
    def filter_camaron_cuatrero(self, vals):
        data_res = []

        if vals[0]["date_init"] == vals[0]["date_end"]:
            data_res = self._create_excel(
                vals[0]["date_init"], vals[0]["tipo_reporte"])
        elif vals[0]["date_init"] > vals[0]["date_end"]:
            raise UserError('La fecha inicial no puede ser mayor a la final')
        else:
            date1 = datetime.datetime.strptime(
                vals[0]["date_init"]+" 00:00:00",'%Y-%m-%d %H:%M:%S')
            date2 = datetime.datetime.strptime(
                vals[0]["date_end"]+" 23:59:59",'%Y-%m-%d %H:%M:%S')
            rangeDates = self._rangeDate(date1,date2)
            for date in rangeDates:
                temp = self._create_excel(date, vals[0]["tipo_reporte"])
                data_res = data_res + temp
        if len(data_res) != 0:
            return {
                'data': data_res,
                'empty': False,
                'length': len(data_res)
            }
        else:
            return {
                'empty': True,
            }


"""class WizardHourXtra(models.TransientModel):
    _name = "hours.xtras"

    employee_ids = fields.Many2many(
        "hr.employee", "user_id", string="Empleados")
    date = fields.Date("Fecha a ingresar")

    def _evalueIndex(self, index, array):
        try:
            array[index]
        except:
            return False
        return True

    #@api.model
    def dat_form_custom(self, vals):
        data = self.env["hr.employee.markings"].search(
            [
                "&",
                ("employee", "in", vals[0]["employee_ids"]),
                ("date", "=", vals[0]["date"]),
            ]
        )
        data_res = []
        for i in vals[0]["employee_ids"]:
            fil = list(filter(lambda x: x.employee.id == i, data))
            diff = self.env["hr.employee.markings"].hour_extra(
                fil[0].hour, fil[1].hour)
            temp = {
                "Empleado": fil[0].employee.name,
                "Fecha": vals[0]["date"],
                "Entrada": fil[0].hour,
                "Salida": fil[1].hour,
                "Horas extra": diff
            }
            data_res.append(temp)
        return data_res"""
