from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ODentalRentalPackage(models.Model):
    _name = "odental.rental.package"
    _description = "Paquete prepago O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "purchase_date desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    package_type_id = fields.Many2one(
        "odental.rental.package.type", required=True, ondelete="restrict", tracking=True
    )
    provider_organization_id = fields.Many2one(related="package_type_id.organization_id", store=True, index=True)
    renter_organization_id = fields.Many2one(
        "odental.organization", string="Organización arrendataria", required=True,
        ondelete="restrict", index=True, tracking=True
    )
    professional_id = fields.Many2one(
        "odental.professional", string="Profesional beneficiario", required=True,
        ondelete="restrict", index=True, tracking=True
    )
    company_id = fields.Many2one(related="provider_organization_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    purchase_date = fields.Date(required=True, default=fields.Date.context_today)
    expiration_date = fields.Date(readonly=True, copy=False, index=True)
    payment_reference = fields.Char(
        string="Referencia de pago", copy=False,
        help="Comprobante revisado por administración antes de activar el saldo."
    )
    state = fields.Selection(
        [("draft", "Borrador"), ("active", "Activo"), ("exhausted", "Agotado"),
         ("expired", "Vencido"), ("cancelled", "Cancelado")],
        required=True, default="draft", tracking=True, index=True
    )
    credit_move_ids = fields.One2many(
        "odental.rental.credit.move", "package_id", string="Movimientos de saldo", readonly=True
    )
    total_minutes = fields.Integer(compute="_compute_balances", store=True)
    consumed_minutes = fields.Integer(compute="_compute_balances", store=True)
    remaining_minutes = fields.Integer(compute="_compute_balances", store=True)
    sale_order_id = fields.Many2one("sale.order", string="Cotización", readonly=True, copy=False, ondelete="restrict")

    @api.depends("credit_move_ids.minutes")
    def _compute_balances(self):
        for package in self:
            credits = sum(move.minutes for move in package.credit_move_ids if move.minutes > 0)
            debits = -sum(move.minutes for move in package.credit_move_ids if move.minutes < 0)
            package.total_minutes = credits
            package.consumed_minutes = debits
            package.remaining_minutes = max(credits - debits, 0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("odental.rental.package") or "Nuevo"
        return super().create(vals_list)

    @api.constrains("renter_organization_id", "professional_id", "package_type_id")
    def _check_parties(self):
        for package in self:
            if package.renter_organization_id not in package.professional_id.organization_ids:
                raise ValidationError("El profesional no pertenece a la organización arrendataria.")
            if package.renter_organization_id == package.provider_organization_id:
                raise ValidationError("El paquete requiere una organización arrendataria distinta del propietario.")

    def write(self, vals):
        protected = {"package_type_id", "renter_organization_id", "professional_id", "purchase_date"}
        system_fields = {"state", "expiration_date", "sale_order_id"}
        if system_fields.intersection(vals) and not self.env.context.get("odental_package_transition"):
            raise UserError("Utilice las acciones del paquete para cambiar su estado o cotización.")
        for package in self:
            if package.state != "draft" and protected.intersection(vals):
                raise UserError("Un paquete activado no puede cambiar de titular ni condiciones.")
        return super().write(vals)

    def action_activate(self):
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError("Solo un administrador clínico puede activar saldo prepago.")
        for package in self:
            if package.state != "draft":
                raise UserError("Solo un paquete en borrador puede activarse.")
            if not package.payment_reference:
                raise ValidationError("Registre la referencia de pago antes de activar el paquete.")
            package.with_context(odental_package_transition=True).write({
                "state": "active",
                "expiration_date": package.purchase_date + timedelta(days=package.package_type_id.validity_days),
            })
            move_model = self.env["odental.rental.credit.move"].sudo().with_context(odental_credit_system=True)
            move_model.create({
                "package_id": package.id, "move_type": "purchase",
                "minutes": package.package_type_id.purchased_minutes,
                "description": "Horas adquiridas",
            })
            if package.package_type_id.bonus_minutes:
                move_model.create({
                    "package_id": package.id, "move_type": "bonus",
                    "minutes": package.package_type_id.bonus_minutes,
                    "description": "Bonificación del paquete",
                })

    def action_cancel(self):
        for package in self:
            if package.consumed_minutes:
                raise UserError("No se puede cancelar un paquete que ya tiene consumo.")
            package.with_context(odental_package_transition=True).write({"state": "cancelled"})

    def _consume(self, minutes, booking_line):
        self.ensure_one()
        today = fields.Date.context_today(self)
        if self.state != "active" or not self.expiration_date or self.expiration_date < today:
            if self.state == "active":
                self.sudo().with_context(odental_package_transition=True).write({"state": "expired"})
            return 0
        remaining_before = self.remaining_minutes
        consumed = min(max(int(minutes or 0), 0), remaining_before)
        if consumed:
            self.env["odental.rental.credit.move"].sudo().with_context(odental_credit_system=True).create({
                "package_id": self.id, "booking_line_id": booking_line.id,
                "move_type": "usage", "minutes": -consumed,
                "description": f"Consumo {booking_line.booking_id.name}: {booking_line.resource_id.name}",
            })
            if consumed >= remaining_before:
                self.sudo().with_context(odental_package_transition=True).write({"state": "exhausted"})
        return consumed

    def _ensure_partner(self):
        self.ensure_one()
        if self.professional_id.partner_id:
            return self.professional_id.partner_id
        partner = self.env["res.partner"].create({"name": self.professional_id.name, "company_id": False})
        self.professional_id.partner_id = partner
        return partner

    def _get_pricelist(self):
        self.ensure_one()
        pricelist = self.env["product.pricelist"].with_company(self.company_id).search([
            ("currency_id", "=", self.currency_id.id),
            "|", ("company_id", "=", False), ("company_id", "=", self.company_id.id),
        ], limit=1)
        if not pricelist:
            raise ValidationError("Configure una tarifa de venta en la moneda del propietario.")
        return pricelist

    def action_create_quotation(self):
        self.ensure_one()
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError("Solo un administrador clínico puede crear la cotización.")
        if self.sale_order_id:
            return self.action_view_quotation()
        product = self.package_type_id.product_id
        order = self.env["sale.order"].with_company(self.company_id).create({
            "partner_id": self._ensure_partner().id,
            "company_id": self.company_id.id,
            "pricelist_id": self._get_pricelist().id,
            "origin": self.name,
            "odental_rental_package_id": self.id,
            "order_line": [(0, 0, {
                "product_id": product.id, "name": self.package_type_id.name,
                "product_uom_qty": 1, "product_uom": product.uom_id.id,
                "price_unit": self.package_type_id.price,
            })],
        })
        self.with_context(odental_package_transition=True).write({"sale_order_id": order.id})
        return self.action_view_quotation()

    def action_view_quotation(self):
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError("Este paquete todavía no tiene cotización.")
        return {
            "type": "ir.actions.act_window", "res_model": "sale.order",
            "res_id": self.sale_order_id.id, "view_mode": "form", "target": "current",
        }


class ODentalRentalCreditMove(models.Model):
    _name = "odental.rental.credit.move"
    _description = "Movimiento de saldo prepago O Dental"
    _order = "create_date, id"

    package_id = fields.Many2one("odental.rental.package", required=True, ondelete="cascade", index=True)
    booking_line_id = fields.Many2one("odental.rental.booking.line", ondelete="restrict", index=True)
    provider_organization_id = fields.Many2one(related="package_id.provider_organization_id", store=True, index=True)
    renter_organization_id = fields.Many2one(related="package_id.renter_organization_id", store=True, index=True)
    move_type = fields.Selection(
        [("purchase", "Compra"), ("bonus", "Bonificación"), ("usage", "Consumo"), ("adjustment", "Ajuste")],
        required=True, index=True
    )
    minutes = fields.Integer(required=True)
    description = fields.Char(required=True)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("odental_credit_system"):
            raise AccessError("Los movimientos de saldo solo pueden generarse desde el flujo controlado.")
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get("odental_credit_system"):
            raise UserError("Los movimientos de saldo son inmutables.")
        return super().write(vals)

    def unlink(self):
        raise UserError("Los movimientos de saldo son inmutables.")
