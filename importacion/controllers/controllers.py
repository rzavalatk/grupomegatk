# -*- coding: utf-8 -*-
from odoo import http

# class Grupomegatk/importacion(http.Controller):
#     @http.route('/grupomegatk/importacion/grupomegatk/importacion/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/grupomegatk/importacion/grupomegatk/importacion/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('grupomegatk/importacion.listing', {
#             'root': '/grupomegatk/importacion/grupomegatk/importacion',
#             'objects': http.request.env['grupomegatk/importacion.grupomegatk/importacion'].search([]),
#         })

#     @http.route('/grupomegatk/importacion/grupomegatk/importacion/objects/<model("grupomegatk/importacion.grupomegatk/importacion"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('grupomegatk/importacion.object', {
#             'object': obj
#         })