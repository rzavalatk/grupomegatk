from odoo import models, fields, api, _


class Products(models.TransientModel):
    _inherit = 'product.product'
    
    
    def update_product_ids():
        products = self.env['product.product'].search([])
        for product in products:
            product.write({
                'product_tmpl_id': product.id,
            })

    # Ejecutar el script
    update_product_ids()



