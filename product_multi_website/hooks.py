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

    owner_missing_products = env["product.template"].sudo().search(
        [("owner_company_id", "=", False)]
    )
    for product in owner_missing_products:
        owner_company = (
            product.company_id
            or product.website_id.company_id
            or product.website_ids_multi[:1].company_id
            or product.create_uid.company_id
            or env.company
        )
        product.owner_company_id = owner_company.id
