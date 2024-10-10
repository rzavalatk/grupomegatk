##############################################################################
# Copyright (c) 2022 lumitec GmbH (https://www.lumitec.solutions)
# All Right Reserved
#
# See LICENSE file for full licensing details.
##############################################################################
import datetime
SITEMAP_CACHE_TIME = datetime.timedelta(hours=12)
LOC_PER_SITEMAP = 45000
import logging
from datetime import datetime
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.web import Home

_logger = logging.getLogger(__name__)


class WebsiteVisitor(Home):
    @http.route(['/website/update_visitor_last_connection'], type='json',
                auth="public", website=True)
    def update_visitor_last_connection(self):
        """Update last_connection_datetime based on scrolling the website"""
        visitor_sudo = request.env[
            'website.visitor'].sudo()._get_visitor_from_request()
        if visitor_sudo:
            visitor_sudo.sudo().write(
                {'last_connection_datetime': datetime.now()})
            return True
        return False
