# -*- coding: utf-8 -*-
from odoo import http

# class Grupomegatk/megaActivofijo(http.Controller):
#     @http.route('/grupomegatk/mega_activofijo/grupomegatk/mega_activofijo/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/grupomegatk/mega_activofijo/grupomegatk/mega_activofijo/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('grupomegatk/mega_activofijo.listing', {
#             'root': '/grupomegatk/mega_activofijo/grupomegatk/mega_activofijo',
#             'objects': http.request.env['grupomegatk/mega_activofijo.grupomegatk/mega_activofijo'].search([]),
#         })

#     @http.route('/grupomegatk/mega_activofijo/grupomegatk/mega_activofijo/objects/<model("grupomegatk/mega_activofijo.grupomegatk/mega_activofijo"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('grupomegatk/mega_activofijo.object', {
#             'object': obj
#         })