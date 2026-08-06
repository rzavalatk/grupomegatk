from odoo import models
from odoo.osv import expression


class Website(models.Model):
    _inherit = "website"

    def sale_product_domain(self):
        """Extiende el dominio base de tienda para soportar multip sitio por producto.

        El producto se muestra si:
        - no tiene sitios definidos (global), o
        - el sitio actual esta en website_ids_multi.
        """
        domain = super().sale_product_domain()
        self.ensure_one()
        multi_website_domain = [
            "|",
            ("website_ids_multi", "=", False),
            ("website_ids_multi", "in", self.id),
        ]
        return expression.AND([domain, multi_website_domain])
