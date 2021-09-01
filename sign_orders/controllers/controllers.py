# -*- coding: utf-8 -*-
from odoo import http


# class Custom(http.Controller):
#     @http.route(['/set_sign'], type='json', auth='public', website=True)
#     def set_sign(self, values):
#         try:
#             sign = http.request.env['sign_documents.docspdf'].sudo().search(
#                 [('id', '=', values['id'])])
#             sign['sign'] = values['sign']
#             return True
#         except:
#             return False
