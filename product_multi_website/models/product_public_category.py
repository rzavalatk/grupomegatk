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
