import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError


HONDURAS_TZ = pytz.timezone("America/Tegucigalpa")


class CashflowBankReconciliationSnapshot(models.Model):
    _name = "cashflow.bank.reconciliation.snapshot"
    _description = "Corte de conciliación bancaria del flujo"
    _order = "cutoff_date desc, account_id"
    _check_company_auto = True

    plan_id = fields.Many2one(
        "cashflow.plan", required=True, ondelete="cascade", check_company=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company", required=True, index=True, check_company=True,
    )
    company_currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", store=True,
    )
    position_id = fields.Many2one(
        "cashflow.bank.position", required=True, ondelete="cascade",
        check_company=True, index=True,
    )
    journal_id = fields.Many2one(
        "account.journal", string="Diario bancario", check_company=True,
    )
    account_id = fields.Many2one(
        "account.account", required=True, string="Cuenta bancaria",
        check_company=True, index=True,
    )
    currency_id = fields.Many2one(
        "res.currency", required=True, string="Moneda de la cuenta",
    )
    cutoff_date = fields.Date(required=True, index=True, string="Fecha del corte")
    captured_at = fields.Datetime(required=True, default=fields.Datetime.now, string="Generado el")
    capture_source = fields.Selection(
        [("automatic", "Automático"), ("manual", "Manual")],
        required=True, default="manual", string="Origen",
    )
    is_latest = fields.Boolean(default=False, index=True, string="Último corte")
    accounting_balance = fields.Monetary(
        currency_field="currency_id", string="Saldo según Odoo",
    )
    real_balance = fields.Monetary(
        currency_field="currency_id", string="Saldo real",
    )
    difference = fields.Monetary(
        currency_field="currency_id", string="Diferencia",
    )
    accounting_balance_company = fields.Monetary(
        currency_field="company_currency_id", string="Saldo Odoo equivalente",
    )
    real_balance_company = fields.Monetary(
        currency_field="company_currency_id", string="Saldo real equivalente",
    )
    difference_company = fields.Monetary(
        currency_field="company_currency_id", string="Diferencia equivalente",
    )
    absolute_difference_company = fields.Monetary(
        currency_field="company_currency_id", string="Diferencia absoluta",
    )
    match_percentage = fields.Float(
        digits=(16, 2), string="Coincidencia (%)",
        help="Porcentaje de coincidencia entre el saldo real y el saldo contable de Odoo.",
    )
    status = fields.Selection(
        [
            ("reconciled", "Conciliada"),
            ("review", "Revisar"),
            ("critical", "Crítica"),
        ],
        required=True, index=True, string="Estado",
    )

    _sql_constraints = [
        (
            "cashflow_bank_reconciliation_unique",
            "unique(company_id, cutoff_date, account_id)",
            "Solo puede existir un corte diario por cuenta bancaria.",
        ),
    ]

    @api.model
    def _status_for_difference(self, difference):
        absolute = abs(difference)
        if absolute <= 5000:
            return "reconciled"
        if absolute <= 100000:
            return "review"
        return "critical"

    @api.model
    def _match_percentage(self, real_balance, accounting_balance):
        base = max(abs(real_balance), abs(accounting_balance))
        if not base:
            return 100.0
        return max(0.0, 100.0 - (abs(real_balance - accounting_balance) / base * 100.0))

    @api.model
    def action_capture_current_company(self):
        plan = self.env["cashflow.plan"].search([
            ("company_id", "=", self.env.company.id),
        ], limit=1)
        if not plan:
            raise UserError(_("No existe un flujo proyectado para la empresa activa."))
        plan._capture_bank_reconciliation(source="manual")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Corte bancario generado"),
                "message": _("Se guardó la comparación actual entre los saldos reales y Odoo."),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }


class CashflowPlanBankReconciliation(models.Model):
    _inherit = "cashflow.plan"

    def _capture_bank_reconciliation(self, cutoff_date=None, source="manual", captured_at=None):
        Snapshot = self.env["cashflow.bank.reconciliation.snapshot"].sudo()
        all_snapshots = Snapshot.browse()
        cutoff_date = cutoff_date or fields.Date.context_today(self)
        captured_at = captured_at or fields.Datetime.now()
        for plan in self:
            positions = plan.bank_position_ids.filtered(
                lambda position: position.position_type == "liquidity" and position.account_id
            )
            if not positions:
                continue
            Snapshot.search([
                ("company_id", "=", plan.company_id.id),
                ("is_latest", "=", True),
            ]).write({"is_latest": False})
            for position in positions:
                real = position.real_balance
                accounting = position.accounting_balance
                difference = real - accounting
                real_company = position.real_balance_company
                accounting_company = position.accounting_balance_company
                difference_company = real_company - accounting_company
                values = {
                    "plan_id": plan.id,
                    "company_id": plan.company_id.id,
                    "position_id": position.id,
                    "journal_id": position.journal_id.id,
                    "account_id": position.account_id.id,
                    "currency_id": position.currency_id.id,
                    "cutoff_date": cutoff_date,
                    "captured_at": captured_at,
                    "capture_source": source,
                    "is_latest": True,
                    "accounting_balance": accounting,
                    "real_balance": real,
                    "difference": difference,
                    "accounting_balance_company": accounting_company,
                    "real_balance_company": real_company,
                    "difference_company": difference_company,
                    "absolute_difference_company": abs(difference_company),
                    "match_percentage": Snapshot._match_percentage(real_company, accounting_company),
                    "status": Snapshot._status_for_difference(difference_company),
                }
                snapshot = Snapshot.search([
                    ("company_id", "=", plan.company_id.id),
                    ("cutoff_date", "=", cutoff_date),
                    ("account_id", "=", position.account_id.id),
                ], limit=1)
                if snapshot:
                    snapshot.write(values)
                else:
                    snapshot = Snapshot.create(values)
                all_snapshots |= snapshot
        return all_snapshots

    @api.model
    def get_bank_status_dashboard_data(self):
        plan = self.search([("company_id", "=", self.env.company.id)], limit=1)
        if not plan:
            return {
                "company": self.env.company.display_name,
                "currency": self.env.company.currency_id.name,
                "accounts": [],
                "history": [],
                "totals": {
                    "real": 0.0,
                    "accounting": 0.0,
                    "difference": 0.0,
                    "absolute_difference": 0.0,
                    "match_percentage": 100.0,
                },
            }
        Snapshot = self.env["cashflow.bank.reconciliation.snapshot"]
        positions = plan.bank_position_ids.filtered(
            lambda position: position.position_type == "liquidity" and position.account_id
        )
        accounts = []
        total_real = total_accounting = 0.0
        for position in positions:
            real = position.real_balance_company
            accounting = position.accounting_balance_company
            difference = real - accounting
            total_real += real
            total_accounting += accounting
            accounts.append({
                "id": position.id,
                "name": position.account_id.display_name,
                "journal": position.journal_id.display_name or "",
                "currency": position.currency_id.name,
                "real_original": position.real_balance,
                "accounting_original": position.accounting_balance,
                "difference_original": position.real_balance - position.accounting_balance,
                "real": real,
                "accounting": accounting,
                "difference": difference,
                "match_percentage": Snapshot._match_percentage(real, accounting),
                "status": Snapshot._status_for_difference(difference),
            })
        accounts.sort(key=lambda item: abs(item["difference"]), reverse=True)
        history_by_date = {}
        snapshots = Snapshot.search([
            ("company_id", "=", plan.company_id.id),
        ], order="cutoff_date desc, account_id", limit=400)
        for snapshot in snapshots:
            key = fields.Date.to_string(snapshot.cutoff_date)
            history = history_by_date.setdefault(key, {
                "date": key,
                "real": 0.0,
                "accounting": 0.0,
                "absolute_difference": 0.0,
            })
            history["real"] += snapshot.real_balance_company
            history["accounting"] += snapshot.accounting_balance_company
            history["absolute_difference"] += snapshot.absolute_difference_company
        history = sorted(history_by_date.values(), key=lambda item: item["date"])[-8:]
        for item in history:
            item["match_percentage"] = Snapshot._match_percentage(
                item["real"], item["accounting"]
            )
        difference = total_real - total_accounting
        return {
            "company": plan.company_id.display_name,
            "currency": plan.currency_id.name,
            "accounts": accounts,
            "history": history,
            "totals": {
                "real": total_real,
                "accounting": total_accounting,
                "difference": difference,
                "absolute_difference": sum(abs(item["difference"]) for item in accounts),
                "match_percentage": Snapshot._match_percentage(total_real, total_accounting),
            },
        }

    @api.model
    def _cron_capture_bank_reconciliation(self, now=None):
        """Capture one Friday close after 18:00 Honduras time."""
        now_utc = fields.Datetime.to_datetime(now or fields.Datetime.now())
        if now_utc.tzinfo:
            local_now = now_utc.astimezone(HONDURAS_TZ)
        else:
            local_now = pytz.UTC.localize(now_utc).astimezone(HONDURAS_TZ)
        if local_now.weekday() != 4 or local_now.hour < 18:
            return False
        cutoff_date = local_now.date()
        captured_at = now_utc.astimezone(pytz.UTC).replace(tzinfo=None) if now_utc.tzinfo else now_utc
        Snapshot = self.env["cashflow.bank.reconciliation.snapshot"].sudo()
        for plan in self.sudo().search([]):
            already_captured = Snapshot.search_count([
                ("company_id", "=", plan.company_id.id),
                ("cutoff_date", "=", cutoff_date),
                ("capture_source", "=", "automatic"),
            ])
            if not already_captured:
                plan._capture_bank_reconciliation(
                    cutoff_date=cutoff_date,
                    source="automatic",
                    captured_at=captured_at,
                )
        return True
