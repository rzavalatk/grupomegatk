import itertools,operator
from odoo.addons.web.controllers.main import WebClient, Home
from odoo import http
from odoo.osv import expression
from odoo.http import content_disposition, dispatch_rpc, request
from odoo.addons.http_routing.controllers.main import Routing

class KsRouting(Routing):

    @http.route('/website/translations', type='json', auth="public", website=True)
    def get_website_translations(self, lang, mods=None):
        Modules = request.env['ir.module.module'].sudo()
        IrHttp = request.env['ir.http'].sudo()
        mods = [x['name'] for x in request.env['ir.module.module'].sudo().search_read(
                       [('state', '=', 'installed')], ['name'])]
        domain = IrHttp._get_translation_frontend_modules_domain()
        modules = Modules.search(
            expression.AND([domain, [('state', '=', 'installed')]])
        ).mapped('name')
        if mods:
            modules += mods
        return WebClient().translations(mods=modules, lang=lang)
