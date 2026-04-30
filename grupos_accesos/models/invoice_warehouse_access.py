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


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_user_allowed_warehouses_for_sale(self, user, company=None):
        return self.env["account.move"]._get_user_allowed_warehouses(user, company=company)

    def _check_user_allowed_sale_warehouses(self):
        user = self.env.user
        if not user.has_group("grupos_accesos.group_invoice_by_warehouse"):
            return

        for order in self:
            if not order.warehouse_id:
                continue

            allowed = order._get_user_allowed_warehouses_for_sale(user, company=order.company_id)
            if not allowed:
                raise UserError(_(
                    "No tiene almacenes permitidos para cotizar. "
                    "Asigne almacenes permitidos o configure property_warehouse_id en el usuario."
                ))

            if order.warehouse_id not in allowed:
                raise UserError(_(
                    "No puede cotizar en el almacén %(warehouse)s. "
                    "Almacenes permitidos: %(allowed)s."
                ) % {
                    "warehouse": order.warehouse_id.name,
                    "allowed": ", ".join(allowed.mapped("name")),
                })

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._check_user_allowed_sale_warehouses()
        return orders

    def write(self, vals):
        res = super().write(vals)
        if "warehouse_id" in vals:
            self._check_user_allowed_sale_warehouses()
        return res


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _delivery_edit_restricted(self):
        self.ensure_one()
        return self.picking_type_id.code == "outgoing"

    def _check_delivery_edit_access(self):
        user = self.env.user
        if self.env.context.get("allow_delivery_validation_write"):
            return

        restricted_pickings = self.filtered(
            lambda picking: picking._delivery_edit_restricted()
            and user._company_restriction_active_for_group(
                "grupos_accesos.group_edit_delivery_operations",
                company=picking.company_id or self.env.company,
            )
            and not user.has_group("grupos_accesos.group_edit_delivery_operations")
        )
        if restricted_pickings:
            raise UserError(_(
                "No tiene permisos para editar entregas. Solo puede validarlas."
            ))

    @api.model_create_multi
    def create(self, vals_list):
        return super(StockPicking, self.with_context(allow_delivery_validation_write=True)).create(vals_list)

    def write(self, vals):
        self._check_delivery_edit_access()
        return super().write(vals)

    def action_confirm(self):
        return super(StockPicking, self.with_context(allow_delivery_validation_write=True)).action_confirm()

    def action_assign(self):
        return super(StockPicking, self.with_context(allow_delivery_validation_write=True)).action_assign()

    def button_validate(self):
        return super(StockPicking, self.with_context(allow_delivery_validation_write=True)).button_validate()


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model_create_multi
    def create(self, vals_list):
        return super(StockMove, self.with_context(allow_delivery_validation_write=True)).create(vals_list)

    def _check_delivery_edit_access(self):
        user = self.env.user
        if self.env.context.get("allow_delivery_validation_write"):
            return

        restricted_moves = self.filtered(
            lambda move: move.picking_id
            and move.picking_id.picking_type_id.code == "outgoing"
            and user._company_restriction_active_for_group(
                "grupos_accesos.group_edit_delivery_operations",
                company=move.company_id or self.env.company,
            )
            and not user.has_group("grupos_accesos.group_edit_delivery_operations")
        )
        if restricted_moves:
            raise UserError(_(
                "No tiene permisos para editar entregas. Solo puede validarlas."
            ))

    def write(self, vals):
        self._check_delivery_edit_access()
        return super().write(vals)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        return super(StockMoveLine, self.with_context(allow_delivery_validation_write=True)).create(vals_list)

    def _check_delivery_edit_access(self):
        user = self.env.user
        if self.env.context.get("allow_delivery_validation_write"):
            return

        restricted_lines = self.filtered(
            lambda line: (
                (line.picking_id and line.picking_id.picking_type_id.code == "outgoing")
                or (line.move_id.picking_id and line.move_id.picking_id.picking_type_id.code == "outgoing")
            )
            and user._company_restriction_active_for_group(
                "grupos_accesos.group_edit_delivery_operations",
                company=line.company_id or self.env.company,
            )
            and not user.has_group("grupos_accesos.group_edit_delivery_operations")
        )
        if restricted_lines:
            raise UserError(_(
                "No tiene permisos para editar entregas. Solo puede validarlas."
            ))

    def write(self, vals):
        self._check_delivery_edit_access()
        return super().write(vals)
