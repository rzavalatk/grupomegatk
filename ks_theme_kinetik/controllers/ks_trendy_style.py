from odoo import http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug, unslug


class WebsiteTrendyStyle(http.Controller):
    """Fetching alll the categories for the given styles"""

    @http.route([
        '/trendy_style',
    ], type='json', auth="public", website=True)
    def TrendyStyleHomePage(self):
        all_categories = request.env['product.public.category'].sudo().search([])
        products_brands = []
        for prods in all_categories:
            if prods.ks_categ_tag:
                ks_img_url = "/web/image/product.public.category/" + str(prods.id) + "/image"
                categ_url = ("/shop/category/%s" % slug(prods))
                values = {
                    'name': prods.name,
                    'image_medium': ks_img_url,
                    'ks_product_category_slogan': prods.ks_product_category_slogan,
                    'id': prods.id,
                    'ks_url': categ_url,
                }
                products_brands.append(values)
        return products_brands
