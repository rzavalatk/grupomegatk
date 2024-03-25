from odoo import models, fields, api, _


class Products(models.TransientModel):
    _inherit = 'product.crons'
    
    
    def update_product_ids(self):
        products = self.env['product.product'].search([])
        for product in products:
            product.write({
                'product_tmpl_id': product.id,
            })




