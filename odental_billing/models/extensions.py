from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ODentalClinicalAudit(models.Model):
    _inherit = "odental.clinical.audit"

    event_type = fields.Selection(
        selection_add=[
            ("invoice_draft_created", "Factura borrador creada"),
            ("payment_registered", "Cobro registrado"),
        ],
        ondelete={"invoice_draft_created": "cascade", "payment_registered": "cascade"},
    )


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

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get("invoice_id", self.env.context.get("default_invoice_id")) for vals in vals_list):
            raise UserError("La factura se vincula mediante las acciones del plan.")
        return super().create(vals_list)

    def write(self, vals):
        if "invoice_id" in vals:
            raise UserError("La factura se vincula mediante las acciones del plan.")
        if (
            {"billing_site_id"}.intersection(vals)
            and any(plan._is_commercially_frozen() for plan in self)
        ):
            raise UserError("La sede y la factura de un plan aprobado no pueden alterarse manualmente.")
        return super().write(vals)

    def _link_invoice(self, invoice):
        self.ensure_one()
        if (invoice.odental_treatment_plan_id != self or invoice.company_id != self.billing_company_id
            or invoice.odental_patient_id != self.patient_id or invoice.move_type != "out_invoice"):
            raise ValidationError("La factura no corresponde al plan y su compañía.")
        if self.invoice_id and self.invoice_id != invoice:
            raise UserError("El plan ya tiene una factura vinculada.")
        super(ODentalTreatmentPlan, self).write({"invoice_id": invoice.id})

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
        self._link_invoice(invoice)
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
        snapshots = {"odental_fiscal_number", "odental_cai", "odental_fiscal_date_limit", "odental_fiscal_range"}
        if any(vals.get(key, self.env.context.get("default_" + key)) for vals in vals_list for key in snapshots):
            raise UserError("Los datos fiscales se asignan al publicar la factura.")
        moves = super().create(vals_list)
        for move in moves.filtered("odental_treatment_plan_id"):
            plan = move.odental_treatment_plan_id
            if move.move_type == "out_invoice" and not plan.invoice_id:
                plan._link_invoice(move)
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
        if fiscal_snapshots.intersection(vals):
            raise UserError("Los datos fiscales emitidos no pueden editarse manualmente.")
        clinical_links = {"odental_is_clinical", "odental_treatment_plan_id", "odental_patient_id",
                          "odental_organization_id", "odental_site_id", "odental_fiscal_authorization_id"}
        if clinical_links.intersection(vals) and any(move.state == "posted" and move.odental_is_clinical for move in self):
            raise UserError("Las referencias clínicas de una factura publicada son inmutables.")
        return super().write(vals)

    def generate_tickets(self):
        # Optional compatibility with fields_megatk: clinical invoices and their
        # payment entries do not participate in retail raffles. No extra ACLs.
        for move in self:
            if move.odental_is_clinical or move.origin_payment_id.odental_collection_id:
                continue
            parent = getattr(super(AccountMove, move), "generate_tickets", None)
            if parent:
                parent()

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
                super(AccountMove, move).write(
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

    def write(self, vals):
        registered = self.filtered(lambda payment: payment.odental_collection_id.state == "registered")
        financial = {"amount", "currency_id", "company_id", "journal_id", "partner_id", "payment_type",
                     "partner_type", "odental_collection_id", "move_id"}
        if registered and (financial.intersection(vals) or vals.get("state") in {"draft", "canceled", "cancelled", "rejected"}):
            raise UserError("El pago pertenece a un cobro registrado. Requiere una rectificación contable supervisada.")
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda payment: payment.odental_collection_id.state == "registered"):
            raise UserError("No puede eliminar el pago de un cobro registrado.")
        return super().unlink()


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    odental_collection_id = fields.Many2one("odental.clinical.collection", readonly=True)

    def _create_payment_vals_from_wizard(self, batch_result):
        values = super()._create_payment_vals_from_wizard(batch_result)
        if self.odental_collection_id:
            values["odental_collection_id"] = self.odental_collection_id.id
        return values

    def _create_payment_vals_from_batch(self, batch_result):
        values = super()._create_payment_vals_from_batch(batch_result)
        if self.odental_collection_id:
            values["odental_collection_id"] = self.odental_collection_id.id
        return values

    def _create_payments(self):
        self.ensure_one()
        collection = self.odental_collection_id
        clinical_invoices = self.line_ids.move_id.filtered("odental_is_clinical")
        if clinical_invoices and not collection:
            raise UserError("Registre el pago desde Cobros clínicos para conservar la caja y sus autorizaciones.")
        if collection:
            if self.payment_difference_handling != "open":
                raise ValidationError("El saldo no pagado debe permanecer pendiente; no se permite cancelarlo como diferencia desde caja.")
            if collection.state != "draft":
                raise UserError("Este cobro ya fue procesado.")
            collection._check_scope()
            collection._check_partial_authorization()
            if self.line_ids.move_id != collection.invoice_id:
                raise ValidationError("El asistente de pago debe corresponder a la factura del cobro.")
            if self.currency_id != collection.currency_id or self.currency_id.compare_amounts(self.amount, collection.amount):
                raise ValidationError("El importe y la moneda deben coincidir con el cobro autorizado.")
            if self.journal_id != collection.journal_id:
                raise ValidationError("El diario debe coincidir con el cobro autorizado.")
        payments = super()._create_payments()
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
