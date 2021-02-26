# -*- coding: utf-8 -*-
import json
from odoo.addons.website_sale.controllers import main
from werkzeug.exceptions import NotFound
from odoo import fields, http, tools, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
import math
import time
main.PPG = 24
PPG=main.PPG
PPR = 4

"""
     To optimize search when user clicks on a brand it will filter data and render products template
     @override 
"""


class WebsiteSale(main.WebsiteSale):
    """ @Override
        To add other domains for the search box
    """

    def _get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        # id is added to be sure that order is a unique sort key
        if request.registry.models.get('ks_theme_kinetik.ks_settings', False):
            default_order_by = request.env['ks_theme_kinetik.ks_settings'].search([]).default_order_by
            if default_order_by:
                order = post.get('order') or default_order_by
            else:
                order = post.get('order') or 'website_sequence desc'
        else:
            order = post.get('order') or 'website_sequence desc'
        return 'is_published desc, %s, id desc' % order


    def _get_search_domain(self, search, category, attrib_values, brand=None, ks_max_selected_price= None,ks_min_selected_price=None):
        domain = request.website.sale_product_domain()
        try:
            if search:
                for srch in search.split(" "):
                    domain += [
                        '|', '|', '|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                        ('description_sale', 'ilike', srch), ('ks_product_brand_id.name', 'ilike', srch),
                        ('public_categ_ids.name', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]
            if category:
                domain += [('public_categ_ids', 'child_of', int(category))]

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
                        domain += [('ks_product_brand_id.id', 'in', ids)]
                    else:
                        domain += [('attribute_line_ids.value_ids', 'in', ids)]
                        attrib = value[0]
                        ids = [value[1]]
                if attrib != 0:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                elif attrib == 0:
                    domain += [('ks_product_brand_id.id', 'in', ids)]
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
                        domain += [('ks_product_brand_id.id', 'in', ids)]

                domain += [('ks_product_brand_id.id', 'in', ids)]
            if (ks_min_selected_price or ks_min_selected_price == 0.0) and (ks_max_selected_price or ks_max_selected_price == 0.0):
                domain += [('list_price', '<=', float(ks_max_selected_price)),
                           ('list_price', '>=', float(ks_min_selected_price))]
            return domain
        except Exception:
            pass
    def ks_getShopValues(self, page=0, category=None, search='', ppg=False, **post):
        add_qty = int(post.get('add_qty', 1))
        if category:
            category = request.env['product.public.category'].search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()

        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
        if request.httprequest.args.getlist('attrib'):
            attrib_list = request.httprequest.args.getlist('attrib')
            try:
                if post.get('filter_variant_remove'):
                    attrib_list.remove(post['filter_variant_remove'])
            except:
                pass
        else:
            attrib_list = post.get('attrib')
            try:
                if post.get('filter_variant_remove'):
                    attrib_list.remove(post['filter_variant_remove'])
            except:
                pass
        if attrib_list==None:
            attrib_list=[]
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
        brnd_list = post.get('brnd',request.httprequest.args.getlist('brnd'))
        if request.httprequest.args.getlist('brnd'):
            brnd_list = request.httprequest.args.getlist('brnd')
            try:
                if post.get('filter_brand_remove'):
                    brnd_list.remove(post['filter_brand_remove'])
            except:
                pass
        else:
            brnd_list = post.get('brnd')
            try:
                if post.get('filter_brand_remove'):
                    brnd_list.remove(post['filter_brand_remove'])
            except:
                pass
        if brnd_list==None:
            brnd_list=[]
        if 'filter' in post:
            ks_filer_val = post['filter']
            filter = ks_filer_val.split("_")
            if filter.__len__() == 2 and filter[0] == "brand":
                # search = filter[1]
                brnd_list = ['0-' + str(
                    request.env["ks_product_manager.ks_brand"].search([("name", "=", filter[1])], limit=1).id)]
        brnds_values = [[int(x) for x in v.split("-")] for v in brnd_list if v]
        brnds_set = {v[1] for v in brnds_values}

        product_ids = request.env['product.template'].search(['&', ('sale_ok', '=', True), ('active', '=', True)])

        ks_min_price_avail = ks_max_price_avail = 0
        product_count = len(product_ids)
        if product_ids:
            request.cr.execute('select min(list_price),max(list_price) from product_template where id in %s',
                               (tuple(product_ids.ids),))
            min_max_vals = request.cr.fetchall()
            ks_min_price_avail = min_max_vals[0][0] or 0
            ks_max_price_avail = min_max_vals[0][1] or 1

        pricelist_context, pricelist = self._get_pricelist_context()
        compute_currency = self._get_compute_currency(pricelist, product_ids[:1])

        ks_prod_min_price = ks_min_price_avail = round(compute_currency(float(ks_min_price_avail)), 2)
        ks_prod_max_price = ks_max_price_avail = round(compute_currency(float(ks_max_price_avail)), 2)

        ks_min_selected_price = post.get('min', ks_min_price_avail)
        ks_max_selected_price = post.get('max', ks_max_price_avail)

        company = product_ids[0:1] and product_ids[0:1]._get_current_company(pricelist=pricelist,
                                                           website=request.website) or pricelist.company_id or request.website.company_id
        from_currency = pricelist.currency_id
        to_currency = (product_ids[0:1] or request.env['res.company']._get_main_company()).currency_id
        domain = self._get_search_domain(search, category, attrib_values, brnds_values,
                                         ks_max_selected_price=from_currency._convert(float(ks_max_selected_price), to_currency, company, fields.Date.today()) if ks_max_selected_price else ks_max_selected_price,
                                         ks_min_selected_price=from_currency._convert(float(ks_min_selected_price), to_currency, company, fields.Date.today()) if ks_min_selected_price else ks_min_selected_price)


        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        Product = request.env['product.template'].with_context(bin_size=True)

        Category = request.env['product.public.category']
        search_categories = False
        search_product = Product.search(domain)
        if search:
            categories = search_product.mapped('public_categ_ids')
            search_categories = Category.search(
                [('id', 'parent_of', categories.ids)] + request.website.website_domain())
            categs = search_categories.filtered(lambda c: not c.parent_id)
        else:
            categs = Category.search([('parent_id', '=', False)] + request.website.website_domain())

        parent_category_ids = []
        if category:
            url = "/shop/category/%s" % slug(category)
            parent_category_ids = [category.id]
            current_category = category
            while current_category.parent_id:
                parent_category_ids.append(current_category.parent_id.id)
                current_category = current_category.parent_id
        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list,
                        brnd=brnd_list,
                        min=ks_min_selected_price, ppg=ppg, max=ks_max_selected_price, order=post.get('order'))
        if post.get('filter_remove'):
            category=None
            del(post['filter_remove'])
            keep = QueryURL('/shop', search=search, attrib=attrib_list,
                        brnd=brnd_list,
                        min=ks_min_selected_price,ppg=ppg, max=ks_max_selected_price, order=post.get('order'))
        pager = request.website.pager(url=url, total=len(search_product), page=page, step=ppg, scope=7, url_args=post)

        if post.get('offset', False):
            pager =request.website.pager(url=url, total=len(search_product) - post['offset'], page=page, step=ppg, scope=7,
                                  url_args=post)

            products = Product.search(domain, offset=post['offset'], limit=ppg,
                                      order=self._get_search_order(post))
        else:
            products = Product.search(domain, offset=pager['offset'], limit=ppg, order=self._get_search_order(post))


        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([('attribute_line_ids.value_ids', '!=', False),
                                                  ('attribute_line_ids.product_tmpl_id', 'in', search_product.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        brands = request.env["ks_product_manager.ks_brand"].search([("ks_is_published", "=", True)])
        ks_img_url = ""
        breadcrumb_url=''
        try:
            breadcrumb_url=request.env['ks_theme_kinetik.ks_breadcumb'].search([]).ks_breadcumb_image_url
        except Exception:
            pass

        if category is None:
            category = 0
            cat_name = ''
        else:
            cat_name = category.name
            if category.ks_categ_background:
                ks_img_url = "/web/image/product.public.category/" + str(category.id) + "/ks_categ_background"

        child_cat = Category.search([('parent_id', '!=', False), '|', ('website_id', '=', request.website.id), ('website_id', '=', False)]).ids

        show_price_filter = True
        search_product_ctg_attr = []
        if search or category or attrib_values or brnds_values:
            doamin_new = domain[:]
            doamin_new[-1] = ('list_price', '>=', from_currency._convert(float(ks_prod_min_price), to_currency, company, fields.Date.today()))
            doamin_new[-2] = ('list_price', '<=', from_currency._convert(float(ks_prod_max_price), to_currency, company, fields.Date.today()))

            search_product_ctg_attr = Product.search(doamin_new).ids

            if len(search_product_ctg_attr) == 1:
                show_price_filter = False

            if search_product_ctg_attr:

                request.cr.execute('select min(list_price),max(list_price) from product_template where id in %s',
                                   (tuple(search_product_ctg_attr),))
                min_max_vals = request.cr.fetchall()

                ks_min_price_avail = round(compute_currency(float(min_max_vals[0][0] or 0)), 2)
                ks_max_price_avail = round(compute_currency(float(min_max_vals[0][1] or 1)), 2)

            if post.get('min') and float(post.get('min')) == ks_prod_min_price and post.get('max') and float(post.get('max')) == ks_prod_max_price:
                ks_min_selected_price = ks_min_price_avail
                ks_max_selected_price = ks_max_price_avail
            else:
                if post.get('min') and float(post.get('min')) == ks_min_price_avail:
                    ks_min_selected_price = ks_min_price_avail
                else:
                    ks_min_selected_price = post.get('min', ks_min_price_avail)
                if post.get('max') and float(post.get('max')) == ks_max_price_avail:
                    ks_max_selected_price = ks_max_price_avail
                else:
                    ks_max_selected_price = post.get('max', ks_max_price_avail)

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'ks_img_url': ks_img_url,
            'add_qty': add_qty,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': main.TableCompute().process(products, ppg),
            'rows': PPR,
            'categories': categs,
            'web_category': child_cat,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'parent_category_ids': parent_category_ids,
            'search_categories_ids': search_categories and search_categories.ids,
            'min_price_selected':  ks_min_selected_price if not ks_min_selected_price else float(ks_min_price_avail) if float(ks_min_selected_price) <= float(ks_min_price_avail) and len(search_product_ctg_attr) > 1 else float(ks_min_selected_price),
            'max_price_selected': ks_max_selected_price if not ks_max_selected_price else float(ks_max_price_avail) if float(ks_max_selected_price) >= float(ks_max_price_avail) and len(search_product_ctg_attr) > 1 else float(ks_max_selected_price),
            'min_price_set': float(ks_min_price_avail),
            'max_price_set': float(ks_max_price_avail),
            'brands': brands,
            'brnd_set': brnds_set,
            'ppg': ppg,
            'order': post.get('order'),
            'category_name': cat_name,
            'active_attributes_ids': attributes_ids,
            'page_count':pager['page_count'],
            'breadcumb_shop': breadcrumb_url,
            'show_price_filter': show_price_filter,
            'open_price_filter': True if request.website.viewref('website_sale.products_attributes').active and (float(ks_min_price_avail) != float(ks_min_selected_price) or float(ks_max_price_avail) != float(ks_max_selected_price)) else False,
        }
        if category:
            values['main_object'] = category
        return values

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>''',
        '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        if request.registry.models.get('ks_theme_kinetik.ks_settings', False):
            ks_cron_status = request.env['ks_theme_kinetik.ks_settings'].search([]).cron_update
            if ks_cron_status==True:
                ks_cron_record = request.env.ref('ks_theme_kinetik.ir_cron_update_sale_count')
                try:
                    ks_cron_record.sudo().write({'active': False})
                except:
                    pass
        if post.get('filter_clear'):
            return request.redirect('/shop')
        if post.get('filter_remove'):
            category=None
        if post.get("max", False)=='':
                post['max']=0
        values = self.ks_getShopValues(page, category, search, ppg, **post)
        return request.render("website_sale.products", values)

    @http.route(['/shop/load/more'], type='json', auth="public", website=True)
    def shop_load_more(self, **post):
        ks_page_offset = 24
        ppg = 24
        list_view=False
        ks_search, ks_max, ks_min, ks_category, ks_order = ("" for i in range(5))
        ks_attrib, ks_brands = ([] for i in range(2))
        ks_cate = request.env['product.public.category']
        if post.get("filters", False):
            for filter in post.get("filters"):
                if filter['name'] == 'load_class':
                    ks_load_class = filter['value']
                elif filter['name'] == 'search':
                    ks_search = filter['value']
                elif filter['name'] == 'attrib':
                    ks_attrib.append(filter['value'])
                elif filter['name'] == 'brnd':
                    ks_brands.append(filter['value'])
                elif filter['name'] == 'min':
                    ks_min = filter['value']
                elif filter['name'] == 'max':
                    if filter['value']=='':
                        ks_max='0'
                    ks_max = filter['value']
                elif filter['name'] == 'ppg':
                    ppg = filter['value']
                elif filter['name'] == 'category':
                    ks_category = filter['value']
                    ks_cate = ks_cate.search([('name', '=', ks_category)], limit=1)
                elif filter['name'] == 'offset':
                    ks_page_offset = filter['value']
                elif filter['name'] == 'order':
                    ks_order = filter['value']
                elif filter['name'] == 'search_2':
                    if (len(ks_search)==0):
                        ks_search = filter['value']
                post.update({
                    "attrib": ks_attrib,
                    "brnd": ks_brands,
                    "offset": int(ks_page_offset)
                })
        if ks_order !='':
            post.update({
                'order':ks_order
            })

        values = self.ks_getShopValues(page=1, category=ks_cate, search=ks_search, ppg=ppg, min=ks_min,
                                    max=ks_max, **post)

        values['ks_load_class'] = ks_load_class

        shop_products = request.env['ir.ui.view'].render_template("ks_theme_kinetik.products_infinite_loader", values)
        if request.website.viewref('website_sale.products_list_view').active:
            shop_products = request.env['ir.ui.view'].render_template("ks_theme_kinetik.products_list_view_load_more",
                                                                      values)
            list_view = True
        return ({
            "template": shop_products,
            "no_more": len(values['products']),
            'page_count':values['pager']['page_count'],
            "list_view":list_view
        })

