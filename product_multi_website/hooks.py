from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    """Copia el website_id historico al nuevo campo website_ids_multi al instalar.

    Esto evita que los productos ya configurados pierdan su restriccion de sitio.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    products = env["product.template"].sudo().search([("website_id", "!=", False)])
    for product in products:
        if product.website_id and product.website_id not in product.website_ids_multi:
            product.website_ids_multi = [(4, product.website_id.id)]
