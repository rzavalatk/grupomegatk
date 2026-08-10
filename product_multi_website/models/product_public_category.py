from odoo import models, fields


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    website_ids_multi = fields.Many2many(
        "website",
        "product_public_category_website_multi_rel",
        "category_id",
        "website_id",
        string="Sitios web",
        help="Si se deja vacio, la categoria aparece en todos los sitios.",
    )

    def write(self, vals):
        res = super().write(vals)
        if "website_ids_multi" in vals:
            self._sync_category_website_field()
        return res

    def _sync_category_website_field(self):
        """Sincroniza website_id para que el filtro nativo de Odoo funcione cross-website."""
        for category in self:
            if len(category.website_ids_multi) == 1:
                category.website_id = category.website_ids_multi.id
            else:
                # 0 o varios sitios: global (False) para que aparezca en todos
                category.website_id = False
