# -*- coding: utf-8 -*-
from odoo import http

# class Grupomegatk/fieldsPrintex(http.Controller):
#     @http.route('/grupomegatk/fields_printex/grupomegatk/fields_printex/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/grupomegatk/fields_printex/grupomegatk/fields_printex/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('grupomegatk/fields_printex.listing', {
#             'root': '/grupomegatk/fields_printex/grupomegatk/fields_printex',
#             'objects': http.request.env['grupomegatk/fields_printex.grupomegatk/fields_printex'].search([]),
#         })

#     @http.route('/grupomegatk/fields_printex/grupomegatk/fields_printex/objects/<model("grupomegatk/fields_printex.grupomegatk/fields_printex"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('grupomegatk/fields_printex.object', {
#             'object': obj
#         })