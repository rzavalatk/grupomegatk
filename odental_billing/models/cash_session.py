from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ODentalCashSession(models.Model):
    _name = "odental.cash.session"
    _description = "Sesión de caja O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "opened_at desc, id desc"

    name = fields.Char(default="Nueva", readonly=True, copy=False, index=True)
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="restrict", index=True
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía que cobra", required=True, ondelete="restrict", index=True
    )
    site_id = fields.Many2one("odental.site", required=True, ondelete="restrict", index=True)
    cashier_id = fields.Many2one(
        "res.users", string="Cajero", required=True, default=lambda self: self.env.user, index=True
    )
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    opening_amount = fields.Monetary(string="Efectivo inicial", default=0.0, tracking=True)
    collection_ids = fields.One2many(
        "odental.clinical.collection", "cash_session_id", string="Cobros"
    )
    collected_amount = fields.Monetary(compute="_compute_totals", store=True)
    cash_collected_amount = fields.Monetary(compute="_compute_totals", store=True)
    expected_closing_amount = fields.Monetary(compute="_compute_totals", store=True)
    actual_closing_amount = fields.Monetary(string="Efectivo contado", tracking=True)
    difference_amount = fields.Monetary(compute="_compute_totals", store=True)
    opened_at = fields.Datetime(readonly=True, copy=False)
    opened_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    closed_at = fields.Datetime(readonly=True, copy=False)
    closed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    closing_notes = fields.Text()
    state = fields.Selection(
        [("draft", "Borrador"), ("open", "Abierta"), ("closed", "Cerrada")],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )

    @api.depends(
        "opening_amount",
        "actual_closing_amount",
        "collection_ids.amount",
        "collection_ids.affects_cash",
        "collection_ids.state",
    )
    def _compute_totals(self):
        for session in self:
            registered = session.collection_ids.filtered(lambda item: item.state == "registered")
            session.collected_amount = sum(registered.mapped("amount"))
            session.cash_collected_amount = sum(
                registered.filtered("affects_cash").mapped("amount")
            )
            session.expected_closing_amount = (
                session.opening_amount + session.cash_collected_amount
            )
            session.difference_amount = (
                session.actual_closing_amount - session.expected_closing_amount
                if session.state == "closed"
                else 0.0
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nueva") == "Nueva":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.cash.session"
                ) or "Nueva"
        return super().create(vals_list)

    @api.constrains("organization_id", "company_id", "site_id")
    def _check_scope(self):
        for session in self:
            organization = session.organization_id
            allowed_companies = organization.company_id | organization.mapped(
                "professional_ids.billing_company_id"
            )
            if session.company_id not in allowed_companies:
                raise ValidationError("La compañía de cobro no está habilitada para la organización.")
            if not session.site_id.is_available_to(organization):
                raise ValidationError("La sede no está disponible para esta organización.")

    @api.constrains("cashier_id", "organization_id")
    def _check_cashier(self):
        for session in self:
            organization = session.organization_id
            if session.cashier_id not in organization.user_ids and session.cashier_id != organization.owner_user_id:
                raise ValidationError("El cajero debe ser un usuario autorizado de la organización.")

    def write(self, vals):
        if not self.env.context.get("allow_cash_transition"):
            if "state" in vals:
                raise UserError("Utilice las acciones de caja para cambiar su estado.")
            immutable = {"organization_id", "company_id", "site_id", "cashier_id", "opening_amount"}
            if immutable.intersection(vals) and any(session.state != "draft" for session in self):
                raise UserError("No puede cambiar la configuración de una caja iniciada.")
            if "actual_closing_amount" in vals and any(session.state != "open" for session in self):
                raise UserError("El efectivo contado solo se registra al cerrar una caja abierta.")
        return super().write(vals)

    def unlink(self):
        if any(session.state != "draft" or session.collection_ids for session in self):
            raise UserError("Solo puede eliminar una caja en borrador sin cobros.")
        return super().unlink()

    def action_open(self):
        for session in self:
            if session.state != "draft":
                raise UserError("Solo una caja en borrador puede abrirse.")
            existing = self.search_count(
                [
                    ("id", "!=", session.id),
                    ("organization_id", "=", session.organization_id.id),
                    ("site_id", "=", session.site_id.id),
                    ("company_id", "=", session.company_id.id),
                    ("cashier_id", "=", session.cashier_id.id),
                    ("state", "=", "open"),
                ]
            )
            if existing:
                raise ValidationError("El cajero ya tiene una caja abierta en esta sede.")
            session.with_context(allow_cash_transition=True).write(
                {
                    "state": "open",
                    "opened_at": fields.Datetime.now(),
                    "opened_by_id": self.env.user.id,
                }
            )

    def action_close(self):
        for session in self:
            if session.state != "open":
                raise UserError("Solo una caja abierta puede cerrarse.")
            drafts = session.collection_ids.filtered(lambda item: item.state == "draft")
            if drafts:
                raise ValidationError("Resuelva o cancele los cobros pendientes antes de cerrar.")
            session.with_context(allow_cash_transition=True).write(
                {
                    "state": "closed",
                    "closed_at": fields.Datetime.now(),
                    "closed_by_id": self.env.user.id,
                }
            )
