# -*- coding: utf-8 -*-
from odoo import api, fields, models


class WizardHourXtra(models.TransientModel):
    _name = "hours.xtras"

    employee_ids = fields.Many2many("hr.employee", "user_id", string="Empleados")
    date = fields.Date("Fecha a ingresar")

    def _evalueIndex(self, index, array):
        try:
            array[index]
        except:
            return False
        return True

    @api.model
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
            fil = list(filter(lambda x: x.employee.id == i,data))
            diff = self.env["hr.employee.markings"].hour_extra(fil[0].hour,fil[1].hour)
            temp = {
                "Empleado": fil[0].employee.name,
                "Fecha": vals[0]["date"],
                "Entrada": fil[0].hour,
                "Salida": fil[1].hour,
                "Horas extra": diff
            }
            data_res.append(temp)
        return data_res
