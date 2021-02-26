# -*- coding: utf-8 -*-

from odoo import http, models, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.web import Home
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.portal.controllers.mail import PortalChatter
import re

class Website(Home):
    """The purpose of this method inheritance to add website_frontend  view in the customization dropdown"""

    def ks_get_text(self, text):
        return int(text) if text.isdigit() else text

    def ks_natural_keys(self, text):
        return [self.ks_get_text(c) for c in re.split(r'(\d+)', text)]

    @http.route("/website/get_switchable_related_views", type="json", auth="user", website=True)
    def get_switchable_related_views(self, key):

        views = request.env["ir.ui.view"].get_related_views(key, bundles=False).filtered(lambda v: v.customize_show)
        custom_button_views = views.search(
            ["|", "|", "|", "|","|","|","|", ('key', 'like', 'ks_button_style_layout'), ('key', 'like', 'custom_font_layout'),
             ('key', 'like', 'custom_snippet_width'), ('key', 'like', 'ks_sale_tags'),('key', 'like', 'custom_header_offer_price'),
             ('key', 'like', 'static_fltr'),('key', 'like', 'load_more_product'),('key', 'like', 'ks_static_icons'), ('active', 'in', [1, 0])])
        for view in custom_button_views:
            if view.website_id and view.website_id.id == request.website.id:
                views |= view
            elif not view.website_id and not any(
                    view.key == view2.key and view2.website_id and view2.website_id.id == request.website.id for view2
                    in custom_button_views):
                views |= view
        un_sorted_views = views.read(['name', 'id', 'key', 'xml_id', 'arch', 'active', 'inherit_id'])
        # Sorting for header and footer layouts in the theme customization pop up
        sorted_views = sorted(un_sorted_views, key=lambda i: self.ks_natural_keys(i['name']))
        return sorted_views

    @http.route(['/shop/wishlist/remove/<model("product.wishlist"):wish>'], type='json', auth="public", website=True)
    def rm_from_wishlist(self, wish, **kw):

        """Here we have override the wishlist remove controller form product.wishlist model.
        This is used to remove procuct from wishlist for every user and each website"""
        request.env['product.wishlist'].sudo().search([('id', '=', wish.id)]).unlink()
        return True

    # Handle quick preview of the products
    # return view for the modal
    @http.route(['/shop/product/'], type='json', auth="public", website=True)
    def _show_optional_products(self, **kwargs):
        mimetype = 'video/mp4'
        name = 'product_video'
        public = '1'
        request.cr.execute('UPDATE ir_attachment SET mimetype=%s WHERE name=%s', (mimetype, name))
        request.cr.execute('UPDATE ir_attachment SET public=%s WHERE name=%s', (public, name))
        ks_pid = kwargs.get("product_id")
        pricelist = request.website.get_current_pricelist()
        product = request.env['product.template'].browse(ks_pid)
        ProductCategory = request.env['product.public.category']
        categs = ProductCategory.search([('parent_id', '=', False)])
        add_qty = int(kwargs.get('add_qty', 1))
        product_context = dict(request.env.context, quantity=add_qty,
                               active_id=product.id,
                               partner=request.env.user.partner_id)
        if not product_context.get('pricelist'):
            product_context['pricelist'] = pricelist.id
            product = product.with_context(product_context)
        keep = QueryURL('/shop', category=product.categ_id and product.categ_id.id, search=[], attrib=[])
        values = {
            'search': [],
            'category': product.categ_id,
            'pricelist': pricelist,
            'attrib_values': [],
            # compute_currency deprecated, get from product
            'compute_currency': request.website.get_current_pricelist().currency_id,
            'attrib_set': (),
            'keep': keep,
            'image_url': "/web/image/product.template/"+str(product.id)+"/image/330x330",
            'categories': product.categ_id,
            'main_object': product,
            'product': product,
            'add_qty': add_qty,
            'optional_product_ids': [p.with_context({'active_id': p.id}) for p in product.optional_product_ids],
            'per_desc': ((product.website_public_price-product.website_price)/product.website_public_price)*100 if product.website_public_price > 0 else 0,
            # get_attribute_exclusions deprecated, use product method
           # 'get_attribute_exclusions': self._get_attribute_exclusions,
        }
        return [request.env['ir.ui.view'].render_template("ks_theme_kinetik.product",values),len(values['optional_product_ids']), values]

    # Handle variants on add to cart button of the products
    # return view for the modal
    @http.route(['/shop/product_variant/'], type='json', auth="public", website=True)
    def _show_variant(self, **kwargs):

        mimetype = 'video/mp4'
        name = 'product_video'
        public = '1'
        request.cr.execute('UPDATE ir_attachment SET mimetype=%s WHERE name=%s', (mimetype, name))
        request.cr.execute('UPDATE ir_attachment SET public=%s WHERE name=%s', (public, name))

        # request.cr.execute('UPDATE ir_attachment SET mimetype=%s, public=%s WHERE name=%s',
        #                    ('video/mp4', '1', 'product_video'))
        ks_pid = kwargs.get("product_id")
        pricelist = request.website.get_current_pricelist()
        product = request.env['product.template'].browse(ks_pid)
        ProductCategory = request.env['product.public.category']
        categs = ProductCategory.search([('parent_id', '=', False)])

        add_qty = int(kwargs.get('add_qty', 1))
        product_context = dict(request.env.context, quantity=add_qty,
                                active_id=product.id,
                                partner=request.env.user.partner_id)
        if not product_context.get('pricelist'):
             product_context['pricelist'] = pricelist.id
             product = product.with_context(product_context)
        keep = QueryURL('/shop', category=product.categ_id and product.categ_id.id, search=[], attrib=[])
        # prod_price = \
        #     product._get_combination_info(product._get_first_possible_combination(), add_qty=1, pricelist='')[
        #         'price']
        #
        # if not prod_price:
        #     prod_price = product['list_price']
        # if (prod_price == 0):
        #     per_dis = 0
        # else:
        #     per_dis = int(((product.list_price - prod_price) / product.list_price) * 100)

        values = {
            'search': [],
            'category': product.categ_id,
            'pricelist': pricelist,
            'attrib_values': [],
            'compute_currency': request.website.get_current_pricelist().currency_id,
            'attrib_set': (),
            'keep': keep,
            'image_url': "/web/image/product.template/" + str(product.id) + "/image/330x330",
            'categories': product.categ_id,
            'main_object': product,
            'product': product,
            'add_qty': add_qty,
            'optional_product_ids': [p.with_context({'active_id': p.id}) for p in product.optional_product_ids],
            'per_desc': ((product.website_public_price-product.website_price)/product.website_public_price)*100 if product.website_public_price > 0 else 0,
        }
        return [request.env['ir.ui.view'].render_template("ks_theme_kinetik.cart_pop_up",values), values]

class WebsiteRating(PortalChatter):

    @http.route()
    def portal_chatter_init(self, res_model, res_id, domain=False, limit=False, **kwargs):
        result = super(WebsiteRating, self).portal_chatter_init(res_model, res_id, domain=domain, limit=limit, **kwargs)
        # get the rating statistics about the record
        record = request.env[res_model].browse(res_id)
        if hasattr(record, 'rating_avg'):
            record.sudo().ks_rating_avg = record.sudo().rating_avg
        return result


