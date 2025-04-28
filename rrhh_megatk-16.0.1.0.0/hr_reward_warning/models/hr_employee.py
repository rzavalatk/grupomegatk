# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api, _


class HrAnnouncements(models.Model):
    _inherit = 'hr.employee'

    def _announcement_count(self):
        now = datetime.now()
        now_date = now.date()
        for obj in self:
            announcement_ids_general = self.env[
                'hr.announcement'].sudo().search(
                [('is_announcement', '=', True),
                 ('state', 'in', ('approved', 'done')),
                 ('date_start', '<=', now_date)])
            announcement_ids_emp = self.env['hr.announcement'].sudo().search(
                [('employee_ids', 'in', self.id),
                 ('state', 'in', ('approved', 'done')),
                 ('date_start', '<=', now_date)])
            announcement_ids_dep = self.env['hr.announcement'].sudo().search(
                [('department_ids', 'in', self.department_id.id),
                 ('state', 'in', ('approved', 'done')),
                 ('date_start', '<=', now_date)])
            announcement_ids_job = self.env['hr.announcement'].sudo().search(
                [('position_ids', 'in', self.job_id.id),
                 ('state', 'in', ('approved', 'done')),
                 ('date_start', '<=', now_date)])

            announcement_ids = announcement_ids_general.ids + announcement_ids_emp.ids + announcement_ids_dep.ids + announcement_ids_job.ids

            obj.announcement_count = len(set(announcement_ids))

    def announcement_view(self):
        now = datetime.now()
        now_date = now.date()
        for obj in self:

            announcement_ids_general = self.env[
                'hr.announcement'].sudo().search(
                [('is_announcement', '=', True),
                 ('state', 'in', ('approved', 'done')),
                 ('date_start', '<=', now_date)])
            announcement_ids_emp = self.env['hr.announcement'].sudo().search(
                [('employee_ids', 'in', self.id),
                 ('state', 'in', ('approved', 'done')),
                 ('date_start', '<=', now_date)])
            announcement_ids_dep = self.env['hr.announcement'].sudo().search(
                [('department_ids', 'in', self.department_id.id),
                 ('state', 'in', ('approved', 'done')),
                 ('date_start', '<=', now_date)])
            announcement_ids_job = self.env['hr.announcement'].sudo().search(
                [('position_ids', 'in', self.job_id.id),
                 ('state', 'in', ('approved', 'done')),
                 ('date_start', '<=', now_date)])

            ann_obj = announcement_ids_general.ids + announcement_ids_emp.ids + announcement_ids_job.ids + announcement_ids_dep.ids

            ann_ids = []

            for each in ann_obj:
                ann_ids.append(each)
            view_id = self.env.ref(
                'hr_reward_warning.view_hr_announcement_form').id
            if ann_ids:
                if len(ann_ids) > 1:
                    value = {
                        'domain': str([('id', 'in', ann_ids)]),
                        'view_mode': 'tree,form',
                        'res_model': 'hr.announcement',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Comunicados'),
                    }
                else:
                    value = {
                        'view_mode': 'form',
                        'res_model': 'hr.announcement',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Comunicados'),
                        'res_id': ann_ids and ann_ids[0]
                    }
                return value

    announcement_count = fields.Integer(compute='_announcement_count',
                                        string='# Comunicados',
                                        help="Count of Announcement's")
