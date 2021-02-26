from odoo import http
from odoo.http import request


class Ks_WebsiteMainSlider(http.Controller):
    """Fetching all the images and links from the main slider model"""

    @http.route([
        '/get/main/slider/data',
    ], type='json', auth="public", website=True)
    def Ks_MainSlider(self, **post):
        ks_slides = request.env['ks_product_main.slider'].sudo().search_read([], order='sequence asc')
        rtl= request.env['res.lang'].search([('code', '=', request.env.lang)]).direction == 'rtl'
        return [ks_slides,rtl]
