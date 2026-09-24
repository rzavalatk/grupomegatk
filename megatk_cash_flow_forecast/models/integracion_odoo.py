from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    cashflow_receivable_balance = fields.Monetary(
        compute="_compute_cashflow_balances",
        currency_field="cashflow_currency_id",
        string="CxC pendiente",
    )
    cashflow_payable_balance = fields.Monetary(
        compute="_compute_cashflow_balances",
        currency_field="cashflow_currency_id",
        string="CxP pendiente",
    )
    cashflow_currency_id = fields.Many2one(
        "res.currency", compute="_compute_cashflow_balances"
    )
    cashflow_management_count = fields.Integer(
        compute="_compute_cashflow_counts", string="Gestiones de cobranza"
    )
    cashflow_promise_count = fields.Integer(
        compute="_compute_cashflow_counts", string="Promesas activas"
    )

    def _cashflow_commercial_partners(self):
        return self.mapped("commercial_partner_id")

    @api.depends_context("company", "allowed_company_ids")
    def _compute_cashflow_balances(self):
        MoveLine = self.env["account.move.line"].sudo()
        for partner in self:
            commercial = partner.commercial_partner_id
            domain = [
                ("company_id", "=", self.env.company.id),
                ("parent_state", "=", "posted"),
                ("partner_id", "child_of", commercial.id),
                ("account_id.account_type", "in", ("asset_receivable", "liability_payable")),
                ("amount_residual", "!=", 0),
            ]
            receivable = 0.0
            payable = 0.0
            for line in MoveLine.search(domain):
                if line.account_id.account_type == "asset_receivable":
                    receivable += line.amount_residual
                else:
                    payable -= line.amount_residual
            partner.cashflow_currency_id = self.env.company.currency_id
            partner.cashflow_receivable_balance = receivable
            partner.cashflow_payable_balance = payable

    def _compute_cashflow_counts(self):
        Note = self.env["cashflow.management.note"]
        Promise = self.env["cashflow.promise"]
        for partner in self:
            commercial = partner.commercial_partner_id
            partner.cashflow_management_count = Note.search_count([
                ("company_id", "=", self.env.company.id),
                ("partner_id", "=", commercial.id),
            ])
            partner.cashflow_promise_count = Promise.search_count([
                ("company_id", "=", self.env.company.id),
                ("commercial_partner_id", "=", commercial.id),
                ("state", "=", "active"),
            ])

    def action_cashflow_open_receivables(self):
        self.ensure_one()
        commercial = self.commercial_partner_id
        self.env["cashflow.portfolio.snapshot"].sudo().refresh_partner(
            self.env.company, commercial
        )
        return {
            "type": "ir.actions.act_window",
            "name": f"Cuenta por cobrar · {commercial.display_name}",
            "res_model": "cashflow.portfolio.snapshot",
            "view_mode": "list",
            "domain": [
                ("company_id", "=", self.env.company.id),
                ("partner_id", "=", commercial.id),
                ("direction", "=", "receivable"),
            ],
            "context": {"cashflow_report_direction": "receivable"},
        }

    def action_cashflow_open_management_history(self):
        self.ensure_one()
        commercial = self.commercial_partner_id
        return {
            "type": "ir.actions.act_window",
            "name": f"Historial de cobranza · {commercial.display_name}",
            "res_model": "cashflow.management.note",
            "view_mode": "list,form",
            "domain": [
                ("company_id", "=", self.env.company.id),
                ("partner_id", "=", commercial.id),
            ],
            "context": {
                "default_company_id": self.env.company.id,
                "default_partner_id": commercial.id,
            },
        }

    def action_cashflow_open_payables(self):
        self.ensure_one()
        commercial = self.commercial_partner_id
        self.env["cashflow.portfolio.snapshot"].sudo().refresh_partner(
            self.env.company, commercial
        )
        return {
            "type": "ir.actions.act_window",
            "name": f"Cuenta por pagar · {commercial.display_name}",
            "res_model": "cashflow.portfolio.snapshot",
            "view_mode": "list",
            "domain": [
                ("company_id", "=", self.env.company.id),
                ("partner_id", "=", commercial.id),
                ("direction", "=", "payable"),
            ],
            "context": {"cashflow_report_direction": "payable"},
        }

    def action_cashflow_open_promises(self):
        self.ensure_one()
        commercial = self.commercial_partner_id
        return {
            "type": "ir.actions.act_window",
            "name": f"Proyecciones activas · {commercial.display_name}",
            "res_model": "cashflow.promise",
            "view_mode": "list,form",
            "domain": [
                ("company_id", "=", self.env.company.id),
                ("commercial_partner_id", "=", commercial.id),
                ("state", "=", "active"),
            ],
            "context": {
                "default_company_id": self.env.company.id,
                "default_partner_id": commercial.id,
            },
        }


class AccountMove(models.Model):
    _inherit = "account.move"

    cashflow_management_count = fields.Integer(
        compute="_compute_cashflow_management_count", string="Gestiones de cobranza"
    )
    cashflow_projection_count = fields.Integer(
        compute="_compute_cashflow_projection_count", string="Proyecciones activas"
    )

    def _compute_cashflow_management_count(self):
        Note = self.env["cashflow.management.note"]
        for move in self:
            move.cashflow_management_count = Note.search_count([
                ("company_id", "=", move.company_id.id),
                ("move_id", "=", move.id),
            ])

    def _compute_cashflow_projection_count(self):
        Promise = self.env["cashflow.promise"]
        for move in self:
            move.cashflow_projection_count = Promise.search_count([
                ("company_id", "=", move.company_id.id),
                ("source_move_id", "=", move.id),
                ("state", "=", "active"),
            ])

    def action_cashflow_schedule_document(self):
        self.ensure_one()
        if self.state != "posted" or self.move_type not in (
            "out_invoice", "out_refund", "in_invoice", "in_refund"
        ):
            return False
        direction = (
            "receivable"
            if self.move_type in ("out_invoice", "out_refund")
            else "payable"
        )
        plan = self.env["cashflow.plan"].with_company(
            self.company_id
        ).get_or_create_current_plan()
        classification = self.env["cashflow.portfolio.classification"].search([
            ("company_id", "=", self.company_id.id),
            ("partner_id", "=", self.commercial_partner_id.id),
            ("direction", "=", direction),
        ], limit=1)
        return {
            "type": "ir.actions.act_window",
            "name": "Programar cobro" if direction == "receivable" else "Programar pago",
            "res_model": "cashflow.promise",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_plan_id": plan.id,
                "default_partner_id": self.commercial_partner_id.id,
                "default_direction": direction,
                "default_source_move_id": self.id,
                "default_classification_id": classification.id or False,
                "default_currency_id": self.currency_id.id,
                "default_rate_date": fields.Date.context_today(self),
                "default_amount": abs(self.amount_residual),
                "default_period": "week_1",
            },
        }

    def action_cashflow_open_projections(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Proyecciones · {self.name}",
            "res_model": "cashflow.promise",
            "view_mode": "list,form",
            "domain": [
                ("company_id", "=", self.company_id.id),
                ("source_move_id", "=", self.id),
            ],
            "context": {
                "default_partner_id": self.commercial_partner_id.id,
                "default_source_move_id": self.id,
            },
        }

    def action_cashflow_add_management_note(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Registrar gestión de cobranza",
            "res_model": "cashflow.management.note",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_company_id": self.company_id.id,
                "default_partner_id": self.commercial_partner_id.id,
                "default_move_id": self.id,
                "default_direction": "receivable",
            },
        }

    def action_cashflow_open_management_history(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Historial de cobranza · {self.name}",
            "res_model": "cashflow.management.note",
            "view_mode": "list,form",
            "domain": [("company_id", "=", self.company_id.id), ("move_id", "=", self.id)],
            "context": {
                "default_company_id": self.company_id.id,
                "default_partner_id": self.commercial_partner_id.id,
                "default_move_id": self.id,
            },
        }
