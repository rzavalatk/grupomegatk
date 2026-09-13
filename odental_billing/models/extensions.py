from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ODentalOrganization(models.Model):
    _inherit = "odental.organization"

    require_hn_fiscal_control = fields.Boolean(
        string="Exigir control fiscal SAR",
        default=lambda self: self.env.company.country_id.code == "HN",
        help="Impide publicar facturas clínicas sin CAI, rango y vigencia válidos.",
    )

class ODentalTreatmentPlan(models.Model):
    _inherit = "odental.treatment.plan"

    billing_site_id = fields.Many2one(
        "odental.site", string="Sede de emisión", ondelete="restrict", tracking=True
    )
    invoice_id = fields.Many2one(
        "account.move", string="Factura", readonly=True, copy=False, ondelete="restrict"
    )

    @api.onchange("organization_id")
    def _onchange_billing_site(self):
        for plan in self:
            if not plan.organization_id or plan.billing_site_id:
                continue
            sites = plan.organization_id.site_ids | plan.organization_id.shared_site_ids
            if len(sites) == 1:
                plan.billing_site_id = sites

    @api.constrains("billing_site_id", "organization_id")
    def _check_billing_site(self):
        for plan in self.filtered("billing_site_id"):
            if not plan.billing_site_id.is_available_to(plan.organization_id):
                raise ValidationError("La sede de emisión no está disponible para la organización.")

    def write(self, vals):
        if (
            not self.env.context.get("allow_billing_link")
            and {"billing_site_id", "invoice_id"}.intersection(vals)
            and any(plan._is_commercially_frozen() for plan in self)
        ):
            raise UserError("La sede y la factura de un plan aprobado no pueden alterarse manualmente.")
        return super().write(vals)

    def action_create_invoice(self):
        self.ensure_one()
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError("Solo un administrador clínico puede crear la factura.")
        if self.state not in {"approved", "in_progress", "completed"}:
            raise UserError("El plan debe estar aprobado antes de facturarse.")
        if self.invoice_id:
            return self.action_view_invoice()
        if self.organization_id.require_hn_fiscal_control and not self.billing_site_id:
            raise ValidationError("Seleccione la sede de emisión antes de crear la factura.")
        active_lines = self.line_ids.filtered(lambda line: line.state != "cancelled")
        if not active_lines:
            raise ValidationError("El plan no contiene procedimientos facturables activos.")
        if active_lines.filtered(lambda line: not line.service_id.product_id):
            raise ValidationError("Todos los servicios deben tener un producto facturable.")
        partner = self._ensure_invoice_partner()
        journal = self.env["account.journal"].with_company(self.billing_company_id).search(
            [("type", "=", "sale"), ("company_id", "=", self.billing_company_id.id)],
            limit=1,
        )
        if not journal:
            raise ValidationError("Configure un diario de ventas para la compañía que factura.")
        line_commands = []
        for line in active_lines:
            product = line.service_id.product_id
            accounts = product.product_tmpl_id._get_product_accounts()
            income_account = accounts.get("income")
            if not income_account:
                raise ValidationError(
                    f"Configure una cuenta de ingresos para el servicio {line.service_id.name}."
                )
            line_commands.append(
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "name": line.description,
                        "quantity": line.quantity,
                        "price_unit": line.price_unit,
                        "discount": line.discount,
                        "tax_ids": [(6, 0, line.tax_ids.ids)],
                        "account_id": income_account.id,
                        "odental_treatment_line_id": line.id,
                    },
                )
            )
        authorization = self.env["odental.fiscal.authorization"]
        if self.billing_site_id:
            authorization = authorization.search(
                [
                    ("organization_id", "=", self.organization_id.id),
                    ("company_id", "=", self.billing_company_id.id),
                    ("site_id", "=", self.billing_site_id.id),
                    ("journal_id", "=", journal.id),
                    ("document_type", "=", "01"),
                    ("state", "=", "active"),
                ],
                limit=1,
            )
        invoice = self.env["account.move"].with_company(self.billing_company_id).create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "company_id": self.billing_company_id.id,
                "journal_id": journal.id,
                "invoice_origin": self.name,
                "ref": self.name,
                "odental_is_clinical": True,
                "odental_treatment_plan_id": self.id,
                "odental_patient_id": self.patient_id.id,
                "odental_organization_id": self.organization_id.id,
                "odental_site_id": self.billing_site_id.id,
                "odental_fiscal_authorization_id": authorization.id,
                "invoice_line_ids": line_commands,
            }
        )
        self.with_context(allow_treatment_transition=True, allow_billing_link=True).write(
            {"invoice_id": invoice.id}
        )
        self.clinical_record_id._log_event(
            "invoice_draft_created",
            f"Factura borrador {invoice.name} creada desde {self.name}",
            source_record=self,
        )
        return self.action_view_invoice()

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError("Este plan todavía no posee una factura.")
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.invoice_id.id,
            "view_mode": "form",
            "target": "current",
        }


class AccountMove(models.Model):
    _inherit = "account.move"

    odental_is_clinical = fields.Boolean(string="Factura clínica O Dental", copy=False)
    odental_treatment_plan_id = fields.Many2one(
        "odental.treatment.plan", readonly=True, copy=False, index=True
    )
    odental_patient_id = fields.Many2one("odental.patient", readonly=True, copy=False, index=True)
    odental_organization_id = fields.Many2one(
        "odental.organization", readonly=True, copy=False, index=True
    )
    odental_site_id = fields.Many2one("odental.site", string="Sede de emisión", copy=False)
    odental_fiscal_authorization_id = fields.Many2one(
        "odental.fiscal.authorization",
        string="Autorización SAR",
        copy=False,
        domain="[('company_id', '=', company_id), ('journal_id', '=', journal_id), ('state', '=', 'active')]",
    )
    odental_fiscal_number = fields.Char(string="Número fiscal", readonly=True, copy=False, index=True)
    odental_cai = fields.Char(string="CAI emitido", readonly=True, copy=False)
    odental_fiscal_date_limit = fields.Date(
        string="Fecha límite fiscal", readonly=True, copy=False
    )
    odental_fiscal_range = fields.Char(string="Rango autorizado", readonly=True, copy=False)

    _sql_constraints = [
        (
            "odental_fiscal_number_company_unique",
            "unique(company_id, odental_fiscal_number)",
            "El número fiscal ya fue utilizado por esta compañía.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves.filtered("odental_treatment_plan_id"):
            plan = move.odental_treatment_plan_id
            if move.move_type == "out_invoice" and not plan.invoice_id:
                plan.with_context(
                    allow_treatment_transition=True, allow_billing_link=True
                ).write({"invoice_id": move.id})
        return moves

    @api.constrains(
        "odental_fiscal_authorization_id", "company_id", "journal_id", "move_type", "odental_site_id"
    )
    def _check_odental_authorization_scope(self):
        for move in self.filtered("odental_fiscal_authorization_id"):
            authorization = move.odental_fiscal_authorization_id
            expected_type = "01" if move.move_type == "out_invoice" else "07"
            if authorization.company_id != move.company_id:
                raise ValidationError("La autorización fiscal pertenece a otra compañía.")
            if authorization.journal_id != move.journal_id:
                raise ValidationError("La autorización fiscal pertenece a otro diario.")
            if move.move_type in {"out_invoice", "out_refund"} and authorization.document_type != expected_type:
                raise ValidationError("La autorización fiscal no corresponde al tipo de documento.")
            if move.odental_site_id and authorization.site_id != move.odental_site_id:
                raise ValidationError("La autorización fiscal pertenece a otra sede.")

    def write(self, vals):
        fiscal_snapshots = {
            "odental_fiscal_number",
            "odental_cai",
            "odental_fiscal_date_limit",
            "odental_fiscal_range",
        }
        if not self.env.context.get("allow_odental_fiscal_allocation"):
            if fiscal_snapshots.intersection(vals):
                raise UserError("Los datos fiscales emitidos no pueden editarse manualmente.")
            if "odental_fiscal_authorization_id" in vals and any(
                move.state == "posted" for move in self
            ):
                raise UserError("La autorización fiscal de una factura publicada es inmutable.")
        return super().write(vals)

    def action_post(self):
        for move in self.filtered(
            lambda item: item.odental_is_clinical
            and item.move_type in {"out_invoice", "out_refund"}
            and not item.odental_fiscal_number
        ):
            organization = move.odental_organization_id
            if organization.require_hn_fiscal_control:
                authorization = move.odental_fiscal_authorization_id
                if not authorization:
                    raise ValidationError(
                        "Seleccione una autorización SAR activa antes de publicar la factura."
                    )
                fiscal_number = authorization._allocate_number(move.invoice_date)
                move.with_context(allow_odental_fiscal_allocation=True).write(
                    {
                        "odental_fiscal_number": fiscal_number,
                        "odental_cai": authorization.cai,
                        "odental_fiscal_date_limit": authorization.date_limit,
                        "odental_fiscal_range": authorization.range_display,
                    }
                )
        return super().action_post()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    odental_treatment_line_id = fields.Many2one(
        "odental.treatment.plan.line", readonly=True, copy=False, index=True
    )


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        values = super()._prepare_invoice()
        if self.odental_treatment_plan_id:
            plan = self.odental_treatment_plan_id
            values.update(
                {
                    "odental_is_clinical": True,
                    "odental_treatment_plan_id": plan.id,
                    "odental_patient_id": plan.patient_id.id,
                    "odental_organization_id": plan.organization_id.id,
                    "odental_site_id": plan.billing_site_id.id,
                }
            )
        return values


class AccountPayment(models.Model):
    _inherit = "account.payment"

    odental_collection_id = fields.Many2one(
        "odental.clinical.collection", readonly=True, copy=False, index=True
    )


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    odental_collection_id = fields.Many2one("odental.clinical.collection", readonly=True)

    def _create_payments(self):
        payments = super()._create_payments()
        collection = self.odental_collection_id
        if collection:
            if len(payments) != 1:
                raise ValidationError("El cobro clínico debe producir un único pago contable.")
            if payments.currency_id != collection.currency_id or not collection.currency_id.is_zero(
                payments.amount - collection.amount
            ):
                raise ValidationError(
                    "El pago contable debe conservar la moneda y el importe del cobro clínico."
                )
            if payments.journal_id != collection.journal_id:
                raise ValidationError("El pago contable debe utilizar el diario elegido en caja.")
            payments.odental_collection_id = collection.id
            collection._link_payment(payments)
        return payments
