# -*- coding: utf-8 -*-
# from odoo import http


# class PosSlideToDelete(http.Controller):
#     @http.route('/pos_slide_to_delete/pos_slide_to_delete', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_slide_to_delete/pos_slide_to_delete/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_slide_to_delete.listing', {
#             'root': '/pos_slide_to_delete/pos_slide_to_delete',
#             'objects': http.request.env['pos_slide_to_delete.pos_slide_to_delete'].search([]),
#         })

#     @http.route('/pos_slide_to_delete/pos_slide_to_delete/objects/<model("pos_slide_to_delete.pos_slide_to_delete"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_slide_to_delete.object', {
#             'object': obj
#         })
