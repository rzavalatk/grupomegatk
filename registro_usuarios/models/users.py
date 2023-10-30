# -*- coding: utf-8 -*-

from odoo import models, api


class CustomUsers(models.Model):
    _inherit = 'res.users'

    #@api.model_create_multi 
    def _signup_create_user(self, values):
        current_website = self.env['website'].get_current_website()
        values['company_id'] = current_website.company_id.id
        values['company_ids'] = [(4, current_website.company_id.id)]
        values['website_id'] = current_website.id
        res = super(CustomUsers, self)._signup_create_user(values)
        return res
