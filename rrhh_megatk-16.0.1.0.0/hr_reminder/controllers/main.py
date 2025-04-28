# -*- coding: utf-8 -*-

from odoo import http, fields
from odoo.http import request


class Reminders(http.Controller):

    @http.route('/hr_reminder/all_reminder', type='json', auth="public")
    def all_reminder(self):
        reminder = []
        for i in request.env['hr.reminder'].search([]):
            if i.reminder_active:
                reminder.append({
                    'id': i.id,
                    'name': i.name,
                })
        return reminder


    @http.route('/hr_reminder/reminder_active', type='json', auth="public")
    def reminder_active(self, **kwargs):
        reminder_value = kwargs.get('reminder_name')
        value = []
        i = request.env['hr.reminder'].search([])
        for i in request.env['hr.reminder'].sudo().search([
            ('name', '=', reminder_value)]):
            value.append(i.model_name.model)
            value.append(i.model_field.name)
            value.append(i.search_by)
            value.append(i.date_set)
            value.append(i.date_from)
            value.append(i.date_to)
            value.append(i.id)
            value.append(fields.Date.today())
        return value
