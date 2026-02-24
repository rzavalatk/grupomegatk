# -*- coding: utf-8 -*-
from odoo import http

# class /home/rzavala/odoo/grupomegatk12/reportesMega(http.Controller):
#     @http.route('//home/rzavala/odoo/grupomegatk12/reportes_mega//home/rzavala/odoo/grupomegatk12/reportes_mega/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('//home/rzavala/odoo/grupomegatk12/reportes_mega//home/rzavala/odoo/grupomegatk12/reportes_mega/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('/home/rzavala/odoo/grupomegatk12/reportes_mega.listing', {
#             'root': '//home/rzavala/odoo/grupomegatk12/reportes_mega//home/rzavala/odoo/grupomegatk12/reportes_mega',
#             'objects': http.request.env['/home/rzavala/odoo/grupomegatk12/reportes_mega./home/rzavala/odoo/grupomegatk12/reportes_mega'].search([]),
#         })

#     @http.route('//home/rzavala/odoo/grupomegatk12/reportes_mega//home/rzavala/odoo/grupomegatk12/reportes_mega/objects/<model("/home/rzavala/odoo/grupomegatk12/reportes_mega./home/rzavala/odoo/grupomegatk12/reportes_mega"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('/home/rzavala/odoo/grupomegatk12/reportes_mega.object', {
#             'object': obj
#         })