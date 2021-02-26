from odoo import http, _
from odoo.http import request
import json
from odoo.exceptions import ValidationError


class WebsiteSearchSuggestions(http.Controller):
    """ This search works on the brand/categories/products for now"""

    @http.route([
        '/get/search/suggestions/<string:query>',
    ], type='http', auth="public", website=True)
    def ks_website_search_suggestions(self, query=''):
        if query:
            try:
                website = request.env['website'].get_current_website()
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                ks_currency_id= request.env['website'].get_current_website().currency_id
                ks_result = request.env['product.template'].sudo().search_read([("name", "ilike", query + "%"),('website_published', '=', True)],
                                                                                          fields=['name', 'id','website_price'], limit=20)

                for res in ks_result:
                    ks_product_img="/web/image/product.template/" + str(res['id']) + "/image/60x60"
                    res.update({"url": "/shop/product/%s?search=%s" % (res['id'],res['name'] ),
                                "prod_url":ks_product_img,
                                "prod_price": float("{0:.2f}".format(res['website_price'])),
                                 "currency_symbol":ks_currency_id.symbol,
                                "currency_position": ks_currency_id.position,
                                })


                ks_brands = request.env["ks_product_manager.ks_brand"].sudo().search_read([("name", "ilike", query + "%"),'|', ('website_id','=', website.id), ('website_id','=',False), ("ks_is_published", "=", True)],
                                                                                       fields=['name', 'id'])
                if ks_brands and ks_result.__len__() < 20:
                    for brand in ks_brands:
                        ks_brand_logo="/web/image/ks_product_manager.ks_brand/" + str(brand['id']) + "/ks_brand_logo"
                        brand.update({"url": '/shop?filter=brand_' + brand['name'],
                                      'prod_url':ks_brand_logo
                                      })

                    ks_result.extend(ks_brands)
                ks_categories = request.env["product.public.category"].sudo().search_read([("name", "ilike", query + "%"),'|', ('website_id', '=', website.id), ('website_id', '=', False)],
                                                                                       fields=['name', 'id'])
                if ks_categories and ks_result.__len__() < 20:
                    for category in ks_categories:
                        ks_cat_image = "/web/image/product.public.category/" + str(category['id']) + "/image"
                        url = "/shop/category/" + str((category['name']).replace(" ", "-")) + "-" + str(category['id'])+"?search="+category['name']
                        category.update({"url": url,
                                         'prod_url': ks_cat_image
                                         })
                    ks_result.extend(ks_categories)

                """
                 To sort the result on the basis of the query and word starting with the query will be appeared first
                """

                def sort_on_query(x):
                    if x['name'].lower().startswith(query):
                        return x['name'][:1]
                    else:
                        return x['name'][1:]

                sorted_res = sorted(ks_result, key=sort_on_query)
                return json.dumps({"result": sorted_res},skipkeys=True)
            except Exception as e:
                raise ValidationError(_("Something went wrong: " + str(e)))
