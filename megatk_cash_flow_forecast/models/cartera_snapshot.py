from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import UserError


class CashflowPortfolioSnapshot(models.Model):
    """Operational report cache rebuilt from Odoo's currently open move lines."""

    _name = "cashflow.portfolio.snapshot"
    _description = "Detalle de cartera para flujo proyectado"
    _order = "direction, partner_id"

    company_id = fields.Many2one("res.company", required=True, index=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    direction = fields.Selection([( "receivable", "Cuenta por cobrar"), ("payable", "Cuenta por pagar")], required=True, index=True)
    direction_name = fields.Char(compute="_compute_labels")
    classification = fields.Selection([
        ("customer", "Clientes"), ("employee_receivable", "CxC empleados"),
        ("group_receivable", "Grupo Mega"), ("supplier", "Proveedores"),
        ("creditor", "Acreedores"), ("advance", "Anticipos"),
        ("legal", "En legal"), ("to_reconcile", "Por depurar"),
        ("unassigned", "Por asignar"),
    ], required=True, default="unassigned", index=True)
    classification_name = fields.Char(compute="_compute_labels")
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    at_day = fields.Monetary(string="Al día")
    days_1_30 = fields.Monetary(string="1–30 días")
    days_31_60 = fields.Monetary(string="31–60 días")
    days_61_90 = fields.Monetary(string="61–90 días")
    days_91_120 = fields.Monetary(string="91–120 días")
    old = fields.Monetary(string="Antiguos")
    credit = fields.Monetary(string="Crédito / anticipo")
    total = fields.Monetary(compute="_compute_total", store=True)
    projected_periods = fields.Char(string="Semanas proyectadas", readonly=True)
    last_management = fields.Text(string="Última gestión", readonly=True)
    last_management_at = fields.Datetime(string="Fecha última gestión", readonly=True)
    next_action_date = fields.Date(string="Próxima gestión", readonly=True)
    open_document_count = fields.Integer(string="Documentos abiertos", readonly=True)
    refreshed_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)

    _sql_constraints = [
        (
            "company_partner_direction_uniq",
            "unique(company_id, partner_id, direction)",
            "Solo puede existir una línea de cartera por empresa, contacto y tipo.",
        )
    ]

    @api.depends("at_day", "days_1_30", "days_31_60", "days_61_90", "days_91_120", "old", "credit")
    def _compute_total(self):
        for record in self:
            record.total = record.at_day + record.days_1_30 + record.days_31_60 + record.days_61_90 + record.days_91_120 + record.old - record.credit

    @api.depends("direction", "classification")
    def _compute_labels(self):
        directions = dict(self._fields["direction"].selection)
        classifications = dict(self._fields["classification"].selection)
        for record in self:
            record.direction_name = directions.get(record.direction, "")
            record.classification_name = classifications.get(record.classification, "")

    @api.model
    def _prepare_company_values(self, company):
        """Read Odoo's open items and prepare the operational customer/vendor summary."""
        today = fields.Date.context_today(self)
        lines = self.env["account.move.line"].search([
            ("company_id", "=", company.id),
            ("parent_state", "=", "posted"),
            ("account_id.account_type", "in", ("asset_receivable", "liability_payable")),
            ("amount_residual", "!=", 0),
        ])
        classifications = {
            (item.partner_id.id, item.direction): item.classification
            for item in self.env["cashflow.portfolio.classification"].search([("company_id", "=", company.id)])
        }
        scheduled = defaultdict(set)
        promises = self.env["cashflow.promise"].search([
            ("company_id", "=", company.id), ("state", "=", "active"),
        ])
        period_labels = {
            "week_1": "1",
            "week_2": "2",
            "week_3": "3",
            "pending": "Pend.",
        }
        for promise in promises:
            partner = promise.partner_id.commercial_partner_id
            if partner:
                scheduled[(partner.id, promise.direction)].add(promise.period)
        latest_notes = {}
        notes = self.env["cashflow.management.note"].search([
            ("company_id", "=", company.id), ("direction", "=", "receivable"),
        ], order="create_date desc, id desc")
        for note in notes:
            latest_notes.setdefault(note.partner_id.commercial_partner_id.id, note)
        values = defaultdict(lambda: defaultdict(float))
        documents = defaultdict(set)
        for line in lines:
            direction = "receivable" if line.account_id.account_type == "asset_receivable" else "payable"
            partner = line.partner_id.commercial_partner_id
            if not partner:
                continue
            # A credit in CxC or an advance/payment in CxP is the opposite sign of its debt.
            is_credit = (direction == "receivable" and line.amount_residual < 0) or (direction == "payable" and line.amount_residual > 0)
            key = (partner.id, direction)
            documents[key].add(line.move_id.id)
            if is_credit:
                values[key]["credit"] += abs(line.amount_residual)
                continue
            overdue = max((today - (line.date_maturity or line.date)).days, 0)
            field_name = "at_day" if overdue == 0 else (
                "days_1_30" if overdue <= 30 else "days_31_60" if overdue <= 60 else
                "days_61_90" if overdue <= 90 else "days_91_120" if overdue <= 120 else "old"
            )
            values[key][field_name] += abs(line.amount_residual)
        created = []
        for (partner_id, direction), buckets in values.items():
            created.append({
                "company_id": company.id,
                "partner_id": partner_id,
                "direction": direction,
                "classification": classifications.get((partner_id, direction), "unassigned"),
                "projected_periods": ", ".join(
                    period_labels[period]
                    for period, _label in (
                        ("week_1", "Semana 1"),
                        ("week_2", "Semana 2"),
                        ("week_3", "Semana 3"),
                        ("pending", "Pendiente"),
                    )
                    if period in scheduled[(partner_id, direction)]
                ),
                "last_management": latest_notes[partner_id].note if direction == "receivable" and partner_id in latest_notes else False,
                "last_management_at": latest_notes[partner_id].create_date if direction == "receivable" and partner_id in latest_notes else False,
                "next_action_date": latest_notes[partner_id].next_action_date if direction == "receivable" and partner_id in latest_notes else False,
                "open_document_count": len(documents[(partner_id, direction)]),
                **buckets,
            })
        return created

    @api.model
    def refresh_company(self, company):
        """Rebuild the company summary without writing any accounting data."""
        self.env.cr.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s), %s)",
            ["megatk_cashflow_portfolio", company.id],
        )
        self.search([("company_id", "=", company.id)]).unlink()
        return self.create(self._prepare_company_values(company))

    @api.model
    def refresh_partner(self, company, partner):
        """Refresh one contact for meeting and collection follow-up screens."""
        commercial = partner.commercial_partner_id
        self.env.cr.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s), %s)",
            ["megatk_cashflow_partner", company.id * 1000000 + commercial.id],
        )
        self.search([
            ("company_id", "=", company.id),
            ("partner_id", "=", commercial.id),
        ]).unlink()
        values = [
            item for item in self._prepare_company_values(company)
            if item["partner_id"] == commercial.id
        ]
        return self.create(values)

    def write(self, vals):
        """Persist the operational classification behind the refreshed report.

        Snapshots are rebuilt from Odoo open items, so writing the transient row
        alone would lose the change on the next refresh.  The classification is
        saved per company, contact and direction instead.
        """
        protected_fields = set(vals) - {"classification"}
        if protected_fields and not self.env.context.get("cashflow_internal_update"):
            raise UserError(
                "El detalle viene de Odoo y no se modifica manualmente; solo puede cambiar su clasificación operativa."
            )
        if "classification" in vals:
            Classification = self.env["cashflow.portfolio.classification"]
            for snapshot in self:
                classification = Classification.search([
                    ("company_id", "=", snapshot.company_id.id),
                    ("partner_id", "=", snapshot.partner_id.id),
                    ("direction", "=", snapshot.direction),
                ], limit=1)
                if classification:
                    classification.write({"classification": vals["classification"]})
                else:
                    Classification.create({
                        "company_id": snapshot.company_id.id,
                        "partner_id": snapshot.partner_id.id,
                        "direction": snapshot.direction,
                        "classification": vals["classification"],
                    })
        return super().write(vals)

    def action_add_management_note(self):
        self.ensure_one()
        if self.direction != "receivable":
            raise UserError("Las gestiones de cobranza solo corresponden a cuentas por cobrar.")
        return {
            "type": "ir.actions.act_window",
            "name": "Registrar gestión de cobranza",
            "res_model": "cashflow.management.note",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_company_id": self.company_id.id,
                "default_partner_id": self.partner_id.id,
                "default_direction": "receivable",
            },
        }

    def action_schedule_promise(self):
        self.ensure_one()
        classification = self.env["cashflow.portfolio.classification"].search([
            ("company_id", "=", self.company_id.id),
            ("partner_id", "=", self.partner_id.id),
            ("direction", "=", self.direction),
        ], limit=1)
        plan = self.env["cashflow.plan"].with_company(self.company_id).get_or_create_current_plan()
        return {
            "type": "ir.actions.act_window",
            "name": "Programar cobro" if self.direction == "receivable" else "Programar pago",
            "res_model": "cashflow.promise",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_plan_id": plan.id,
                "default_company_id": self.company_id.id,
                "default_partner_id": self.partner_id.id,
                "default_direction": self.direction,
                "default_classification_id": classification.id or False,
                "default_period": "week_1",
                "default_amount": max(self.total, 0.0),
            },
        }

    @api.model
    def action_new_manual_expense(self):
        plan = self.env["cashflow.plan"].get_or_create_current_plan()
        return {
            "type": "ir.actions.act_window",
            "name": "Nuevo egreso manual o recurrente",
            "res_model": "cashflow.manual.expense",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_plan_id": plan.id,
                "default_period": "week_1",
                "default_currency_id": plan.currency_id.id,
            },
        }

    def action_open_documents(self):
        self.ensure_one()
        move_types = (
            ("out_invoice", "out_refund")
            if self.direction == "receivable"
            else ("in_invoice", "in_refund")
        )
        return {
            "type": "ir.actions.act_window",
            "name": f"Documentos abiertos · {self.partner_id.display_name}",
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [
                ("company_id", "=", self.company_id.id),
                ("commercial_partner_id", "=", self.partner_id.id),
                ("move_type", "in", move_types),
                ("state", "=", "posted"),
                ("amount_residual", "!=", 0),
            ],
        }

    def action_refresh_partner(self):
        self.ensure_one()
        self.sudo().refresh_partner(self.company_id, self.partner_id)
        return {"type": "ir.actions.client", "tag": "reload"}

    @api.model
    def action_refresh_current_company(self):
        """Refresh the active company's read-only portfolio cache on demand."""
        plan = self.env["cashflow.plan"].sudo().get_or_create_current_plan()
        plan.action_refresh_open_items()
        self.sudo().refresh_company(self.env.company)
        return {"type": "ir.actions.client", "tag": "reload"}

    @api.model
    def action_print_current_company(self):
        """Refresh and print the active company's current CxC/CxP view."""
        direction = self.env.context.get("cashflow_report_direction")
        if direction not in (False, None, "receivable", "payable"):
            raise UserError("El tipo de cartera solicitado no es válido.")
        plan = self.env["cashflow.plan"].sudo().get_or_create_current_plan()
        plan.action_refresh_open_items()
        self.sudo().refresh_company(self.env.company)
        domain = [("company_id", "=", self.env.company.id)]
        if direction:
            domain.append(("direction", "=", direction))
        snapshots = self.search(domain)
        if not snapshots:
            raise UserError("Odoo no muestra partidas abiertas para este detalle.")
        return self.env.ref("megatk_cash_flow_forecast.action_report_portfolio").report_action(
            snapshots.with_context(cashflow_report_direction=direction)
        )

    def action_open_management_history(self):
        self.ensure_one()
        if self.direction != "receivable":
            raise UserError("El historial de cobranza solo corresponde a cuentas por cobrar.")
        return {
            "type": "ir.actions.act_window",
            "name": f"Historial de cobros · {self.partner_id.display_name}",
            "res_model": "cashflow.management.note",
            "view_mode": "list,form",
            "domain": [
                ("company_id", "=", self.company_id.id),
                ("partner_id", "=", self.partner_id.id),
                ("direction", "=", "receivable"),
            ],
            "context": {
                "default_company_id": self.company_id.id,
                "default_partner_id": self.partner_id.id,
                "default_direction": "receivable",
            },
        }
