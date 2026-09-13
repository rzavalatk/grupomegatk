from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ODentalCommissionRule(models.Model):
    _name = "odental.commission.rule"
    _description = "Regla de comisión O Dental"
    _order = "priority desc, id desc"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía pagadora", required=True, ondelete="restrict", index=True
    )
    professional_id = fields.Many2one(
        "odental.professional", string="Profesional específico", ondelete="cascade", index=True
    )
    service_id = fields.Many2one(
        "odental.service", string="Servicio específico", ondelete="cascade", index=True
    )
    percentage = fields.Float(string="Comisión (%)", required=True, default=0.0)
    priority = fields.Integer(default=10)
    notes = fields.Text()

    @api.constrains("percentage")
    def _check_percentage(self):
        for rule in self:
            if not 0 <= rule.percentage <= 100:
                raise ValidationError("La comisión debe estar entre 0 y 100 por ciento.")

    @api.constrains("organization_id", "company_id", "professional_id", "service_id")
    def _check_scope(self):
        for rule in self:
            organization = rule.organization_id
            allowed_companies = organization.company_id | organization.mapped(
                "professional_ids.billing_company_id"
            )
            if rule.company_id not in allowed_companies:
                raise ValidationError("La compañía pagadora no está habilitada para la organización.")
            if rule.professional_id and organization not in rule.professional_id.organization_ids:
                raise ValidationError("El profesional no pertenece a la organización.")
            if rule.service_id and rule.service_id.organization_id != organization:
                raise ValidationError("El servicio no pertenece a la organización.")


class ODentalCommissionSettlement(models.Model):
    _name = "odental.commission.settlement"
    _description = "Liquidación de comisiones O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_to desc, id desc"

    name = fields.Char(default="Nueva", readonly=True, copy=False, index=True)
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="restrict", index=True
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía pagadora", required=True, ondelete="restrict", index=True
    )
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    date_from = fields.Date(required=True, default=fields.Date.context_today)
    date_to = fields.Date(required=True, default=fields.Date.context_today)
    line_ids = fields.One2many(
        "odental.commission.settlement.line", "settlement_id", string="Detalle", copy=False
    )
    base_amount = fields.Monetary(compute="_compute_totals", store=True)
    commission_amount = fields.Monetary(compute="_compute_totals", store=True)
    approved_at = fields.Datetime(readonly=True, copy=False)
    approved_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    payment_reference = fields.Char(copy=False)
    paid_at = fields.Datetime(readonly=True, copy=False)
    paid_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    cancellation_reason = fields.Text(copy=False)
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("calculated", "Calculada"),
            ("approved", "Aprobada"),
            ("paid", "Pagada"),
            ("cancelled", "Cancelada"),
        ],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )

    @api.depends("line_ids.base_amount", "line_ids.commission_amount")
    def _compute_totals(self):
        for settlement in self:
            settlement.base_amount = sum(settlement.line_ids.mapped("base_amount"))
            settlement.commission_amount = sum(
                settlement.line_ids.mapped("commission_amount")
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nueva") == "Nueva":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.commission.settlement"
                ) or "Nueva"
        return super().create(vals_list)

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for settlement in self:
            if settlement.date_to < settlement.date_from:
                raise ValidationError("La fecha final no puede ser anterior a la inicial.")

    @api.constrains("organization_id", "company_id")
    def _check_scope(self):
        for settlement in self:
            organization = settlement.organization_id
            allowed_companies = organization.company_id | organization.mapped(
                "professional_ids.billing_company_id"
            )
            if settlement.company_id not in allowed_companies:
                raise ValidationError("La compañía pagadora no está habilitada para la organización.")

    def _matching_rule(self, professional, service):
        self.ensure_one()
        rules = self.env["odental.commission.rule"].search([
            ("active", "=", True),
            ("organization_id", "=", self.organization_id.id),
            ("company_id", "=", self.company_id.id),
            "|", ("professional_id", "=", False), ("professional_id", "=", professional.id),
            "|", ("service_id", "=", False), ("service_id", "=", service.id),
        ])
        if not rules:
            return rules
        return max(
            rules,
            key=lambda rule: (
                int(bool(rule.professional_id)) + int(bool(rule.service_id)),
                rule.priority,
                rule.id,
            ),
        )

    def action_calculate(self):
        for settlement in self:
            if settlement.state not in {"draft", "calculated"}:
                raise UserError("Solo una liquidación en borrador puede recalcularse.")
            settlement.line_ids.unlink()
            collections = self.env["odental.clinical.collection"].search([
                ("organization_id", "=", settlement.organization_id.id),
                ("company_id", "=", settlement.company_id.id),
                ("state", "=", "registered"),
                ("received_at", ">=", fields.Datetime.to_datetime(settlement.date_from)),
                ("received_at", "<", fields.Datetime.add(fields.Datetime.to_datetime(settlement.date_to), days=1)),
            ])
            commands = []
            for collection in collections:
                plan = collection.invoice_id.odental_treatment_plan_id
                if not plan or not plan.amount_untaxed or not collection.invoice_id.amount_total:
                    continue
                tax_excluded_collection = settlement.currency_id.round(
                    collection.amount * collection.invoice_id.amount_untaxed
                    / collection.invoice_id.amount_total
                )
                active_lines = plan.line_ids.filtered(
                    lambda line: line.state != "cancelled" and line.price_subtotal > 0
                )
                denominator = sum(active_lines.mapped("price_subtotal"))
                if not denominator:
                    continue
                for treatment_line in active_lines:
                    professional = treatment_line.professional_id or plan.responsible_professional_id
                    rule = settlement._matching_rule(professional, treatment_line.service_id)
                    if not rule:
                        continue
                    duplicate = self.env["odental.commission.settlement.line"].search_count([
                        ("collection_id", "=", collection.id),
                        ("treatment_line_id", "=", treatment_line.id),
                        ("settlement_id.state", "in", ("calculated", "approved", "paid")),
                    ])
                    if duplicate:
                        continue
                    base = settlement.currency_id.round(
                        tax_excluded_collection * treatment_line.price_subtotal / denominator
                    )
                    commission = settlement.currency_id.round(base * rule.percentage / 100.0)
                    commands.append((0, 0, {
                        "professional_id": professional.id,
                        "collection_id": collection.id,
                        "treatment_line_id": treatment_line.id,
                        "rule_id": rule.id,
                        "base_amount": base,
                        "percentage": rule.percentage,
                        "commission_amount": commission,
                    }))
            settlement.with_context(allow_settlement_transition=True).write({
                "line_ids": commands,
                "state": "calculated",
            })

    def action_approve(self):
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError("Solo un administrador clínico puede aprobar comisiones.")
        for settlement in self:
            if settlement.state != "calculated":
                raise UserError("Solo una liquidación calculada puede aprobarse.")
            if not settlement.line_ids:
                raise ValidationError("La liquidación no contiene comisiones.")
            settlement.with_context(allow_settlement_transition=True).write({
                "state": "approved",
                "approved_at": fields.Datetime.now(),
                "approved_by_id": self.env.user.id,
            })

    def action_mark_paid(self):
        for settlement in self:
            if settlement.state != "approved":
                raise UserError("Solo una liquidación aprobada puede marcarse pagada.")
            if not settlement.payment_reference:
                raise ValidationError("Registre la referencia del pago realizado.")
            settlement.with_context(allow_settlement_transition=True).write({
                "state": "paid",
                "paid_at": fields.Datetime.now(),
                "paid_by_id": self.env.user.id,
            })

    def action_cancel(self):
        for settlement in self:
            if settlement.state not in {"draft", "calculated"}:
                raise UserError("Una liquidación aprobada o pagada no puede cancelarse.")
            if not settlement.cancellation_reason:
                raise ValidationError("Indique el motivo de cancelación.")
            settlement.line_ids.unlink()
            settlement.with_context(allow_settlement_transition=True).write({"state": "cancelled"})

    def write(self, vals):
        protected = {"organization_id", "company_id", "date_from", "date_to", "line_ids"}
        if not self.env.context.get("allow_settlement_transition"):
            if "state" in vals:
                raise UserError("Utilice las acciones de liquidación para cambiar su estado.")
            if protected.intersection(vals) and any(record.state != "draft" for record in self):
                raise UserError("Una liquidación calculada no puede modificarse manualmente.")
        return super().write(vals)

    def unlink(self):
        if any(record.state != "draft" for record in self):
            raise UserError("Solo se pueden eliminar liquidaciones en borrador.")
        return super().unlink()


class ODentalCommissionSettlementLine(models.Model):
    _name = "odental.commission.settlement.line"
    _description = "Detalle de comisión O Dental"
    _order = "professional_id, id"

    settlement_id = fields.Many2one(
        "odental.commission.settlement", required=True, ondelete="cascade", index=True
    )
    organization_id = fields.Many2one(related="settlement_id.organization_id", store=True, index=True)
    company_id = fields.Many2one(related="settlement_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="settlement_id.currency_id", store=True)
    professional_id = fields.Many2one(
        "odental.professional", required=True, ondelete="restrict", index=True
    )
    collection_id = fields.Many2one(
        "odental.clinical.collection", required=True, ondelete="restrict", index=True
    )
    treatment_line_id = fields.Many2one(
        "odental.treatment.plan.line", required=True, ondelete="restrict", index=True
    )
    service_id = fields.Many2one(related="treatment_line_id.service_id", store=True, index=True)
    rule_id = fields.Many2one(
        "odental.commission.rule", required=True, ondelete="restrict"
    )
    base_amount = fields.Monetary(required=True)
    percentage = fields.Float(required=True)
    commission_amount = fields.Monetary(required=True)

    _sql_constraints = [
        (
            "settlement_collection_treatment_unique",
            "unique(settlement_id, collection_id, treatment_line_id)",
            "El cobro y procedimiento ya están incluidos en esta liquidación.",
        )
    ]
