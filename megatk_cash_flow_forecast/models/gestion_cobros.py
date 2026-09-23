from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CashflowManagementNote(models.Model):
    _name = "cashflow.management.note"
    _description = "Gestión de cobranza"
    _order = "create_date desc, id desc"
    _check_company_auto = True

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True, readonly=True)
    partner_id = fields.Many2one("res.partner", required=True, string="Cliente", index=True)
    promise_id = fields.Many2one(
        "cashflow.promise", string="Cobro proyectado", ondelete="set null", check_company=True,
        domain="[('company_id', '=', company_id), ('direction', '=', 'receivable')]",
    )
    direction = fields.Selection([( "receivable", "Cuenta por cobrar")], default="receivable", required=True, readonly=True)
    note = fields.Text(required=True, string="Gestión realizada")
    next_action_date = fields.Date(string="Próxima gestión")
    follow_up_status = fields.Selection([
        ("none", "Sin próxima gestión"), ("upcoming", "Programada"),
        ("today", "Gestionar hoy"), ("overdue", "Vencida"),
    ], compute="_compute_follow_up_status", string="Seguimiento")
    author_id = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True, string="Registrado por")

    @api.onchange("promise_id")
    def _onchange_promise_id(self):
        if self.promise_id:
            self.partner_id = self.promise_id.partner_id

    @api.constrains("promise_id", "partner_id", "company_id")
    def _check_promise_consistency(self):
        for record in self.filtered("promise_id"):
            if record.promise_id.direction != "receivable":
                raise ValidationError("La gestión solo puede vincularse con un cobro esperado.")
            if (
                record.promise_id.company_id != record.company_id
                or record.promise_id.commercial_partner_id != record.partner_id.commercial_partner_id
            ):
                raise ValidationError(
                    "El cobro proyectado debe corresponder a la misma empresa y al mismo cliente."
                )

    @api.depends("next_action_date")
    def _compute_follow_up_status(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.next_action_date:
                record.follow_up_status = "none"
            elif record.next_action_date < today:
                record.follow_up_status = "overdue"
            elif record.next_action_date == today:
                record.follow_up_status = "today"
            else:
                record.follow_up_status = "upcoming"

    @api.model_create_multi
    def create(self, vals_list):
        normalized = []
        for vals in vals_list:
            values = dict(vals)
            promise_id = values.get("promise_id")
            partner_id = values.get("partner_id")
            promise = (
                self.env["cashflow.promise"].browse(promise_id).exists()
                if promise_id else self.env["cashflow.promise"]
            )
            partner = promise.commercial_partner_id if promise else (
                self.env["res.partner"].browse(partner_id).commercial_partner_id
                if partner_id else self.env["res.partner"]
            )
            if partner:
                values["partner_id"] = partner.id
            normalized.append(values)
        records = super().create(normalized)
        Snapshot = self.env["cashflow.portfolio.snapshot"].sudo().with_context(cashflow_internal_update=True)
        for record in records:
            snapshots = Snapshot.search([
                ("company_id", "=", record.company_id.id),
                ("partner_id", "=", record.partner_id.commercial_partner_id.id),
                ("direction", "=", "receivable"),
            ])
            snapshots.write({
                "last_management": record.note,
                "last_management_at": record.create_date,
                "next_action_date": record.next_action_date,
            })
            if record.promise_id:
                promise = record.promise_id.sudo()
                promise.write({"note": record.note})
                promise.message_post(body=record.note, author_id=self.env.user.partner_id.id)
        return records

    def write(self, vals):
        values = dict(vals)
        if values.get("partner_id"):
            values["partner_id"] = self.env["res.partner"].browse(
                values["partner_id"]
            ).commercial_partner_id.id
        return super().write(values)
