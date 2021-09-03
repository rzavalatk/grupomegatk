# -*- coding: utf-8 -*-
from odoo import http


# class BreadcumCustom(http.Controller):
#     @http.route(['/get_images_breadcum'], type='json', auth='public', website=True)
#     def get_images_breadcum(self):
#         current_website = http.request.env['website'].get_current_website()
#         images = http.request.env['breadcum_custom.images'].sudo().search(
#             [('website_id', '=', current_website.id)], limit=1)
#         res = {}
#         if len(images) > 0:    
#             res["name"] = images[0].name
#             res["image"] = images[0].image
#         return res
