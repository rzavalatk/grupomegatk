import json

from odoo import http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug, unslug


class WebsiteBlog(http.Controller):
    """Fetching data from 3 blog snippet newly and published"""

    @http.route([
        '/ks_blogs',
    ], type='json', auth="public", website=True)
    def TrendyStyleHomePage(self):
        all_blogs = request.env['blog.post'].sudo().search([("is_published", "=", True)], limit=4,
                                                           order='create_date desc')
        blogs_all = []
        for prods in all_blogs:
            display_date = prods['create_date'].strftime("%d %B")
            for prod_blog in request.env['blog.blog'].sudo().search([]):
                ks_blog_redirect_url = ("/blog/%s" % slug(prod_blog))
                ks_blog_redirect_url_1 = ("/post/%s" % slug(prods))
                ks_link_redirect = ks_blog_redirect_url + ks_blog_redirect_url_1

            ks_blog_url_sanitized = ''
            if prods.cover_properties:
                ks_blog_url = json.loads(prods.cover_properties)['background-image']
                if ks_blog_url != "none":
                    # bad hack to get url
                    ks_blog_url_inner = ks_blog_url.split("(")[1]
                    ks_blog_url_sanitized = ks_blog_url_inner.split(")")[0]

            values = {
                'ks_blog_url': ks_blog_url_sanitized,
                'ks_create_date': display_date,
                'ks_name': prods.name,
                'ks_Subtitle': prods.subtitle,
                'id': prods.id,
                'ks_blog_content': prods.teaser,
                'ks_link_redirect': ks_link_redirect,
            }
            blogs_all.append(values)
        return blogs_all
