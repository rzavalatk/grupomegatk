# # -*- coding: utf-8 -*-
from odoo import models, fields, api
from lxml import etree



class Ks_IrUiView(models.Model):
    _inherit = "ir.ui.view"
    #
    # LAZYLOAD_DEFAULT_SRC = 'data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=='
    #
    # @api.model
    # def render_template(self, template, values=None, engine='ir.qweb'):
    #     res = super(Ks_IrUiView, self).render_template(template, values, engine)
    #     html = etree.HTML(res)
    #     imgs = html.xpath('//main//img[@src][not(hasclass("lazyload-disable"))]') + html.xpath('//footer//img[@src][not(hasclass("lazyload-disable"))]')
    #     for img in imgs:
    #         src = img.attrib['src']
    #         img.attrib['src'] = self.LAZYLOAD_DEFAULT_SRC
    #         img.attrib['data-src'] = src
    #     res = etree.tostring(html, method='html')
    #     return res

    @api.multi
    def toggle(self):
        """ Switches between enabled and disabled statuses
        """

        def deactivate_views(current_view, views):
            for hv in views:
                if current_view.key != hv.key and hv.active:
                    hv.write({'active': False})

        for view in self:
            # Activating current view and deactive other view of footer,heade,fonts etc...
            if 'ks_theme_kinetik.custom_footer_layout' in view.key:

                footer_views = view.search([('key', 'like', 'custom_footer_layout'), ('active', '=', True),
                                            ('website_id', '=', self.env['website'].get_current_website().id)])
                deactivate_views(view, footer_views)

            elif 'ks_theme_kinetik.custom_snippet_width_1' in view.key:
                width_views = view.search([('key', 'like', 'custom_snippet_width'), ('active', '=', True),
                                           ('website_id', '=', self.env['website'].get_current_website().id)])
                deactivate_views(view, width_views)
            elif 'ks_theme_kinetik.custom_header_offer_price' in view.key:
                offer_header_views = view.search([('key', 'like', 'custom_header_offer_price'), ('active', '=', True),
                                                  ('website_id', '=', self.env['website'].get_current_website().id)])
                deactivate_views(view, offer_header_views)
            elif 'ks_theme_kinetik.custom_header_layout' in view.key:
                header_views = view.search(
                    [('key', 'like', 'custom_header_layout'), ('active', '=', True),
                     ('website_id', '=', self.env['website'].get_current_website().id)])
                deactivate_views(view, header_views)
            elif 'ks_theme_kinetik.custom_font_layout' in view.key:
                font_views = view.search(
                    [('key', 'like', 'custom_font_layout'),('active', '=', True),
                     ('website_id', '=', self.env['website'].get_current_website().id)])
                deactivate_views(view, font_views)
            elif 'ks_theme_kinetik.ks_button_style_layout' in view.key:
                button_views = view.search(
                    [('key', 'like', 'ks_button_style_layout'), ('active', '=', True),
                     ('website_id', '=', self.env['website'].get_current_website().id)])
                deactivate_views(view, button_views)

            # rewriting on view and it works
            state = not view.active
            try:
                view.write({'active':state})
            except Exception:
                view.write({'active': not view.active})

    @api.model
    def ks_delete_update_color_file(self):
        website_get = self.env['website'].search([])
        if website_get:
            for website in website_get:
                delete_view = self.env['ir.ui.view'].search(
                    ['|', ('active', '!=', False), ('active', '=', False),
                     ('website_id', '=', website.id),
                     ('name', 'ilike', 'ks_theme_kinetik.ks_updated_')])
                if delete_view:
                    delete_view.unlink()
