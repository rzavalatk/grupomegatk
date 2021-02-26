# -*- coding: utf-8 -*-

from . import controllers
from . import models
from odoo import api, SUPERUSER_ID


# TODO: Apply for remove the Website Related view


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    website_get = env['website'].search([])
    if website_get:
        for website in website_get:
            delete_view_id = env['ir.ui.view'].search(['|', ('active', '=', True), ('active', '=', False),
                                             ('website_id', '=', website.id), '|', ('inherit_id', '!=', False), ('inherit_id', '=', False)])
            if delete_view_id:
                delete_view_id.unlink()


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    submenu_view = env["ir.ui.view"].search([('name', '=', 'Submenu')])
    website = env['ir.module.module'].sudo().search([('name', '=', 'website')])
    try:
        if 'has_mega_menu' in submenu_view.arch:
            website.button_immediate_upgrade()
    except:
        pass
