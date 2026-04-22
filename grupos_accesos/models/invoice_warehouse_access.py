from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = "res.users"

    allowed_invoice_warehouse_ids = fields.Many2many(
        "stock.warehouse",
        "res_users_allowed_invoice_warehouse_rel",
        "user_id",
        "warehouse_id",
        string="Almacenes permitidos para facturar",
        help="Define en que almacenes puede facturar el usuario cuando tiene el grupo de restriccion.",
    )


class AccountMove(models.Model):
    _inherit = "account.move"

    def _collect_user_default_warehouses(self, user, company=None):
        company_user = user.with_company(company) if company else user
        warehouses = self.env["stock.warehouse"]

        # Campo confirmado por negocio: res.users.property_warehouse_id
        if "property_warehouse_id" in company_user._fields and company_user.property_warehouse_id:
            warehouses |= company_user.property_warehouse_id

        user_field_candidates = [
            "warehouse_id",
            "default_warehouse_id",
            "warehouse_ids",
        ]
        for field_name in user_field_candidates:
            if field_name not in company_user._fields:
                continue
            value = company_user[field_name]
            if not value:
                continue
            if getattr(value, "_name", "") == "stock.warehouse":
                warehouses |= value

        partner = company_user.partner_id
        if partner:
            partner_field_candidates = [
                "warehouse_id",
                "default_warehouse_id",
                "property_warehouse_id",
                "warehouse_ids",
            ]
            for field_name in partner_field_candidates:
                if field_name not in partner._fields:
                    continue
                value = partner[field_name]
                if not value:
                    continue
                if getattr(value, "_name", "") == "stock.warehouse":
                    warehouses |= value

        return warehouses

    def _get_user_allowed_warehouses(self, user, company=None):
        allowed = user.allowed_invoice_warehouse_ids
        if allowed:
            return allowed

        default_warehouses = self._collect_user_default_warehouses(user, company=company)
        if default_warehouses:
            return default_warehouses

        return self.env["stock.warehouse"]

    def _get_related_invoice_warehouses(self):
        self.ensure_one()
        warehouses = self.env["stock.warehouse"]

        sale_lines = self.invoice_line_ids.mapped("sale_line_ids")
        if sale_lines:
            warehouses |= sale_lines.mapped("order_id.warehouse_id")

        if not warehouses and self.invoice_origin:
            origin_names = [name.strip() for name in self.invoice_origin.split(",") if name.strip()]
            if origin_names:
                sale_orders = self.env["sale.order"].search([
                    ("name", "in", origin_names),
                    ("company_id", "=", self.company_id.id),
                ])
                warehouses |= sale_orders.mapped("warehouse_id")

        return warehouses

    def _check_user_allowed_invoice_warehouses(self):
        user = self.env.user
        if not user.has_group("grupos_accesos.group_invoice_by_warehouse"):
            return

        for move in self:
            if move.move_type not in ("out_invoice", "out_refund", "out_receipt"):
                continue

            allowed = self._get_user_allowed_warehouses(user, company=move.company_id)
            if not allowed:
                raise UserError(_(
                    "No tiene almacenes permitidos para facturar. "
                    "Asigne almacenes permitidos o configure property_warehouse_id en el usuario."
                ))

            related_warehouses = move._get_related_invoice_warehouses()
            if not related_warehouses:
                continue

            forbidden = related_warehouses - allowed
            if forbidden:
                raise UserError(_(
                    "No puede facturar en estos almacenes: %(warehouses)s. "
                    "Almacenes permitidos: %(allowed)s."
                ) % {
                    "warehouses": ", ".join(forbidden.mapped("name")),
                    "allowed": ", ".join(allowed.mapped("name")),
                })

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_user_allowed_invoice_warehouses()
        return records

    def action_post(self):
        self._check_user_allowed_invoice_warehouses()
        return super().action_post()
