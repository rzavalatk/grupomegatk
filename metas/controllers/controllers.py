# -*- coding: utf-8 -*-
from odoo import http

# class Grupomegatk/metas(http.Controller):
#     @http.route('/grupomegatk/metas/grupomegatk/metas/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/grupomegatk/metas/grupomegatk/metas/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('grupomegatk/metas.listing', {
#             'root': '/grupomegatk/metas/grupomegatk/metas',
#             'objects': http.request.env['grupomegatk/metas.grupomegatk/metas'].search([]),
#         })

#     @http.route('/grupomegatk/metas/grupomegatk/metas/objects/<model("grupomegatk/metas.grupomegatk/metas"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('grupomegatk/metas.object', {
#             'object': obj
#         })