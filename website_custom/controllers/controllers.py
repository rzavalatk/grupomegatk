# -*- coding: utf-8 -*-
from odoo import http


class RoutesJSON(http.Controller):
    @http.route(['/get_images_breadcum'], type='json', auth='public', website=True)
    def get_images_breadcum(self):
        current_website = http.request.env['website'].get_current_website()
        images = http.request.env['breadcum_custom.images'].sudo().search(
            [('website_id', '=', current_website.id)], limit=1)
        res = {}
        if len(images) > 0:
            res["name"] = images[0].name
            res["image"] = images[0].image
        return res

    @http.route(['/chat_facebook_active'], type='json', auth='public', website=True)
    def chat_facebook(self):
        setting = http.request.env['res.config.settings'].sudo().getParams()
        return setting['chat_facebook_active']

    @http.route(['/widget_live_chat'], type='json', auth='public', website=True)
    def widget_live_chat(self):
        company = http.request.env.user.company_id.id
        live = http.request.env['im_livechat.channel'].sudo().search(
            [('company_id', '=', company)])
        print("/////////////", live[0].script_external, "/////////////")
        return live[0].script_external

    @http.route(['/get_images_carousel'], type='json', auth='public', website=True)
    def get_images_carousel(self):
        current_website = http.request.env['website'].get_current_website()
        images = http.request.env['carousel.images'].sudo().search(
            ["&", ('website', '=', current_website.id), ('active', '=', True)])
        res = []
        for item in images:
            res.append({
                "name": item.name,
                "description": item.description,
                "font_color_name": item.font_color_name,
                "font_color_description": item.font_color_description,
                "label_button": item.label_button,
                "image": item.image,
                "product_id": item.product.id,
                "stroke_name": item.stroke_name,
                "color_stroke_name": item.color_stroke_name,
                "size_stroke_name": item.size_stroke_name,
                "stroke_description": item.stroke_description,
                "style": item.style,
                "color_stroke_description": item.color_stroke_description
            })

        return res

    @http.route(['/get_quantity'], type='json', auth='public', website=True)
    def get_quantity(self, product):
        res = http.request.env['product.template'].get_quantity(product)
        return res

    @http.route(['/get_video_web'], type='json', auth='public', website=True)
    def get_video_web(self, url):
        current_website = http.request.env['website'].get_current_website()
        videos = http.request.env['video.web'].sudo().search(
            [('website', '=', current_website.id), ('path', '=', url)])
        res = []
        for video in videos:
            res.append({
                'id': video.id,
                'url': video.url,
                'position': video.position,
                'width': video.width,
                'height': video.height,
            })
        return res

    @http.route(['/set_video_web'], type='json', auth='public', website=True)
    def set_video_web(self, index, path):
        try:
            current_website = http.request.env['website'].sudo().get_current_website()
            video = http.request.env['video.web']
            print("//////////",index,path,"///////////")
            vals = {
                'name': 'Nuevo Video',
                'position': index,
                'website': current_website.id,
                'path': path,
            }
            video.sudo().create(vals)
            return True
        except:
            return False