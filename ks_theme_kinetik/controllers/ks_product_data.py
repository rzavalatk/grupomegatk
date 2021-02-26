from odoo import http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug, unslug
import json
from odoo.addons.website.controllers.main import QueryURL
import base64
from odoo.tools.mimetypes import guess_mimetype
from datetime import datetime
from odoo.tools.misc import formatLang


class Ks_WebsiteProductGrid(http.Controller):
    """Fetching all the product in the grid and slider"""

    @http.route([
        '/product/data',
    ], type='json', auth="public", website=True)
    def Ks_ProductData(self, **post):
        vals = {}
        ks_products = []
        ks_category_slider = []
        ks_blog_slider = []
        ks_brands_slider = []
        ks_link_redirect = []
        url=http.request.httprequest.host_url
        vals.update({'url':url,})
        if post['snippet_name'] == 'grid':
            ks_slider_id = post.get('id', False)
            ks_grid_rec = request.env['ks_product.grid'].sudo().search([("id", "=", ks_slider_id)], limit=1)
            snippet_name = ks_grid_rec.name
            ks_products = ks_grid_rec['ks_product_template_grid']
            vals.update({
                "grid_name": snippet_name,
                "grid_slider_id": str(ks_grid_rec.id),
                "templates": ks_grid_rec.ks_template_selection,
            })

        elif post['snippet_name'] == 'slider':
            ks_slider_id = post.get('id', False)
            ks_slide_rec = request.env['ks_product.slider'].sudo().search([("id", "=", ks_slider_id)], limit=1)
            snippet_name = ks_slide_rec.name
            if ks_slide_rec.ks_item_selection_method == 'brands':
                items=ks_slide_rec.ks_items_per_slide_for_brands
            elif ks_slide_rec.ks_item_selection_method == 'blogs':
                items = ks_slide_rec.ks_items_per_slide_for_blogs
            else:
                items=ks_slide_rec.ks_items_per_slide
            vals.update({
                "slider_id": "product-owl-id-" + str(ks_slide_rec.id),
                "grid_name": snippet_name,
                "loop": ks_slide_rec.ks_loop,
                "auto_slide": ks_slide_rec.ks_auto_slide,
                "speed": ks_slide_rec.ks_Speed,
                "items": items ,
                "navs": ks_slide_rec.ks_nav_links,
                'template_type': ks_slide_rec.ks_template_type,
                'blog_template_type': ks_slide_rec.ks_blog_template,
                'ks_animation': 'box-animation' if ks_slide_rec.ks_is_animation else '',
                "full_width_class": '' if ks_slide_rec.ks_is_full_width else 'container',
                'rtl': request.env['res.lang'].search([('code', '=', request.env.lang)]).direction == 'rtl'
            })
            if ks_slide_rec.ks_item_selection_method == 'products':
                ks_products = ks_slide_rec.ks_product_template_slider
            elif ks_slide_rec.ks_item_selection_method == 'brands':
                ks_brands_slider = ks_slide_rec.env["ks_product_manager.ks_brand"].search(
                    [("id", "=", ks_slide_rec.ks_product_brand_ids.ids), ("ks_is_published", '=', True)])
            elif ks_slide_rec.ks_item_selection_method == 'Cats':
                ks_category_slider = ks_slide_rec.env["product.public.category"].browse(
                    ks_slide_rec.ks_product_cat_ids.ids)
            elif ks_slide_rec.ks_item_selection_method == 'blogs':
                ks_blog_slider = ks_slide_rec.env["blog.post"].browse(
                    ks_slide_rec.ks_product_blogs_ids.ids)
        ks_prods = []
        ks_cats = []
        ks_blogs = []
        ks_brands = []
        ks_currency_id = request.env['website'].get_current_website().currency_id
        if ks_brands_slider:
            for brand in ks_brands_slider:
                    values = {
                        'brand_name': brand.name,
                        'brand_img': "/web/image/ks_product_manager.ks_brand/" + str(brand['id']) + "/ks_image/330x300",
                        'brand_logo': "/web/image/ks_product_manager.ks_brand/" + str(brand['id']) + "/ks_brand_logo/150x150",
                        'brand_id': brand.id,
                        'brand_discount': brand.ks_brand_discount,
                        'url': "/shop?filter=brand_"+str(brand.name),

                    }
                    ks_brands.append(values)
        if ks_blog_slider:
            for blog in ks_blog_slider:
                display_date = blog['create_date'].strftime("%d %B")

                for prod_blog in request.env['blog.blog'].sudo().search([]):
                    ks_blog_redirect_url = ("/blog/%s" % slug(prod_blog))
                    ks_blog_redirect_url_1 = ("/post/%s" % slug(blog))
                    ks_link_redirect = ks_blog_redirect_url + ks_blog_redirect_url_1

                ks_blog_url_sanitized = ""
                if blog.cover_properties:
                    ks_blog_url = json.loads(blog.cover_properties)['background-image']
                    if ks_blog_url != "none":
                        # ks_blog_url = ks_blog_url.split("(")[1]
                        ks_blog_url_inner = ks_blog_url.split("(")[1]
                        ks_blog_url_sanitized = ks_blog_url_inner.split(")")[0]
                values = {
                    'ks_blog_url': ks_blog_url_sanitized,
                    'ks_create_date': display_date,
                    'ks_name': blog.name,
                    'ks_Subtitle': blog.subtitle,
                    'id': blog.id,
                    'author_image': "/web/image/blog.post/" + str(blog.id) + "/author_avatar",
                    'blog_name': blog.blog_id.name,
                    'author_name': blog.author_id.name,
                    'ks_blog_content': blog.teaser,
                    'ks_link_redirect': ks_link_redirect
                }
                ks_blogs.append(values)
        if ks_category_slider:
            for prods in ks_category_slider:
                ks_img_url = "/web/image/product.public.category/" + str(prods.id) + "/image/330x330"
                categ_url = ("/shop/category/%s" % slug(prods))
                values = {
                    'name': prods.name,
                    'image_medium': ks_img_url,
                    'ks_product_category_slogan': prods.ks_product_category_slogan,
                    'id': prods.id,
                    'ks_url': categ_url,
                }
                ks_cats.append(values)
        ks_product_var_id = 0
        is_ks_wishlist = request.website.viewref('website_sale_wishlist.add_to_wishlist').active
        is_ks_cart = request.website.viewref('website_sale.products_add_to_cart').active
        is_ks_compare = request.website.viewref('website_sale_comparison.add_to_compare').active
        is_ks_product_det = request.website.viewref('website_sale.products_description').active
        rating = request.website.viewref('ks_theme_kinetik.ks_product_comment').active
        percentage_discount_show = request.website.viewref('ks_theme_kinetik.percent_discount').active

        if ks_products:
            for prods in ks_products:
                if prods.is_published:
                    ks_product_var_id = prods['product_variant_id'].id
                ks_img_url = "/web/image/product.template/" + str(prods['id']) + "/image/330x330"
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                if (prods.website_public_price == 0):
                    per_dis = 0
                else:
                    per_dis = int(((prods.website_public_price - prods.website_price) / prods.website_public_price) * 100)

                values = {
                    'product_name': prods['name'],
                    'product_tags': prods.ks_product_tags[0].name if len(prods.ks_product_tags.mapped('id')) else None,
                    'website_currency_id': ks_currency_id.symbol,
                    'website_currency_position': ks_currency_id.position,
                    'website_price': formatLang(request.env, prods.website_price, monetary=True,
                                                     currency_obj=ks_currency_id),
                    'website_public_price': formatLang(request.env, prods.website_public_price, monetary=True,
                                                       currency_obj=ks_currency_id),
                    'percentage_discount': per_dis,
                    'percen_show': percentage_discount_show,
                    'product_img': ks_img_url,
                    'prod_id': prods['id'],
                    'prod_price': prods['list_price'],
                    'prod_url': "/shop/product/%s" % (prods['id'],),
                    'brand_name': prods.ks_product_brand_id.name,
                    'ks_product_var_id': ks_product_var_id,
                    'description_sale': prods.description_sale,
                    'is_ks_wishlist': is_ks_wishlist,
                    'in_wish': prods in request.env['product.wishlist'].current().mapped('product_id.product_tmpl_id'),
                    # prods in prods.env['product.wishlist'].search([]).mapped('product_id.product_tmpl_id')
                    'is_ks_cart': is_ks_cart,
                    'is_ks_compare': is_ks_compare,
                    'is_ks_product_det': is_ks_product_det,
                    'is_rating': rating,
                    'rating_avg': prods.rating_avg,
                    'rating_count': prods.rating_count,

                }
                ks_prods.append(values)
        vals.update({
            "prods": ks_prods,
            "trendy": ks_cats,
            "blogs": ks_blogs,
            "brands": ks_brands,
        })
        return vals
class Ks_WebsiteProductMultiTabs(http.Controller):
    """Fetching all the product in the grid and slider"""

    @http.route([
        '/multitab/product/data',
    ], type='json', auth="public", website=True)
    def Ks_MultitabProductData(self, **post):
        vals={}
        ks_tabs = []
        total_tab=[]
        ks_slider_id = post.get('id', False)
        ks_multi_tab_data = request.env['ks_product.multitab_slider'].sudo().search([("id", "=", ks_slider_id)], limit=1)
        is_ks_wishlist = request.website.viewref('website_sale_wishlist.add_to_wishlist').active
        is_ks_cart = request.website.viewref('website_sale.products_add_to_cart').active
        is_ks_compare = request.website.viewref('website_sale_comparison.add_to_compare').active
        is_ks_product_det = request.website.viewref('website_sale.products_description').active
        ks_currency_id = request.env['website'].get_current_website().currency_id
        keep = QueryURL('/shop')
        ks_tabs=ks_multi_tab_data.tabs_line_ids_line
        rating = request.website.viewref('ks_theme_kinetik.ks_product_comment').active
        percentage_discount_show = request.website.viewref('ks_theme_kinetik.percent_discount').active

        vals = {
            "tabs": ks_multi_tab_data,
            "slider_id":ks_slider_id,
            "ks_Speed": ks_multi_tab_data.ks_Speed,
            "ks_loop": ks_multi_tab_data.ks_loop,
            "ks_auto_slide": ks_multi_tab_data.ks_auto_slide,
            "ks_nav_links": ks_multi_tab_data.ks_nav_links,
            "ks_items_per_slide": ks_multi_tab_data.ks_items_per_slide,
            'website_currency_id': ks_currency_id.symbol,
            'website_currency_position': ks_currency_id.position,
            "is_ks_wishlist": is_ks_wishlist,
            "is_ks_cart": is_ks_cart,
            "is_ks_compare": is_ks_compare,
            "is_ks_product_det": is_ks_product_det,
            'rtl': request.env['res.lang'].search([('code', '=', request.env.lang)]).direction == 'rtl'
        }
        if ks_tabs:
            for ks_products_tab in ks_tabs:
                ks_prods=[]
                tab_name=ks_products_tab.tabs_line_ids.name
                tab_id=ks_products_tab.tabs_line_ids.id
                tab_item_len=len(ks_products_tab.ks_product_template_sliders)
                for prods in ks_products_tab.ks_product_template_sliders:
                    if prods.is_published:
                        ks_product_var_id = prods['product_variant_id'].id
                    ks_img_url = "/web/image/product.template/" + str(prods['id']) + "/image/330x330"
                    base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    if (prods.website_public_price == 0):
                        per_dis = 0
                    else:
                        per_dis = int(((prods.website_public_price - prods.website_price) / prods.website_public_price) * 100)
                    values = {
                        'product_name': prods['name'],
                        'product_tags': prods.ks_product_tags[0].name if len(prods.ks_product_tags.mapped('id')) else None,
                        'website_currency_id': ks_currency_id.symbol,
                        'website_currency_position': ks_currency_id.position,
                        'website_price': formatLang(request.env, prods.website_price, monetary=True,
                                                    currency_obj=ks_currency_id),
                        'website_public_price': formatLang(request.env, prods.website_public_price, monetary=True,
                                                           currency_obj=ks_currency_id),
                        'percentage_discount': per_dis,
                        'percen_show': percentage_discount_show,
                        'product_img': ks_img_url,
                        'prod_id': prods['id'],
                        'prod_price': prods['list_price'],
                        'prod_url': "/shop/product/%s" % (prods['id'],),
                        'brand_name': prods.ks_product_brand_id.name,
                        'ks_product_var_id': ks_product_var_id,
                        'description_sale': prods.description_sale,
                        'is_ks_wishlist': is_ks_wishlist,
                        'in_wish': prods in request.env['product.wishlist'].current().mapped('product_id.product_tmpl_id'),
                        'is_ks_cart': is_ks_cart,
                        'is_ks_compare': is_ks_compare,
                        'is_ks_product_det': is_ks_product_det,
                        'rating_count': prods.rating_count,
                        'is_rating': rating,
                        'rating_avg': prods.rating_avg,

                    }
                    ks_prods.append(values)
                total_tab.append([ks_prods,tab_name,'#tab-'+str(tab_id),'tab-'+str(tab_id)])
        vals.update({
            'tab_names':total_tab
        })
        return vals

class Ks_WebsiteRecentlyViewedProducts(http.Controller):

    @http.route([
        '/recently/viewed/products',
    ], type='json', auth="public", website=True)
    def Ks_RecentlyViewedProductData(self, **post):
        # Fetching all the records belongs to a user
        query = "select product_template_id FROM product_template_res_users where res_user_id = %s ORDER BY recently_viewed_date DESC"
        request.env.cr.execute(query, (request.env.user.id,))
        ids = request.env.cr.fetchall()
        product_template_ids = [i[0] for i in ids]

        ks_products = request.env['product.template'].browse(product_template_ids)
        ks_prods = []
        ks_currency_id = request.env['website'].get_current_website().currency_id
        is_ks_wishlist = request.website.viewref('website_sale_wishlist.add_to_wishlist').active
        is_ks_cart = request.website.viewref('website_sale.products_add_to_cart').active
        is_ks_compare = request.website.viewref('website_sale_comparison.add_to_compare').active
        is_ks_product_det = request.website.viewref('website_sale.products_description').active
        rating = request.website.viewref('ks_theme_kinetik.ks_product_comment').active
        percentage_discount_show = request.website.viewref('ks_theme_kinetik.percent_discount').active
        values = []
        if not request.env.user.id == request.website.user_id.id:
          if ks_products:
            for index, prods in enumerate(ks_products):
                if not index >= 10:
                 if prods.is_published:
                    ks_product_var_id = prods['product_variant_id'].id
                    ks_img_url = "/web/image/product.template/" + str(prods['id']) + "/image/330x330"
                    if (prods.website_public_price == 0):
                        per_dis = 0
                    else:
                        per_dis = int(((prods.website_public_price - prods.website_price) / prods.website_public_price) * 100)

                    values = {
                        'product_name': prods['name'],
                        'website_currency_id': ks_currency_id.symbol,
                        'website_currency_position': ks_currency_id.position,
                        'website_price': formatLang(request.env, prods.website_price, monetary=True,
                                                    currency_obj=ks_currency_id),
                        'website_public_price': formatLang(request.env, prods.website_public_price, monetary=True,
                                                           currency_obj=ks_currency_id),
                        'percentage_discount': per_dis,
                        'percen_show': percentage_discount_show,
                        'product_img': ks_img_url,
                        'prod_id': prods['id'],
                        'prod_price': prods['list_price'],
                        'prod_url': "/shop/product/%s" % (prods['id'],),
                        'brand_name': prods.ks_product_brand_id.name,
                        'ks_product_var_id': ks_product_var_id,
                        'description_sale': prods.description_sale,
                        'is_ks_wishlist': is_ks_wishlist,
                        'in_wish': prods in prods.env['product.wishlist'].current().mapped('product_id.product_tmpl_id'),
                        'is_ks_cart': is_ks_cart,
                        'is_ks_compare': is_ks_compare,
                        'is_ks_product_det': is_ks_product_det,
                        'rating_count': prods.rating_count,
                        'is_rating': rating,
                        'rating_avg': prods.rating_avg,

                    }
                    ks_prods.append(values)

        return{
            'rtl': request.env['res.lang'].search([('code', '=', request.env.lang)]).direction == 'rtl',
            "prods":ks_prods,
            "trendy": [],
            "blogs": [],
            "brands": [],
            "grid_name":"Recently Viewed"
        }

    @http.route([
        '/recently/products/viewed',
    ], type='json', auth="public", website=True)
    def KsRecentlyViewedProduct(self, **post):
        # Fetching all the records belongs to a user
        query = "select product_template_id FROM product_template_res_users where res_user_id = %s ORDER BY recently_viewed_date DESC LIMIT 10"
        request.env.cr.execute(query, (request.env.user.id,))
        ids = request.env.cr.fetchall()
        product_template_ids = [i[0] for i in ids]

        ks_products = request.env['product.template'].browse(product_template_ids)
        ks_currency_id = request.env['website'].get_current_website().currency_id
        percentage_discount_show = request.website.viewref('ks_theme_kinetik.percent_discount').active
        ks_prods = []
        values = []
        if ks_products:
            for prods in ks_products:
                if prods.is_published:
                    ks_img_url = "/web/image/product.template/" + str(prods['id']) + "/image/330x330"
                    if (prods.website_public_price == 0):
                        per_dis = 0
                    else:
                        per_dis = int(
                            ((prods.website_public_price - prods.website_price) / prods.website_public_price) * 100)

                    values = {
                        'product_name': prods['name'],
                        'website_price': formatLang(request.env, prods.website_price, monetary=True, currency_obj=ks_currency_id),
                        'prod_image': ks_img_url,
                        'website_currency_id': ks_currency_id.symbol,
                        'website_currency_position': ks_currency_id.position,
                        'prod_id': prods['id'],
                        'percen_show': percentage_discount_show,
                        'prod_price': formatLang(request.env, prods['list_price'], monetary=True, currency_obj=ks_currency_id),
                        'prod_url': "/shop/product/%s" % (prods['id'],),
                        'percentage_discount': per_dis,
                    }
                    ks_prods.append(values)

        return {
            "prods": ks_prods if ks_prods else None,
            "grid_name": "Recently Viewed"
        }


class Ks_video_snippets(http.Controller):
    @http.route('/product_video/data/create', type='http', auth='public', methods=['POST'], website=True)
    def attachment_add_create(self, name, file, **kwargs):
        attachment_id = request.env['ir.attachment'].create({
            'name': name,
            'datas': base64.b64encode(file.read()),
            'res_model': 'mail.compose.message',
            'res_id': 0,
            'public': 'ir.ui.view',
            'mimetype': 'video/mp4',
        }).id
        return request.make_response(
                data=json.dumps({"id": attachment_id}),
                headers=[('Content-Type', 'application/json')]
            )

    @http.route('/product_video/data/read', type='http', auth='public', methods=['POST'], website=True)
    def attachment_add(self, **kwargs):
        attachment = request.env['ir.attachment'].sudo().browse(int(kwargs.get('id', 0)))
        return request.make_response(
            data=json.dumps(attachment.read(['id', 'name', 'mimetype', 'file_size', 'access_token'])[0]),
            headers=[('Content-Type', 'application/json')]
        )

class ks_deal_seconds(http.Controller):
    @http.route('/deal_of_day/data/second/create', type='http', auth='public', methods=['POST'], website=True)
    def second_create(self, date_start, date_end, **kwargs):
        if(len(date_start) and len(date_end)):
            date_end = datetime.strptime(date_end, '%Y-%m-%d')
            date_start = datetime.strptime(date_start, '%Y-%m-%d')
            date_end = datetime(date_end.year, date_end.month, date_end.day, 23, 59, 59)
            date_start = datetime(date_start.year, date_start.month, date_start.day)
            now = datetime.now()
            if (now >= date_start and date_end >= now):
                seconds = int((date_end - now).total_seconds())
            else:
                seconds = 0
        else:
            seconds = 0
        return request.make_response(
            data=json.dumps({"seconds": seconds}),
            headers=[('Content-Type', 'application/json')]
        )

