# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class WarrantyClaimController(http.Controller):
    """ Class for Warranty claim controller"""

    @http.route('/warranty', type='http', auth="public", website=True)
    def warranty_claim(self):
        """ Function to pass the warranty claim details to the warranty
        claim page"""
        customers = request.env['res.partner'].sudo().search([])
        sale_orders = request.env['sale.order'].sudo().search([])
        products = request.env['product.template'].sudo().search([])
        return request.render('product_warranty_management_odoo.warranty_claim_page',
                              {'sale_orders': sale_orders,
                               'customers': customers,
                               'products': products})

    @http.route('/warranty/claim/submit', type='http', auth="public",
                website=True)
    def warranty_claim_submit(self):
        """Function to render the claim thanks view"""
        return request.render('product_warranty_management_odoo.claim_thanks_view')
