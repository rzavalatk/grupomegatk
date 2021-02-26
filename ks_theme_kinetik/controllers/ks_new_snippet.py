from odoo import http
from odoo.http import request


class WebsiteNewSnippets(http.Controller):
    """Fetching all the SCSS"""

    @http.route([
        '/new_snippets/styles',
    ], type='json', auth="public", website=True)
    def CustomSnippetStyles(self):
        snippets_css = request.env["theme.ks_new_snippet"].search([]).mapped("ks_snippet_css")
        values = {
            'snippets_css': snippets_css,
        }
        return values
