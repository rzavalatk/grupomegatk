from odoo import models
from odoo.osv import expression


class Website(models.Model):
    _inherit = "website"

    def sale_product_domain(self):
        self.ensure_one()
        base_domain = super().sale_product_domain()
        # Productos sin asignacion especifica siguen las reglas normales (filtro de compania incluido).
        # Productos asignados explicitamente a este sitio se muestran sin importar la compania.
        return expression.OR([
            expression.AND([base_domain, [("website_ids_multi", "=", False)]]),
            [
                ("is_published", "=", True),
                ("sale_ok", "=", True),
                ("website_ids_multi", "=", self.id),
            ],
        ])
