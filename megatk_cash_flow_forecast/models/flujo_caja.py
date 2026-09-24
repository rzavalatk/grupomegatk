from odoo import api, fields, models
from odoo.exceptions import ValidationError


PERIODS = [
    ("week_1", "Semana 1"),
    ("week_2", "Semana 2"),
    ("week_3", "Semana 3"),
    ("pending", "Pendiente"),
]

PORTFOLIO_CLASSIFICATIONS = [
    ("customer", "Clientes"),
    ("employee_receivable", "CxC empleados"),
    ("group_receivable", "Grupo Mega"),
    ("supplier", "Proveedores"),
    ("creditor", "Acreedores"),
    ("advance", "Anticipos"),
    ("legal", "En legal"),
    ("to_reconcile", "Por depurar"),
    ("unassigned", "Por asignar"),
]


class CashflowPlan(models.Model):
    _name = "cashflow.plan"
    _description = "Flujo de caja proyectado"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "company_id"

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    bank_position_ids = fields.One2many("cashflow.bank.position", "plan_id", string="Disponible por banco")
    promise_ids = fields.One2many("cashflow.promise", "plan_id", string="Promesas y pagos")
    manual_income_ids = fields.One2many(
        "cashflow.manual.income", "plan_id", string="Otros ingresos proyectados"
    )
    manual_expense_ids = fields.One2many("cashflow.manual.expense", "plan_id", string="Egresos manuales")
    total_real_available = fields.Monetary(compute="_compute_totals", string="Disponible real")
    total_expected_receivable = fields.Monetary(compute="_compute_totals", string="Cobros de clientes")
    total_other_income = fields.Monetary(compute="_compute_totals", string="Otros ingresos")
    total_expected_payable = fields.Monetary(compute="_compute_totals", string="Pagos y egresos")
    projected_balance = fields.Monetary(compute="_compute_totals", string="Flujo estimado")
    receivable_week_1 = fields.Monetary(compute="_compute_period_totals", string="Cobros · Semana 1")
    receivable_week_2 = fields.Monetary(compute="_compute_period_totals", string="Cobros · Semana 2")
    receivable_week_3 = fields.Monetary(compute="_compute_period_totals", string="Cobros · Semana 3")
    receivable_pending = fields.Monetary(compute="_compute_period_totals", string="Cobros · Pendiente")
    other_income_week_1 = fields.Monetary(compute="_compute_period_totals", string="Otros ingresos · Semana 1")
    other_income_week_2 = fields.Monetary(compute="_compute_period_totals", string="Otros ingresos · Semana 2")
    other_income_week_3 = fields.Monetary(compute="_compute_period_totals", string="Otros ingresos · Semana 3")
    other_income_pending = fields.Monetary(compute="_compute_period_totals", string="Otros ingresos · Pendiente")
    payable_week_1 = fields.Monetary(compute="_compute_period_totals", string="Pagos · Semana 1")
    payable_week_2 = fields.Monetary(compute="_compute_period_totals", string="Pagos · Semana 2")
    payable_week_3 = fields.Monetary(compute="_compute_period_totals", string="Pagos · Semana 3")
    payable_pending = fields.Monetary(compute="_compute_period_totals", string="Pagos · Pendiente")
    projected_week_1 = fields.Monetary(compute="_compute_projected_period_balances", string="Saldo proyectado · Semana 1")
    projected_week_2 = fields.Monetary(compute="_compute_projected_period_balances", string="Saldo proyectado · Semana 2")
    projected_week_3 = fields.Monetary(compute="_compute_projected_period_balances", string="Saldo proyectado · Semana 3")
    projected_pending = fields.Monetary(compute="_compute_projected_period_balances", string="Saldo proyectado · Pendiente")

    _sql_constraints = [("cashflow_plan_company_unique", "unique(company_id)", "Solo puede existir un flujo proyectado por empresa.")]

    @api.depends(
        "bank_position_ids.real_balance", "bank_position_ids.position_type",
        "promise_ids.company_amount", "promise_ids.direction", "promise_ids.state",
        "manual_income_ids.company_amount", "manual_income_ids.active",
        "manual_expense_ids.company_amount", "manual_expense_ids.active",
    )
    def _compute_totals(self):
        for record in self:
            real = sum(
                record.bank_position_ids.filtered(
                    lambda position: position.position_type == "liquidity"
                ).mapped("real_balance")
            )
            receivable = sum(record.promise_ids.filtered(lambda p: p.state == "active" and p.direction == "receivable").mapped("company_amount"))
            other_income = sum(record.manual_income_ids.filtered("active").mapped("company_amount"))
            payable = sum(record.promise_ids.filtered(lambda p: p.state == "active" and p.direction == "payable").mapped("company_amount"))
            manual = sum(record.manual_expense_ids.filtered("active").mapped("company_amount"))
            record.total_real_available = real
            record.total_expected_receivable = receivable
            record.total_other_income = other_income
            record.total_expected_payable = payable + manual
            record.projected_balance = real + receivable + other_income - payable - manual

    @api.depends(
        "promise_ids.company_amount", "promise_ids.direction", "promise_ids.period", "promise_ids.state",
        "manual_income_ids.company_amount", "manual_income_ids.period", "manual_income_ids.active",
        "manual_expense_ids.company_amount", "manual_expense_ids.period", "manual_expense_ids.active",
    )
    def _compute_period_totals(self):
        for record in self:
            for prefix in ("receivable", "other_income", "payable"):
                for period, _label in PERIODS:
                    setattr(record, f"{prefix}_{period}", 0)
            for promise in record.promise_ids.filtered(lambda p: p.state == "active"):
                field_name = f"{promise.direction}_{promise.period}"
                setattr(record, field_name, getattr(record, field_name) + promise.company_amount)
            for income in record.manual_income_ids.filtered("active"):
                field_name = f"other_income_{income.period}"
                setattr(record, field_name, getattr(record, field_name) + income.company_amount)
            for expense in record.manual_expense_ids.filtered("active"):
                field_name = f"payable_{expense.period}"
                setattr(record, field_name, getattr(record, field_name) + expense.company_amount)

    @api.depends(
        "total_real_available",
        "receivable_week_1", "receivable_week_2", "receivable_week_3", "receivable_pending",
        "other_income_week_1", "other_income_week_2", "other_income_week_3", "other_income_pending",
        "payable_week_1", "payable_week_2", "payable_week_3", "payable_pending",
    )
    def _compute_projected_period_balances(self):
        for record in self:
            running = record.total_real_available
            for period, _label in PERIODS:
                running += (
                    getattr(record, f"receivable_{period}")
                    + getattr(record, f"other_income_{period}")
                    - getattr(record, f"payable_{period}")
                )
                setattr(record, f"projected_{period}", running)

    @api.model
    def get_or_create_current_plan(self):
        plan = self.search([("company_id", "=", self.env.company.id)], limit=1)
        return plan or self.create({"company_id": self.env.company.id})

    @api.model
    def action_open_current_plan(self):
        """Open the one operational projection for the active company."""
        plan = self.get_or_create_current_plan()
        return {
            "type": "ir.actions.act_window",
            "name": "Flujo de caja proyectado",
            "res_model": "cashflow.plan",
            "res_id": plan.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_refresh_open_items(self):
        """Retire projections whose underlying debt no longer exists in Odoo."""
        MoveLine = self.env["account.move.line"]
        for plan in self:
            settled = self.env["cashflow.promise"]
            for promise in plan.promise_ids.filtered(lambda p: p.state == "active"):
                if promise.source_move_line_id or promise.source_move_id:
                    if not promise.source_open:
                        settled |= promise
                    continue
                account_type = "asset_receivable" if promise.direction == "receivable" else "liability_payable"
                residual_operator = ">" if promise.direction == "receivable" else "<"
                has_open_debt = MoveLine.search_count([
                    ("company_id", "=", promise.company_id.id),
                    ("parent_state", "=", "posted"),
                    ("account_id.account_type", "=", account_type),
                    ("partner_id", "child_of", promise.commercial_partner_id.id),
                    ("amount_residual", residual_operator, 0),
                ], limit=1)
                if not has_open_debt:
                    settled |= promise
            for promise in settled:
                promise.message_post(
                    body="Odoo ya no muestra una deuda abierta para este contacto; se retiró de la proyección."
                )
            settled.write({"state": "cancelled"})

    def action_refresh_portfolio(self):
        self.ensure_one()
        self.action_refresh_open_items()
        # The report is a cache derived from Odoo's open items.  It must be
        # rebuilt without requiring normal planning users to delete records.
        self.env["cashflow.portfolio.snapshot"].sudo().refresh_company(self.company_id)
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_print_portfolio(self):
        self.ensure_one()
        self.action_refresh_portfolio()
        snapshots = self.env["cashflow.portfolio.snapshot"].search([
            ("company_id", "=", self.company_id.id),
        ])
        return self.env.ref("megatk_cash_flow_forecast.action_report_portfolio").report_action(snapshots)

    @api.model
    def _cron_refresh_open_promises(self):
        self.sudo().search([]).action_refresh_open_items()

    @api.model
    def _cron_refresh_portfolio(self):
        for company in self.env["res.company"].search([]):
            self.env["cashflow.portfolio.snapshot"].sudo().refresh_company(company)


class CashflowBankPosition(models.Model):
    _name = "cashflow.bank.position"
    _description = "Disponible bancario proyectado"
    _order = "journal_id"
    _check_company_auto = True

    plan_id = fields.Many2one("cashflow.plan", required=True, ondelete="cascade", check_company=True)
    company_id = fields.Many2one(related="plan_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="plan_id.currency_id", store=True)
    position_type = fields.Selection(
        [
            ("liquidity", "Efectivo / banco"),
            ("credit_card", "Tarjeta de crédito"),
            ("loan", "Préstamo por pagar"),
        ],
        required=True,
        default="liquidity",
        string="Tipo",
    )
    journal_id = fields.Many2one(
        "account.journal", domain="[('type', 'in', ('bank', 'cash'))]",
        string="Diario bancario", check_company=True,
    )
    account_id = fields.Many2one(
        "account.account", string="Cuenta del catálogo", check_company=True,
        help="Úsela si la tarjeta o cuenta no tiene un diario bancario configurado.",
    )
    accounting_balance = fields.Monetary(compute="_compute_accounting_balance", readonly=True, string="Saldo contable")
    real_balance = fields.Monetary(required=True, string="Saldo real / disponible")
    balance_difference = fields.Monetary(compute="_compute_balance_difference", string="Diferencia contra Odoo")

    _sql_constraints = [
        ("cashflow_bank_journal_unique", "unique(plan_id, journal_id)", "El diario solo puede agregarse una vez al flujo."),
        ("cashflow_bank_account_unique", "unique(plan_id, account_id)", "La cuenta solo puede agregarse una vez al flujo."),
    ]

    @api.constrains("position_type", "journal_id", "account_id")
    def _check_balance_source(self):
        for record in self:
            if bool(record.journal_id) == bool(record.account_id):
                raise ValidationError("Seleccione un diario bancario o una cuenta del catálogo, pero no ambos.")
            if record.position_type != "liquidity" and record.journal_id:
                raise ValidationError("Las tarjetas y préstamos deben vincularse con su cuenta de pasivo del catálogo.")
            if record.account_id:
                allowed = {
                    "liquidity": {"asset_cash"},
                    "credit_card": {"liability_credit_card", "liability_current", "liability_payable"},
                    "loan": {"liability_current", "liability_non_current", "liability_payable"},
                }
                if record.account_id.account_type not in allowed[record.position_type]:
                    raise ValidationError("La cuenta seleccionada no corresponde al tipo de saldo indicado.")

    @api.onchange("journal_id", "account_id")
    def _onchange_prevent_duplicate_source(self):
        """Reject a repeated source immediately, before the user saves the form."""
        if not self.plan_id:
            return
        siblings = self.plan_id.bank_position_ids - self
        if self.journal_id and self.journal_id in siblings.mapped("journal_id"):
            self.journal_id = False
            return {
                "warning": {
                    "title": "Diario ya agregado",
                    "message": "Ese diario ya está en el flujo. La línea fue conservada para que pueda escoger otro.",
                }
            }
        if self.account_id and self.account_id in siblings.mapped("account_id"):
            self.account_id = False
            return {
                "warning": {
                    "title": "Cuenta ya agregada",
                    "message": "Esa cuenta ya está en el flujo. La línea fue conservada para que pueda escoger otra.",
                }
            }

    @api.onchange("position_type")
    def _onchange_position_type(self):
        if self.position_type != "liquidity":
            self.journal_id = False

    @api.depends("journal_id", "account_id", "company_id", "position_type")
    def _compute_accounting_balance(self):
        MoveLine = self.env["account.move.line"]
        for record in self:
            account = record.journal_id.default_account_id or record.account_id
            if not account:
                record.accounting_balance = 0
                continue
            grouped = MoveLine.read_group([
                ("account_id", "=", account.id),
                ("parent_state", "=", "posted"),
                ("company_id", "=", record.company_id.id),
            ], ["balance:sum"], [])
            balance = grouped[0]["balance"] if grouped else 0
            record.accounting_balance = balance if record.position_type == "liquidity" else -balance

    @api.depends("real_balance", "accounting_balance")
    def _compute_balance_difference(self):
        for record in self:
            record.balance_difference = record.real_balance - record.accounting_balance


class CashflowClassification(models.Model):
    _name = "cashflow.portfolio.classification"
    _description = "Clasificación de cartera proyectada"
    _rec_name = "partner_id"

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade", index=True)
    direction = fields.Selection([( "receivable", "Cuenta por cobrar"), ("payable", "Cuenta por pagar")], required=True)
    classification = fields.Selection(
        PORTFOLIO_CLASSIFICATIONS, required=True, default="unassigned"
    )

    _sql_constraints = [("partner_direction_uniq", "unique(company_id, partner_id, direction)", "La cuenta ya tiene una clasificación para esta empresa.")]

    @api.model_create_multi
    def create(self, vals_list):
        normalized = []
        for vals in vals_list:
            values = dict(vals)
            if values.get("partner_id"):
                values["partner_id"] = self.env["res.partner"].browse(values["partner_id"]).commercial_partner_id.id
            normalized.append(values)
        return super().create(normalized)

    def write(self, vals):
        values = dict(vals)
        if values.get("partner_id"):
            values["partner_id"] = self.env["res.partner"].browse(values["partner_id"]).commercial_partner_id.id
        return super().write(values)

    @api.constrains("direction", "classification")
    def _check_classification_direction(self):
        allowed = {
            "receivable": {"customer", "employee_receivable", "group_receivable", "legal", "to_reconcile", "unassigned"},
            "payable": {"supplier", "creditor", "advance", "to_reconcile", "unassigned"},
        }
        for record in self:
            if record.classification not in allowed[record.direction]:
                raise ValidationError("La clasificación seleccionada no corresponde al tipo de cuenta.")


class CashflowPromise(models.Model):
    _name = "cashflow.promise"
    _description = "Promesa de cobro o pago"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "period, partner_id"
    _check_company_auto = True

    plan_id = fields.Many2one(
        "cashflow.plan", required=True, string="Flujo de la empresa",
        default=lambda self: self.env["cashflow.plan"].get_or_create_current_plan(),
        ondelete="cascade", check_company=True,
    )
    company_id = fields.Many2one(related="plan_id.company_id", store=True, index=True)
    partner_id = fields.Many2one("res.partner", required=True, tracking=True, string="Cliente / proveedor")
    commercial_partner_id = fields.Many2one(related="partner_id.commercial_partner_id", store=True)
    direction = fields.Selection(
        [("receivable", "Cobro de cliente"), ("payable", "Pago a proveedor")],
        required=True, tracking=True, string="Tipo de movimiento",
    )
    period = fields.Selection(PERIODS, required=True, default="week_1", tracking=True, string="Semana")
    company_currency_id = fields.Many2one(related="plan_id.currency_id", store=True)
    currency_id = fields.Many2one(
        "res.currency", required=True, string="Moneda del pago",
        default=lambda self: self.env.company.currency_id,
    )
    amount = fields.Monetary(
        required=True, tracking=True, string="Monto en moneda",
        currency_field="currency_id",
    )
    rate_date = fields.Date(
        required=True, default=fields.Date.context_today,
        string="Fecha del tipo de cambio", tracking=True,
    )
    company_amount = fields.Monetary(
        currency_field="company_currency_id", compute="_compute_company_amount",
        string="Equivalente en moneda de la empresa",
    )
    current_open_balance = fields.Monetary(
        compute="_compute_current_open_balance",
        currency_field="company_currency_id",
        string="Saldo actual en Odoo",
        help="Saldo abierto del contacto en la empresa activa. Es informativo y no modifica la contabilidad.",
    )
    projected_remaining_balance = fields.Monetary(
        compute="_compute_current_open_balance", string="Saldo después de la proyección",
        currency_field="company_currency_id",
    )
    source_move_id = fields.Many2one(
        "account.move", string="Factura o documento de Odoo (opcional)", ondelete="set null", check_company=True,
        domain="[('company_id', '=', company_id), ('partner_id.commercial_partner_id', '=', commercial_partner_id), ('move_type', 'in', direction == 'receivable' and ('out_invoice', 'out_refund') or ('in_invoice', 'in_refund')), ('state', '=', 'posted'), ('amount_residual', '!=', 0)]",
        help="Opcional. Permite relacionar la proyección con una factura o documento concreto.",
    )
    source_move_line_id = fields.Many2one(
        "account.move.line", string="Partida contable técnica de Odoo", ondelete="set null", check_company=True,
        domain="[('company_id', '=', company_id), ('partner_id.commercial_partner_id', '=', commercial_partner_id), ('account_id.account_type', '=', direction == 'receivable' and 'asset_receivable' or 'liability_payable')]",
        help="Opcional. Si esta partida queda saldada en Odoo, se retira automáticamente de la proyección.",
    )
    source_residual = fields.Monetary(
        compute="_compute_source_residual", string="Saldo del documento", readonly=True,
        currency_field="company_currency_id",
    )
    source_open = fields.Boolean(compute="_compute_source_open")
    note = fields.Text(
        string="Última gestión",
        tracking=True,
        readonly=True,
        help="Se actualiza desde el historial de gestiones; no reemplaza ni elimina las gestiones anteriores.",
    )
    state = fields.Selection(
        [("active", "Activo"), ("cancelled", "Cancelado")],
        default="active", required=True, tracking=True, string="Estado",
    )
    classification_id = fields.Many2one(
        "cashflow.portfolio.classification", string="Clasificación", check_company=True,
        domain="[('company_id', '=', company_id), ('partner_id', '=', commercial_partner_id), ('direction', '=', direction)]",
    )
    classification = fields.Selection(
        PORTFOLIO_CLASSIFICATIONS,
        compute="_compute_classification",
        inverse="_inverse_classification",
        string="Clasificación",
        help="Puede clasificar o reclasificar el contacto directamente desde la proyección.",
    )

    @api.depends("classification_id.classification")
    def _compute_classification(self):
        for promise in self:
            promise.classification = promise.classification_id.classification or "unassigned"

    def _inverse_classification(self):
        Classification = self.env["cashflow.portfolio.classification"]
        for promise in self:
            if not (
                promise.company_id
                and promise.commercial_partner_id
                and promise.direction
                and promise.classification
            ):
                continue
            classification = Classification.search([
                ("company_id", "=", promise.company_id.id),
                ("partner_id", "=", promise.commercial_partner_id.id),
                ("direction", "=", promise.direction),
            ], limit=1)
            values = {"classification": promise.classification}
            if classification:
                classification.write(values)
            else:
                values.update({
                    "company_id": promise.company_id.id,
                    "partner_id": promise.commercial_partner_id.id,
                    "direction": promise.direction,
                })
                classification = Classification.create(values)
            promise.classification_id = classification

    def _open_balance_for(self, partner, direction, company):
        if not partner or not direction or not company:
            return 0.0
        account_type = "asset_receivable" if direction == "receivable" else "liability_payable"
        lines = self.env["account.move.line"].sudo().search([
            ("company_id", "=", company.id),
            ("parent_state", "=", "posted"),
            ("partner_id", "child_of", partner.commercial_partner_id.id),
            ("account_id.account_type", "=", account_type),
            ("amount_residual", "!=", 0),
        ])
        signed = sum(lines.mapped("amount_residual"))
        return signed if direction == "receivable" else -signed

    @api.depends("partner_id", "direction", "company_id", "company_amount")
    def _compute_current_open_balance(self):
        for promise in self:
            balance = promise._open_balance_for(
                promise.partner_id, promise.direction, promise.company_id
            )
            promise.current_open_balance = balance
            promise.projected_remaining_balance = balance - promise.company_amount

    @api.depends("amount", "currency_id", "company_currency_id", "company_id", "rate_date")
    def _compute_company_amount(self):
        for promise in self:
            if not promise.currency_id or not promise.company_currency_id or not promise.company_id:
                promise.company_amount = 0
                continue
            promise.company_amount = promise.currency_id._convert(
                promise.amount,
                promise.company_currency_id,
                promise.company_id,
                promise.rate_date or fields.Date.context_today(promise),
            )

    @api.depends(
        "source_move_id.amount_residual",
        "source_move_line_id.amount_residual",
        "direction",
    )
    def _compute_source_residual(self):
        for promise in self:
            if promise.source_move_line_id:
                residual = promise.source_move_line_id.amount_residual
            elif promise.source_move_id:
                lines = promise.source_move_id.line_ids.filtered(
                    lambda line: line.account_id.account_type
                    == ("asset_receivable" if promise.direction == "receivable" else "liability_payable")
                )
                residual = sum(lines.mapped("amount_residual"))
            else:
                residual = 0.0
            promise.source_residual = residual if promise.direction == "receivable" else -residual

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_snapshot_periods()
        return records

    def write(self, vals):
        previous_keys = self._snapshot_keys()
        result = super().write(vals)
        self._sync_snapshot_periods(extra_keys=previous_keys)
        return result

    def unlink(self):
        previous_keys = self._snapshot_keys()
        result = super().unlink()
        self.env["cashflow.promise"]._sync_snapshot_periods(extra_keys=previous_keys)
        return result

    def _snapshot_keys(self):
        return {
            (promise.company_id.id, promise.commercial_partner_id.id, promise.direction)
            for promise in self
            if promise.company_id and promise.commercial_partner_id and promise.direction
        }

    def _sync_snapshot_periods(self, extra_keys=None):
        """Keep week badges current without rebuilding accounting balances."""
        keys = self._snapshot_keys() | set(extra_keys or ())
        labels = {
            "week_1": "1",
            "week_2": "2",
            "week_3": "3",
            "pending": "Pend.",
        }
        Snapshot = self.env["cashflow.portfolio.snapshot"].sudo().with_context(
            cashflow_internal_update=True
        )
        Promise = self.env["cashflow.promise"].sudo()
        for company_id, partner_id, direction in keys:
            promises = Promise.search([
                ("company_id", "=", company_id),
                ("commercial_partner_id", "=", partner_id),
                ("direction", "=", direction),
                ("state", "=", "active"),
            ], order="period, id")
            active_periods = set(promises.mapped("period"))
            periods = [labels[period] for period, _label in PERIODS if period in active_periods]
            Snapshot.search([
                ("company_id", "=", company_id),
                ("partner_id", "=", partner_id),
                ("direction", "=", direction),
            ]).write({"projected_periods": ", ".join(periods)})

    @api.onchange("partner_id", "direction", "plan_id")
    def _onchange_projection_identity(self):
        self.source_move_line_id = False
        self.source_move_id = False
        self.classification_id = False
        if self.partner_id and self.direction and self.plan_id:
            self.classification_id = self.env["cashflow.portfolio.classification"].search([
                ("company_id", "=", self.plan_id.company_id.id),
                ("partner_id", "=", self.partner_id.commercial_partner_id.id),
                ("direction", "=", self.direction),
            ], limit=1)
            balance = self._open_balance_for(
                self.partner_id, self.direction, self.plan_id.company_id
            )
            if balance > 0 and not self.amount:
                self.amount = balance

    @api.constrains("amount")
    def _check_positive_amount(self):
        for promise in self:
            if promise.amount <= 0:
                raise ValidationError("El monto proyectado debe ser mayor que cero.")

    @api.constrains("classification_id", "partner_id", "direction", "company_id")
    def _check_classification_consistency(self):
        for promise in self.filtered("classification_id"):
            classification = promise.classification_id
            if (
                classification.company_id != promise.company_id
                or classification.partner_id != promise.commercial_partner_id
                or classification.direction != promise.direction
            ):
                raise ValidationError(
                    "La clasificación debe corresponder a la misma empresa, contacto y tipo de proyección."
                )

    @api.constrains("source_move_line_id", "partner_id", "direction", "company_id")
    def _check_source_move_line_consistency(self):
        for promise in self.filtered("source_move_line_id"):
            line = promise.source_move_line_id
            expected_type = "asset_receivable" if promise.direction == "receivable" else "liability_payable"
            if line.company_id != promise.company_id:
                raise ValidationError("La partida contable debe pertenecer a la misma empresa de la proyección.")
            if line.partner_id.commercial_partner_id != promise.partner_id.commercial_partner_id:
                raise ValidationError("La partida contable debe pertenecer al mismo contacto de la proyección.")
            if line.account_id.account_type != expected_type:
                raise ValidationError("La partida contable no corresponde al tipo de cobro o pago seleccionado.")

    @api.constrains("source_move_id", "partner_id", "direction", "company_id")
    def _check_source_move_consistency(self):
        for promise in self.filtered("source_move_id"):
            move = promise.source_move_id
            expected_types = (
                {"out_invoice", "out_refund"}
                if promise.direction == "receivable"
                else {"in_invoice", "in_refund"}
            )
            if move.company_id != promise.company_id:
                raise ValidationError("El documento debe pertenecer a la misma empresa de la proyección.")
            if move.commercial_partner_id != promise.commercial_partner_id:
                raise ValidationError("El documento debe pertenecer al mismo contacto de la proyección.")
            if move.move_type not in expected_types:
                raise ValidationError("El documento no corresponde al tipo de cobro o pago seleccionado.")

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_add_management_note(self):
        self.ensure_one()
        if self.direction != "receivable":
            raise ValidationError("Las gestiones de cobranza solo corresponden a cobros esperados.")
        return {
            "type": "ir.actions.act_window",
            "name": "Registrar gestión de cobranza",
            "res_model": "cashflow.management.note",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_company_id": self.company_id.id,
                "default_partner_id": self.commercial_partner_id.id,
                "default_promise_id": self.id,
                "default_move_id": self.source_move_id.id or False,
                "default_direction": "receivable",
            },
        }

    def action_open_management_history(self):
        self.ensure_one()
        if self.direction != "receivable":
            raise ValidationError("El historial de cobranza solo corresponde a cobros esperados.")
        return {
            "type": "ir.actions.act_window",
            "name": f"Historial de cobros · {self.commercial_partner_id.display_name}",
            "res_model": "cashflow.management.note",
            "view_mode": "list,form",
            "domain": [
                ("company_id", "=", self.company_id.id),
                ("partner_id", "=", self.commercial_partner_id.id),
                ("direction", "=", "receivable"),
            ],
            "context": {
                "default_company_id": self.company_id.id,
                "default_partner_id": self.commercial_partner_id.id,
                "default_promise_id": self.id,
                "default_move_id": self.source_move_id.id or False,
                "default_direction": "receivable",
            },
        }

    @api.depends(
        "source_move_id.amount_residual",
        "source_move_line_id.amount_residual",
        "source_residual",
    )
    def _compute_source_open(self):
        for promise in self:
            has_source = bool(promise.source_move_id or promise.source_move_line_id)
            promise.source_open = (
                not has_source
                or not promise.company_id.currency_id.is_zero(promise.source_residual)
            )


class CashflowManualIncome(models.Model):
    _name = "cashflow.manual.income"
    _description = "Otro ingreso proyectado"
    _inherit = ["mail.thread"]
    _order = "period, name"
    _check_company_auto = True

    plan_id = fields.Many2one(
        "cashflow.plan", required=True, string="Flujo de la empresa",
        default=lambda self: self.env["cashflow.plan"].get_or_create_current_plan(),
        ondelete="cascade", check_company=True,
    )
    company_id = fields.Many2one(related="plan_id.company_id", store=True, index=True)
    name = fields.Char(required=True, string="Concepto", tracking=True)
    income_type = fields.Selection(
        [
            ("loan", "Préstamo recibido"),
            ("contribution", "Aporte de socios"),
            ("other", "Otro ingreso"),
        ],
        required=True,
        default="other",
        string="Tipo de ingreso",
        tracking=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contacto de Odoo (opcional)",
        help="Puede dejarse vacío cuando la persona o entidad no existe en Odoo.",
    )
    counterparty_name = fields.Char(
        string="Persona o entidad",
        help="Nombre libre para registrar el origen del ingreso sin crear un contacto en Odoo.",
    )
    period = fields.Selection(PERIODS, required=True, default="week_1", tracking=True, string="Semana")
    company_currency_id = fields.Many2one(related="plan_id.currency_id", store=True)
    currency_id = fields.Many2one(
        "res.currency", required=True, string="Moneda",
        default=lambda self: self.env.company.currency_id,
    )
    amount = fields.Monetary(required=True, tracking=True, string="Monto en moneda")
    rate_date = fields.Date(
        required=True, default=fields.Date.context_today,
        string="Fecha del tipo de cambio", tracking=True,
    )
    company_amount = fields.Monetary(
        currency_field="company_currency_id", compute="_compute_company_amount",
        string="Monto para el flujo",
    )
    active = fields.Boolean(default=True)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id and not self.counterparty_name:
            self.counterparty_name = self.partner_id.display_name

    @api.constrains("amount")
    def _check_positive_amount(self):
        for income in self:
            if income.amount <= 0:
                raise ValidationError("El monto del ingreso debe ser mayor que cero.")

    @api.depends("amount", "currency_id", "company_currency_id", "company_id", "rate_date")
    def _compute_company_amount(self):
        for income in self:
            if not income.currency_id or not income.company_currency_id or not income.company_id:
                income.company_amount = 0
                continue
            income.company_amount = income.currency_id._convert(
                income.amount,
                income.company_currency_id,
                income.company_id,
                income.rate_date or fields.Date.context_today(income),
            )


class CashflowManualExpense(models.Model):
    _name = "cashflow.manual.expense"
    _description = "Egreso manual proyectado"
    _inherit = ["mail.thread"]
    _order = "period, name"
    _check_company_auto = True

    plan_id = fields.Many2one(
        "cashflow.plan", required=True, string="Flujo de la empresa",
        default=lambda self: self.env["cashflow.plan"].get_or_create_current_plan(),
        ondelete="cascade", check_company=True,
    )
    company_id = fields.Many2one(related="plan_id.company_id", store=True, index=True)
    name = fields.Char(required=True, string="Concepto", tracking=True)
    classification = fields.Selection(
        [
            ("payroll", "Planilla y personal"),
            ("rent", "Alquiler"),
            ("taxes", "Impuestos"),
            ("services", "Servicios"),
            ("supplier_advance", "Anticipo a proveedor"),
            ("credit_card_payment", "Pago de tarjeta de crédito"),
            ("loan_payment", "Pago de préstamo"),
            ("other", "Otros pagos"),
        ],
        required=True,
        default="other",
        string="Clasificación",
        tracking=True,
    )
    period = fields.Selection(PERIODS, required=True, default="week_1", tracking=True, string="Semana de pago")
    company_currency_id = fields.Many2one(related="plan_id.currency_id", store=True)
    currency_id = fields.Many2one(
        "res.currency", required=True, string="Moneda",
        default=lambda self: self.env.company.currency_id,
    )
    amount = fields.Monetary(required=True, tracking=True, string="Monto en moneda")
    rate_date = fields.Date(
        required=True, default=fields.Date.context_today,
        string="Fecha del tipo de cambio", tracking=True,
    )
    company_amount = fields.Monetary(
        currency_field="company_currency_id", compute="_compute_company_amount",
        string="Monto para el flujo",
    )
    recurring = fields.Boolean(string="Gasto recurrente", help="Se conserva para futuras proyecciones; solo se cambia la semana.", tracking=True)
    active = fields.Boolean(default=True)

    @api.constrains("amount")
    def _check_positive_amount(self):
        for expense in self:
            if expense.amount <= 0:
                raise ValidationError("El monto del egreso debe ser mayor que cero.")

    @api.depends("amount", "currency_id", "company_currency_id", "company_id", "rate_date")
    def _compute_company_amount(self):
        for expense in self:
            if not expense.currency_id or not expense.company_currency_id or not expense.company_id:
                expense.company_amount = 0
                continue
            expense.company_amount = expense.currency_id._convert(
                expense.amount,
                expense.company_currency_id,
                expense.company_id,
                expense.rate_date or fields.Date.context_today(expense),
            )
