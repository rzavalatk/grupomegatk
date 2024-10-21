##############################################################################
# Copyright (c) 2022 lumitec GmbH (https://www.lumitec.solutions)
# All Right Reserved
#
# See LICENSE file for full licensing details.
##############################################################################
from odoo import fields, models, api
from odoo.tools import split_every


class WebsiteVisitor(models.Model):
    _inherit = 'website.visitor'

    duration = fields.Float('Duration', compute='compute_duration', store=True)
    set_duration = fields.Boolean('Set Duration')

    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Override the search"""
        for arg in args:
            if arg == ['set_duration', '=', True]:
                bot_duration = int(
                    self.env['ir.config_parameter'].sudo().get_param(
                        'website.visitors.live.duration', 0))
                if bot_duration:
                    arg[0] = 'duration'
                    arg[1] = '>'
                    arg[2] = bot_duration
        res = super(WebsiteVisitor, self).search(args, offset=offset,
                                                 limit=limit, order=order,
                                                 count=count)
        return res

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Remove this boolean field from the filter"""
        hide = ['set_duration']
        res = super(WebsiteVisitor, self).fields_get(allfields,
                                                     attributes=attributes)
        for field in res:
            if field in hide:
                res[field]['searchable'] = False
        return res

    def calculate_duration(self):
        visitors = self.env['website.visitor'].search(
            [('set_duration', '=', False)], limit=1500)
        for rec in visitors:
            if rec.last_connection_datetime:
                difference = rec.last_connection_datetime - rec.create_date
                rec.duration = difference.seconds
                rec.set_duration = True

    @api.depends('last_connection_datetime')
    def compute_duration(self):
        """compute duration based on last_connection_datetime and create_date"""
        for rec in self:
            rec.duration = 0.0
            if rec.last_connection_datetime:
                date_create = rec.create_date.replace(microsecond=0)
                date_last_connection = rec.last_connection_datetime.replace(
                    microsecond=0)
                if rec.last_connection_datetime >= rec.create_date:
                    difference = date_last_connection - date_create
                else:
                    difference = date_create - date_last_connection
                rec.duration = difference.seconds
                rec.set_duration = True

    def _cron_remove_bots(self):
        """Archive website visitors if they are bots"""
        bot_duration = int(self.env['ir.config_parameter'].sudo().get_param(
            'website.visitors.live.duration'))
        if bot_duration:
            visitors_to_remove = self.env['website.visitor'].sudo().search(
                [('duration', '<=', bot_duration),
                 ('partner_id', '=', False)], limit=1000)
            visitors_to_remove.unlink()
