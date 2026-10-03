from odoo import api, fields, models
from odoo.exceptions import ValidationError
from markupsafe import Markup, escape


class CashflowManagementNote(models.Model):
    _name = "cashflow.management.note"
    _description = "Gestión de cobro o pago"
    _order = "create_date desc, id desc"
    _check_company_auto = True

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True, readonly=True)
    partner_id = fields.Many2one("res.partner", required=True, string="Cliente / proveedor", index=True)
    move_id = fields.Many2one(
        "account.move", string="Documento de Odoo", ondelete="set null", check_company=True,
        domain="[('company_id', '=', company_id), ('partner_id.commercial_partner_id', '=', partner_id), ('move_type', 'in', direction == 'receivable' and ('out_invoice', 'out_refund') or ('in_invoice', 'in_refund')), ('state', '=', 'posted')]",
    )
    promise_id = fields.Many2one(
        "cashflow.promise", string="Cobro o pago proyectado", ondelete="set null", check_company=True,
        domain="[('company_id', '=', company_id), ('direction', '=', direction)]",
    )
    direction = fields.Selection([
        ("receivable", "Cuenta por cobrar"),
        ("payable", "Cuenta por pagar"),
    ], default="receivable", required=True, readonly=True)
    management_type = fields.Selection([
        ("call", "Llamada"),
        ("message", "Mensaje"),
        ("email", "Correo"),
        ("visit", "Visita"),
        ("promise", "Promesa de pago"),
        ("dispute", "Reclamo o disputa"),
        ("other", "Otra gestión"),
    ], default="call", required=True, string="Tipo de gestión")
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
            self.direction = self.promise_id.direction
            self.partner_id = self.promise_id.partner_id
            self.move_id = self.promise_id.source_move_id

    @api.onchange("move_id")
    def _onchange_move_id(self):
        if self.move_id:
            self.direction = (
                "receivable"
                if self.move_id.move_type in ("out_invoice", "out_refund")
                else "payable"
            )
            self.partner_id = self.move_id.commercial_partner_id

    @api.constrains("promise_id", "partner_id", "company_id")
    def _check_promise_consistency(self):
        for record in self.filtered("promise_id"):
            if record.promise_id.direction != record.direction:
                raise ValidationError("La gestión y la proyección deben ser del mismo tipo.")
            if (
                record.promise_id.company_id != record.company_id
                or record.promise_id.commercial_partner_id != record.partner_id.commercial_partner_id
            ):
                raise ValidationError(
                    "El cobro proyectado debe corresponder a la misma empresa y al mismo cliente."
                )

    @api.constrains("move_id", "partner_id", "company_id")
    def _check_move_consistency(self):
        for record in self.filtered("move_id"):
            expected_types = (
                ("out_invoice", "out_refund")
                if record.direction == "receivable"
                else ("in_invoice", "in_refund")
            )
            if record.move_id.move_type not in expected_types:
                raise ValidationError("El documento no corresponde al tipo de gestión seleccionado.")
            if (
                record.move_id.company_id != record.company_id
                or record.move_id.commercial_partner_id != record.partner_id.commercial_partner_id
            ):
                raise ValidationError(
                    "La factura debe corresponder a la misma empresa y al mismo cliente."
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
            move_id = values.get("move_id")
            promise = (
                self.env["cashflow.promise"].browse(promise_id).exists()
                if promise_id else self.env["cashflow.promise"]
            )
            move = self.env["account.move"].browse(move_id).exists() if move_id else self.env["account.move"]
            if promise:
                values["direction"] = promise.direction
            elif move:
                values["direction"] = (
                    "receivable"
                    if move.move_type in ("out_invoice", "out_refund")
                    else "payable"
                )
            partner = (
                move.commercial_partner_id if move else
                promise.commercial_partner_id if promise else
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
                ("direction", "=", record.direction),
            ])
            snapshots.write({
                "last_management": record.note,
                "last_management_at": record.create_date,
                "next_action_date": record.next_action_date,
            })
            label = dict(record._fields["management_type"].selection).get(
                record.management_type, "Gestión"
            )
            next_action = (
                Markup("<br/><b>Próxima gestión:</b> %s") % escape(record.next_action_date)
                if record.next_action_date else Markup("")
            )
            operation = "cobro" if record.direction == "receivable" else "pago"
            body = Markup("<b>Gestión de %s · %s</b><br/>%s%s") % (
                escape(operation), escape(label), escape(record.note), next_action
            )
            record.partner_id.sudo().message_post(
                body=body, author_id=self.env.user.partner_id.id
            )
            if record.move_id:
                record.move_id.sudo().message_post(
                    body=body, author_id=self.env.user.partner_id.id
                )
            if record.promise_id:
                promise = record.promise_id.sudo()
                promise.write({"note": record.note})
                promise.message_post(body=body, author_id=self.env.user.partner_id.id)
        return records

    def write(self, vals):
        values = dict(vals)
        if values.get("partner_id"):
            values["partner_id"] = self.env["res.partner"].browse(
                values["partner_id"]
            ).commercial_partner_id.id
        return super().write(values)
