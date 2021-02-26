from odoo import http
from odoo.http import request


class WebsiteShopBrands(http.Controller):
    """Fetching all the published brands"""

    @http.route([
        '/product_brands',
    ], type='json', auth="public", website=True)
    def ProductBrandsHomePage(self):
        request.env["ir.qweb"].clear_caches()
        all_brands = request.env['ks_product_manager.ks_brand'].search([("ks_is_published", '=', True),
                                                                        ('website_id', '=', request.website.id)])
        products_brands = []
        for prods in all_brands:
            values = {
                'brand_name': prods.name,
                'brand_img': prods.ks_image,
                'brand_id': prods.id,
                'brand_discount': prods.ks_brand_discount,

            }
            products_brands.append(values)
        return products_brands
