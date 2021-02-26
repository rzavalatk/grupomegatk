# -*- coding: utf-8 -*-

from odoo import http,fields
from odoo.http import request
import json
from odoo.http import content_disposition
from odoo.addons.website_sale.controllers.main import WebsiteSale
from datetime import datetime
import base64
import mimetypes
from odoo.addons.http_routing.models.ir_http import slug
import logging
_logger = logging.getLogger(__name__)


class WebsiteSale(WebsiteSale):
    def second_calculation(self, date_start, date_end):
        date_end = datetime(date_end.year, date_end.month, date_end.day,23,59,59)
        date_start = datetime(date_start.year, date_start.month, date_start.day)
        now = datetime.now()
        if (now >= date_start and date_end >= now):
            seconds = int((date_end - now).total_seconds())
        else:
            seconds = 0
        return seconds

    # result = len(listOfStrings) > 0 and all(elem == listOfStrings[0] for elem in listOfStrings)

    @http.route([
        '/ks_deal_of_the_day',
    ], type='json', auth="public", website=True)
    def ks_deal_of_the_day(self):
        value = []
        qty = []
        item_ids = request.env['ks_theme_kinetik.ks_deal_of_the_day'].sudo().search([]).ks_selected_product.item_ids
        for x in range(0, len(item_ids)):
            qty.append(item_ids[x].min_quantity)
        if (len(qty) > 0):
            if not (len(qty) > 0 and all(elem == qty[0] for elem in qty)):
                # index = qty.index(max(qty))
                item_ids = request.env['ks_theme_kinetik.ks_deal_of_the_day'].sudo().search(
                    []).ks_selected_product.item_ids.search([], order='min_quantity DESC')[0]
            else:
                item_ids = request.env['ks_theme_kinetik.ks_deal_of_the_day'].sudo().search(
                    []).ks_selected_product.item_ids.search([], order='create_date DESC')[0]
        date_start = item_ids.date_start
        date_end = item_ids.date_end
        if not (date_end and date_start):
            seconds = 0
        else:
            seconds = self.second_calculation(date_start, date_end)
        value.append(seconds)
        apld_on = item_ids.applied_on
        if apld_on == '0_product_variant':
            prd_vrnt = item_ids.product_id.product_tmpl_id
            url = "/shop/product/%s" % slug(prd_vrnt)
        elif apld_on == '1_product':
            prd = item_ids.product_tmpl_id
            url = "/shop/product/%s" % slug(prd)
        elif apld_on == '2_product_category':
            url = "/shop"
        elif apld_on == '3_global':
            url = "/shop"
        value.append(url)
        return value

    @http.route([
        '/ks_product_images',
    ], type='json', auth="public", website=True)
    def ks_multi_images(self, **kw):
        ks_p_id = int(kw['ks_p_id'])
        value = []
        res_env = request.env['product.template'].sudo().search([('id', '=', ks_p_id)])
        if res_env.ks_is_accessories_slider:
            ks_prod_accessories = {
                "name": "Accessories",
                "ks_navigation": res_env.ks_accessories_navigation,
                "ks_is_slider": res_env.ks_is_accessories_slider,
                "ks_repeat": res_env.ks_accessories_repeat_product,
                "ks_speed": res_env.ks_accessories_slider_speed,
                "ks_auto": res_env.ka_accessories_automitic_slider,
                'rtl': request.env['res.lang'].search([('code', '=', request.env.lang)]).direction == 'rtl'
            }
            value.append(ks_prod_accessories)
        if res_env.ks_is_alternate_slider:
            ks_prod_alternate = {
                "name": "Alternate",
                "ks_navigation": res_env.ks_alternate_navigation,
                "ks_slider": res_env.ks_is_alternate_slider,
                "ks_repeat": res_env.ks_alternate_repeat_product,
                "ks_speed": res_env.ks_alternate_slider_speed,
                "ks_auto": res_env.ka_alternate_automitic_slider,
                'rtl': request.env['res.lang'].search([('code', '=', request.env.lang)]).direction == 'rtl'
            }
            value.append(ks_prod_alternate)

        return value

    @http.route(['/shop/wishlist/remove/<model("product.wishlist"):wish>'], type='json', auth="public", website=True)
    def rm_from_wishlist(self, wish, **kw):

        """Here we have override the wishlist remove controller form product.wishlist model.
        This is used to remove procuct from wishlist for every user and each website"""
        request.env['product.wishlist'].sudo().search([('id', '=', wish.id)]).unlink()
        return True
# *******************************************
    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """This is used to handle event of add to cart button redirect from detail page but only add fron shop page"""
        super(WebsiteSale, self).cart_update(product_id, add_qty, set_qty, **kw)
        if 'product_template_id' in kw and 'my_cart' in kw:
            return request.redirect("/shop")

        else:
            return request.redirect('/shop/cart')

# *********************************************
    @http.route(['/shop/product/cart/update'], type='json', auth="public", website=True)
    def product_cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """This is used to handle event of add to cart button redirect from detail page but only add fron shop page"""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        product_custom_attribute_values = None
        if kw.get('product_custom_attribute_values'):
            product_custom_attribute_values = kw.get('product_custom_attribute_values')
        no_variant_attribute_values = None
        if kw.get('no_variant_attribute_values'):
            no_variant_attribute_values = kw.get('no_variant_attribute_values')

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty if add_qty else 1,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values
        )
        value = {}
        product = request.env['product.product'].sudo().browse(product_id)
        if product.type == 'product' and product.inventory_availability in ['always', 'threshold']:
            available = product.virtual_available - int(product.cart_qty)
            value.update({
                'display': False if available else True,
            })
        value.update({
            'product_id': product_id,
            'qty': request.website.sale_get_order().cart_quantity,
        })
        return value

    @http.route(['/Combination/Variant/Id'], type='json', auth="public", website=True)
    def variant_combination_id(self, product_id, **kw):
        value = {}
        product = request.env['product.product'].sudo().browse(product_id)
        if product.type == 'product' and product.inventory_availability in ['always', 'threshold']:
            available = product.virtual_available - int(product.cart_qty)
            value.update({
                'display': True if available <= 0 else False,
            })
        return value
# ***************************
    @http.route(["/details/cart/update"], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_grid_modal(self,**kw):
        optional_product_len = len(
            request.env['product.template'].sudo().search([('id', '=', int(kw['template_id']))]).optional_product_ids)
        return optional_product_len

# **********************

    @http.route(['/product_configurator/get_combination_info_website'], type='json', auth="public", methods=['POST'],
                website=True)
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, **kw):
        """We have override that controller to remove default template for images in product detail page"""

        seconds = 0
        query = "select categ_id FROM product_template where id = %s"
        request.env.cr.execute(query, (product_template_id,))
        categ_id = request.env.cr.fetchall()
        res = super(WebsiteSale, self).get_combination_info_website(product_template_id, product_id, combination,add_qty, **kw)
        ks_pricelist_item = request.env['product.pricelist.item'].sudo().search(
            ['&', '|', '|',
             ('product_tmpl_id', '=', res.get("product_template_id", False)),
             ('product_id', '=', res.get("product_id", False)),
             ('categ_id', '=', categ_id[0][0]),
             ('min_quantity', '<=', add_qty),
             ('pricelist_id', '=', request.website.get_current_pricelist().id)
             ], limit=1)
        if ks_pricelist_item.date_start and ks_pricelist_item.date_end:
            date_start = ks_pricelist_item.date_start
            date_end = ks_pricelist_item.date_end
            if (date_end and date_start):
                seconds = self.second_calculation(date_start, date_end)

        # Previous/Next functionality
        ks_filters = {}
        ks_domain = []
        ks_url = ""
        try:
            ks_product_url = request.httprequest.headers.environ['HTTP_REFERER']
            if '?' in ks_product_url:
                ks_url = ks_product_url.split('?')[1]
            if '&' in ks_url:
                ks_url_parameters = ks_url.split('&')
                ks_filters = {x.split('=')[0]: x.split('=')[1] for x in ks_url_parameters}
                # ks_filters2 = {}
                # for param in ks_url_parameters:
                #     if param.split('=')[0] in ks_filters2:
                #         ks_filters2[param.split('=')[0]].append(param.split('=')[1])
                #     else:
                #         ks_filters2.update({param.split('=')[0]: [param.split('=')[1]]})

                # Brand filter
                brnds_values = []
                brand_list =[]
                for x in ks_url_parameters:
                    if x.split('=')[0] == "brnd":
                        brand_list.append(x.split('=')[1])
                if brand_list:
                    brnds_values = [[int(x) for x in v.split("-")] for v in brand_list if v]

                # Attribute filter
                attrib_list = []
                attrib_values = []
                for x in ks_url_parameters:
                    if x.split('=')[0] == "attrib":
                        attrib_list.append(x.split('=')[1])
                if attrib_list:
                    attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]

                # Price filter
                product_ids = request.env['product.template'].search(['&', ('sale_ok', '=', True), ('active', '=', True)])
                ks_min_price_avail = ks_max_price_avail = 0
                if product_ids:
                    request.cr.execute('select min(list_price),max(list_price) from product_template where id in %s',
                                       (tuple(product_ids.ids),))
                    min_max_vals = request.cr.fetchall()
                    ks_min_price_avail = min_max_vals[0][0] or 0
                    ks_max_price_avail = min_max_vals[0][1] or 1

                pricelist_context, pricelist = self._get_pricelist_context()
                compute_currency = self._get_compute_currency(pricelist, product_ids[:1])

                ks_min_price_avail = round(compute_currency(float(ks_min_price_avail)), 2)
                ks_max_price_avail = round(compute_currency(float(ks_max_price_avail)), 2)

                ks_min_selected_price = ks_filters.get('min',ks_min_price_avail)
                ks_max_selected_price = ks_filters.get('max', ks_max_price_avail)

                company = product_ids[0:1] and product_ids[0:1]._get_current_company(pricelist=pricelist,
                                                                                     website=request.website) or pricelist.company_id or request.website.company_id
                from_currency = pricelist.currency_id
                to_currency = (product_ids[0:1] or request.env['res.company']._get_main_company()).currency_id

                ks_domain = self.ks_create_product_domain(ks_filters,attrib_values,brnds_values,
                                                          ks_max_selected_price=from_currency._convert(float(ks_max_selected_price), to_currency, company, fields.Date.today()) if ks_max_selected_price else ks_max_selected_price,
                                                          ks_min_selected_price=from_currency._convert(float(ks_min_selected_price), to_currency, company, fields.Date.today()) if ks_min_selected_price else ks_min_selected_price)
        except Exception as e:
            _logger.exception("Ks Exception in previous and next button functionality: " + str(e))

        product_list = request.env['product.template'].search(ks_domain, order=self.ks_get_products_order(ks_filters)).ids

        current_product_index = product_list.index(product_template_id)
        if current_product_index == 0:
            previous_id = None
        else:
            previous_index = current_product_index - 1
            previous_id = product_list[previous_index]
        next_index = current_product_index + 1
        if len(product_list) <= next_index:
            next_id = None
        else:
            next_id = product_list[next_index]
        pro_description = request.env['product.template'].browse(product_template_id).ks_description
        res.update({
            "seconds": seconds,
            'ks_description_post': pro_description if pro_description else False,
            'prev_prod_url': "/shop/product/%s" % (str(previous_id) + '?' + ks_url) if previous_id else None,
            'next_prod_url': "/shop/product/%s" % (str(next_id) + '?' + ks_url) if next_id else None,
            "default_code": request.env['product.product'].browse(res['product_id']).default_code,
        })
        return res
# *********************************************

    def ks_create_product_domain(self,ks_filters, attrib_values, brand=None,ks_max_selected_price=None,ks_min_selected_price=None):
        ks_domain = request.website.sale_product_domain()

        if ks_filters.get('category'):
            ks_domain += [('public_categ_ids', 'child_of', int(ks_filters.get('category')))]

        if brand:
            attrib = None
            ids = []
            for value in brand:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                elif attrib == 0:
                    ks_domain += [('ks_product_brand_id.id', 'in', ids)]
            ks_domain += [('ks_product_brand_id.id', 'in', ids)]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                elif attrib == 0:
                    ks_domain += [('ks_product_brand_id.id', 'in', ids)]
                else:
                    ks_domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib != 0:
                ks_domain += [('attribute_line_ids.value_ids', 'in', ids)]
            elif attrib == 0:
                ks_domain += [('ks_product_brand_id.id', 'in', ids)]

        if (ks_min_selected_price or ks_min_selected_price == 0.0) and (ks_max_selected_price or ks_max_selected_price == 0.0):
            ks_domain += [('list_price', '<=', float(ks_max_selected_price)),
                       ('list_price', '>=', float(ks_min_selected_price))]
        return ks_domain

    def ks_get_products_order(self,post):
        if post.get('order'):
            post['order'] = post.get('order').replace('+',' ')
        if request.registry.models.get('ks_theme_kinetik.ks_settings', False):
            default_order_by = request.env['ks_theme_kinetik.ks_settings'].search([]).default_order_by
            if default_order_by:
                order = post.get('order') or default_order_by
            else:
                order = post.get('order') or 'website_sequence desc'
        else:
            order = post.get('order') or 'website_sequence desc'
        return 'is_published desc, %s, id desc' % order


    @http.route('/product/sizechart/size_chart/<int:product_id>', type='http', auth="public", methods=['POST', 'GET'],
                website=True)
    def preview_size_chart(self, product_id, **kw):
        product = request.env['product.template'].browse(product_id)
        try:
            if product.size_chart:
                filecontent = base64.b64decode(product.size_chart)
                filename = product.size_chart_name
                content_type = mimetypes.guess_type(filename)
                return request.make_response(
                    filecontent,
                    headers=[('Content-Type', content_type[0] or 'application/octet-stream')])
        except Exception:
            pass
        return False

    # To preview the size chart content
    @http.route('/product/sizechart/download/<int:product_id>', type='http', auth="public", methods=['POST', 'GET'],
                website=True)
    def download_size_chart(self, product_id, **kw):
        product = request.env['product.template'].browse(product_id)
        try:
            if product.size_chart:
                filecontent = base64.b64decode(product.size_chart)
                filename = product.size_chart_name
                content_type = mimetypes.guess_type(filename)
                return request.make_response(
                    filecontent,
                    headers=[('Content-Type', content_type[0] or 'application/octet-stream'),
                             ('Content-Disposition', content_disposition(filename)),
                             ])
        except Exception:
            pass
        return False

    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        seconds = 0
        mimetype = 'video/mp4'
        name = 'product_video'
        public = '1'
        request.cr.execute('UPDATE ir_attachment SET mimetype=%s WHERE name=%s', (mimetype, name))
        request.cr.execute('UPDATE ir_attachment SET public=%s WHERE name=%s', (public, name))
        values = super(WebsiteSale, self).product(product, category, search)
        values.qcontext.update({
            "current_url_fb": "http://www.facebook.com/sharer/sharer.php?u=" + request.httprequest.base_url,
            "current_url_twit": "https://twitter.com/intent/tweet?text=" + request.httprequest.base_url,
            "current_url_lin": "http://www.linkedin.com/shareArticle?mini=true-url=" + request.httprequest.base_url,
            "current_url_gplus": "https://plus.google.com/share?url=" + request.httprequest.base_url,
            "seconds": seconds,
            'ks_brand_icon':product.ks_product_brand_id.id,
            'ks_brand_description':product.ks_product_brand_id.ks_brand_description,
        })
        # use for sorting based most viewed product
        view_count = request.env['product.template'].browse(product.id).ks_view_count
        request.cr.execute('UPDATE product_template SET ks_view_count=%s WHERE id=%s', (view_count + 1, product.id))
        query = "select product_template_id FROM product_template_res_users where res_user_id = %s ORDER BY recently_viewed_date DESC"
        request.env.cr.execute(query, (request.env.user.id,))
        ids = request.env.cr.fetchall()
        product_template_ids = [i[0] for i in ids]
        if product.id not in product_template_ids:
            request.env.cr.execute("insert into product_template_res_users"
                                   "  (res_user_id, product_template_id,recently_viewed_date)"
                                   "  values"
                                   "  (%s, %s, %s)",
                                   (request.env.user.id, product.id, fields.Datetime.now()))
        else:
            request.env.cr.execute(
                'UPDATE product_template_res_users SET recently_viewed_date=%s WHERE product_template_id=%s and res_user_id=%s',
                (fields.Datetime.now(), product.id, request.env.user.id))
        return request.render("website_sale.product", values.qcontext)

    @http.route(["/shop/product/slider"], type='json', auth="public", methods=['POST'], website=True, csrf=True)
    def product_image_slider(self, **kw):

        product = request.env['product.template'].browse(int(kw['product_id']))
        values = {'product': product, }
        return request.env['ir.ui.view'].render_template("ks_theme_kinetik.ks_shop_product_old", values)
