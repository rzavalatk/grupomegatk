from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


WEEK_EXPRESSIONS = {
    "week_1": "cashflow_week_1",
    "week_2": "cashflow_week_2",
    "week_3": "cashflow_week_3",
    "pending": "cashflow_pending",
}


class AccountAgedPartnerBalanceReportHandler(models.AbstractModel):
    _inherit = "account.aged.partner.balance.report.handler"

    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options)
        direction = self._cashflow_direction(report)
        if not direction:
            return
        options["cashflow_direction"] = direction

    def _custom_line_postprocessor(self, report, options, lines):
        lines = super()._custom_line_postprocessor(report, options, lines)
        direction = options.get("cashflow_direction") or self._cashflow_direction(report)
        if not direction or not self._cashflow_user_can_manage(direction):
            return lines
        for line in lines:
            # Aged reports use composite line identifiers.  Asking the report
            # to resolve the res.partner segment is reliable for both the
            # receivable and payable variants, while _get_model_info_from_id
            # can return the report segment instead of the partner segment.
            res_ids = report._get_res_ids_from_line_id(
                line["id"], ["account.report", "res.partner"]
            )
            partner_id = res_ids.get("res.partner")
            if partner_id:
                line["cashflow_partner_id"] = partner_id
                line["cashflow_direction"] = direction
        return lines

    def _cashflow_direction(self, report):
        receivable = self.env.ref(
            "account_reports.aged_receivable_report", raise_if_not_found=False
        )
        payable = self.env.ref(
            "account_reports.aged_payable_report", raise_if_not_found=False
        )
        if receivable and report.id == receivable.id:
            return "receivable"
        if payable and report.id == payable.id:
            return "payable"
        return False

    def _cashflow_user_can_manage(self, direction):
        if self.env.user.has_group("megatk_cash_flow_forecast.group_cashflow_user"):
            return True
        return direction == "receivable" and self.env.user.has_group(
            "megatk_cash_flow_forecast.group_cashflow_collections"
        )

    def _report_custom_engine_cashflow_receivable(
        self, expressions, options, date_scope, current_groupby, next_groupby,
        offset=0, limit=None, warnings=None,
    ):
        return self._cashflow_week_engine_result(
            "receivable", current_groupby, offset=offset, limit=limit
        )

    def _report_custom_engine_cashflow_payable(
        self, expressions, options, date_scope, current_groupby, next_groupby,
        offset=0, limit=None, warnings=None,
    ):
        return self._cashflow_week_engine_result(
            "payable", current_groupby, offset=offset, limit=limit
        )

    def _cashflow_week_amounts(self, direction):
        amounts = defaultdict(lambda: defaultdict(float))
        promises = self.env.get["cashflow.promise"].sudo().search([
            ("company_id", "in", self.env.companies.ids),
            ("direction", "=", direction),
            ("state", "=", "active"),
        ])
        for promise in promises:
            partner_id = promise.commercial_partner_id.id
            amounts[partner_id][promise.period] += promise.company_amount
        return amounts

    def _cashflow_week_engine_result(self, direction, current_groupby, offset=0, limit=None):
        amounts = self._cashflow_week_amounts(direction)
        if not current_groupby:
            return {
                expression: sum(item[period] for item in amounts.values())
                for period, expression in WEEK_EXPRESSIONS.items()
            }
        if current_groupby != "partner_id":
            return []
        partner_rows = sorted(amounts.items())
        if offset:
            partner_rows = partner_rows[offset:]
        if limit:
            partner_rows = partner_rows[:limit]
        return [
            (
                partner_id,
                {
                    expression: partner_amounts.get(period, 0.0)
                    for period, expression in WEEK_EXPRESSIONS.items()
                },
            )
            for partner_id, partner_amounts in partner_rows
        ]


class AccountAgedReceivableReportHandler(models.AbstractModel):
    _inherit = "account.aged.receivable.report.handler"

    def _custom_unfold_all_batch_data_generator(self, report, options, lines_to_expand_by_function):
        # The standard batch optimization only knows the native ageing
        # expressions.  Returning an empty batch lets Odoo evaluate the added
        # cash-flow week expressions through the custom engine above.
        return {}


class AccountAgedPayableReportHandler(models.AbstractModel):
    _inherit = "account.aged.payable.report.handler"

    def _custom_unfold_all_batch_data_generator(self, report, options, lines_to_expand_by_function):
        return {}
self.env.get["cashflow.promise"]self.env["cashflow.promise"]"asset_receivable if direction == "receivable" else "liability_payable""asset_receivable" if direction == "receivable" else "liability_payable"

class CashflowPortfolioSnapshot(models.Model):
    _inherit = "cashflow.portfolio.snapshot"

    @api.model
    def action_from_aged_report(self, partner_id, direction, action_name):
        if direction not in ("receivable", "payable"):
            raise UserError(_("El tipo de cartera solicitado no es válido."))
        if action_name not in ("documents", "schedule", "management", "history"):
            raise UserError(_("La acción solicitada no es válida."))
        is_cashflow_user = self.env.user.has_group(
            "megatk_cash_flow_forecast.group_cashflow_user"
        )
        is_collections = self.env.user.has_group(
            "megatk_cash_flow_forecast.group_cashflow_collections"
        )
        if not is_cashflow_user and not (direction == "receivable" and is_collections):
            raise AccessError(_("No tiene permisos para gestionar esta cartera."))
        partner = self.env["res.partner"].browse(partner_id).exists().commercial_partner_id
        if not partner:
            raise UserError(_("No fue posible identificar el cliente o proveedor."))
        company = self.env.company
        if action_name == "documents":
            return self._cashflow_open_partner_documents(company, partner, direction)
        if action_name == "schedule":
            return self._cashflow_schedule_partner(company, partner, direction)
        if action_name == "management":
            return self._cashflow_register_partner_management(company, partner, direction)
        return self._cashflow_open_partner_history(company, partner, direction)

    def _cashflow_open_partner_documents(self, company, partner, direction):
        account_type = (
            "asset_receivable" if direction == "receivable" else "liability_payable"
        )
        move_ids = self.env["account.move.line"].search([
            ("company_id", "=", company.id),
            ("parent_state", "=", "posted"),
            ("partner_id", "child_of", partner.id),
            ("account_id.account_type", "=", account_type),
            ("amount_residual", "!=", 0),
        ]).mapped("move_id").ids
        return {
            "type": "ir.actions.act_window",
            "name": _("Documentos abiertos · %s") % partner.display_name,
            "res_model": "account.move",
            "view_mode": "list,form",
            "views": [(False, "list"), (False, "form")],
            "domain": [("id", "in", move_ids)],
        }

    def _cashflow_schedule_partner(self, company, partner, direction):
        plan = self.env["cashflow.plan"].with_company(company).get_or_create_current_plan()
        classification = self.env["cashflow.portfolio.classification"].search([
            ("company_id", "=", company.id),
            ("partner_id", "=", partner.id),
            ("direction", "=", direction),
        ], limit=1)
        account_type = (
            "asset_receivable if direction == "receivable" else "liability_payable"
        )
        lines = self.env["account.move.line"].search([
            ("company_id", "=", company.id),
            ("parent_state", "=", "posted"),
            ("partner_id", "child_of", partner.id),
            ("account_id.account_type", "=", account_type),
            ("amount_residual", "!=", 0),
        ])
        signed_balance = sum(lines.mapped("amount_residual"))
        open_balance = signed_balance if direction == "receivable" else -signed_balance
        currencies = lines.mapped("currency_id")
        projection_currency = (
            currencies if len(currencies) == 1 else company.currency_id
        )
        default_amount = company.currency_id._convert(
            max(open_balance, 0.0), projection_currency, company,
            fields.Date.context_today(self),
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Programar cobro") if direction == "receivable" else _("Programar pago"),
            "res_model": "cashflow.promise",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "new",
            "context": {
                "default_plan_id": plan.id,
                "default_company_id": company.id,
                "default_partner_id": partner.id,
                "default_direction": direction,
                "default_classification_id": classification.id or False,
                "default_period": "week_1",
                "default_currency_id": projection_currency.id,
                "default_rate_date": fields.Date.context_today(self),
                "default_amount": default_amount,
            },
        }

    def _cashflow_register_partner_management(self, company, partner, direction):
        return {
            "type": "ir.actions.act_window",
            "name": _("Registrar gestión de cobro")
            if direction == "receivable" else _("Registrar gestión de pago"),
            "res_model": "cashflow.management.note",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "new",
            "context": {
                "default_company_id": company.id,
                "default_partner_id": partner.id,
                "default_direction": direction,
            },
        }

    def _cashflow_open_partner_history(self, company, partner, direction):
        return {
            "type": "ir.actions.act_window",
            "name": _("Historial de gestiones · %s") % partner.display_name,
            "res_model": "cashflow.management.note",
            "view_mode": "list,form",
            "views": [(False, "list"), (False, "form")],
            "domain": [
                ("company_id", "=", company.id),
                ("partner_id", "=", partner.id),
                ("direction", "=", direction),
            ],
            "context": {
                "default_company_id": company.id,
                "default_partner_id": partner.id,
                "default_direction": direction,
            },
        }
