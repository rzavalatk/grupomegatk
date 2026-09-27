from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["odental.service"].search([("product_id", "=", False)])._ensure_billing_product()
