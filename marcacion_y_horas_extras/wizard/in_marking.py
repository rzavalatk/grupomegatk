# -*- coding: utf-8 -*-
from odoo import api, fields, models
import datetime
from odoo.exceptions import ValidationError


class WizardInMarking(models.TransientModel):
    _name = 'making.inside'

    marking_ids = fields.Many2many(
        'hr.employee', 'user_id', string='Empleados')
    more_one_day = fields.Boolean('Rango de fechas')
    date_init = fields.Date('Fecha inicial')
    date_end = fields.Date('Fecha final')
    date = fields.Date('Fecha a ingresar')

    def _evalueIndex(self, index, array):
        try:
            array[index]
        except:
            return False
        return True

    def _ceate_marcking_inter(self, vals, date):
        ids = []
        for item in vals[0]['marking_ids']:
            values = {
                'date': date,
                'employee': item
            }
            temp = self.env['hr.employee.markings'].create(values)
            ids.append(temp.id)
        return ids

    @api.model
    def create_marking(self, vals):
        ids = []
        if self._evalueIndex('more_one_day', vals[0]):
            if vals[0]['more_one_day']:
                dateInit = fields.Datetime.from_string(vals[0]['date_init'])
                dateEnd = fields.Datetime.from_string(vals[0]['date_end'])
                dates = [
                    dateInit + datetime.timedelta(n) for n in range(int((dateEnd - dateInit).days) + 1)
                ]
                datesClear = []
                for date in dates:
                    if date.weekday() != 6:
                        datesClear.append(date)
                for date in datesClear:
                    temp_ids = self._ceate_marcking_inter(vals,fields.Datetime.to_string(date))
                    ids = [*ids,*temp_ids]
            else:
                ids = self._ceate_marcking_inter(vals,vals[0]['date'])
        else:
            ids = self._ceate_marcking_inter(vals,vals[0]['date'])
        res = self.env['hr.employee.markings'].csv_download([('id','in',ids)])
        return res
