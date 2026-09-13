from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ODentalPaymentAgreement(models.Model):
    _name = "odental.payment.agreement"
    _description = "Convenio de pago O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    patient_id = fields.Many2one(
        "odental.patient", required=True, ondelete="restrict", index=True, tracking=True
    )
    organization_id = fields.Many2one(
        related="patient_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía acreedora", required=True, ondelete="restrict", index=True
    )
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    invoice_ids = fields.Many2many(
        "account.move",
        "odental_agreement_invoice_rel",
        "agreement_id",
        "move_id",
        string="Facturas incluidas",
        domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial')), ('company_id', '=', company_id), ('odental_patient_id', '=', patient_id)]",
    )
    invoice_balance = fields.Monetary(
        string="Saldo actual de facturas", compute="_compute_invoice_balance"
    )
    down_payment = fields.Monetary(string="Prima acordada", default=0.0, tracking=True)
    down_payment_collection_id = fields.Many2one(
        "odental.clinical.collection", string="Cobro de la prima", ondelete="restrict", copy=False,
        domain="[('state', '=', 'registered'), ('patient_id', '=', patient_id), ('company_id', '=', company_id)]",
    )
    finance_charge_percent = fields.Float(
        string="Cargo financiero (%)", default=0.0, tracking=True
    )
    principal_amount = fields.Monetary(readonly=True, copy=False)
    financed_amount = fields.Monetary(readonly=True, copy=False)
    finance_charge_amount = fields.Monetary(readonly=True, copy=False)
    scheduled_amount = fields.Monetary(readonly=True, copy=False)
    installment_count = fields.Integer(string="Número de cuotas", default=1, required=True)
    frequency = fields.Selection(
        [("weekly", "Semanal"), ("biweekly", "Quincenal"), ("monthly", "Mensual")],
        required=True,
        default="monthly",
    )
    first_due_date = fields.Date(
        string="Primer vencimiento", required=True, default=fields.Date.context_today
    )
    line_ids = fields.One2many(
        "odental.payment.installment", "agreement_id", string="Cuotas", copy=False
    )
    amount_paid = fields.Monetary(compute="_compute_payment_totals", store=True)
    balance_amount = fields.Monetary(compute="_compute_payment_totals", store=True)
    signer_name = fields.Char(string="Aceptado por", copy=False)
    acceptance_reference = fields.Char(
        string="Referencia de aceptación", copy=False,
        help="Identificador verificable del consentimiento; no almacene códigos secretos.",
    )
    approved_at = fields.Datetime(readonly=True, copy=False)
    approved_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    cancellation_reason = fields.Text(copy=False)
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("proposed", "Propuesto"),
            ("approved", "Aprobado"),
            ("active", "Activo"),
            ("completed", "Completado"),
            ("defaulted", "En mora"),
            ("cancelled", "Cancelado"),
        ],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )

    @api.depends("invoice_ids.amount_residual")
    def _compute_invoice_balance(self):
        for agreement in self:
            agreement.invoice_balance = sum(agreement.invoice_ids.mapped("amount_residual"))

    @api.depends("scheduled_amount", "line_ids.amount_paid")
    def _compute_payment_totals(self):
        for agreement in self:
            agreement.amount_paid = sum(agreement.line_ids.mapped("amount_paid"))
            agreement.balance_amount = max(agreement.scheduled_amount - agreement.amount_paid, 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.payment.agreement"
                ) or "Nuevo"
        return super().create(vals_list)

    @api.constrains("company_id", "patient_id", "invoice_ids")
    def _check_scope(self):
        for agreement in self:
            organization = agreement.organization_id
            allowed_companies = organization.company_id | organization.mapped(
                "professional_ids.billing_company_id"
            )
            if agreement.company_id not in allowed_companies:
                raise ValidationError("La compañía acreedora no está habilitada para la organización.")
            invalid = agreement.invoice_ids.filtered(
                lambda move: move.company_id != agreement.company_id
                or move.odental_patient_id != agreement.patient_id
                or move.move_type != "out_invoice"
                or move.state != "posted"
                or move.currency_id != agreement.currency_id
            )
            if invalid:
                raise ValidationError(
                    "Todas las facturas deben estar publicadas, usar la moneda de la compañía y pertenecer al paciente."
                )
            collection = agreement.down_payment_collection_id
            if collection and (
                collection.state != "registered"
                or collection.patient_id != agreement.patient_id
                or collection.company_id != agreement.company_id
                or collection.amount < agreement.down_payment
            ):
                raise ValidationError("El cobro de la prima no corresponde al convenio o es insuficiente.")

    @api.constrains("down_payment", "finance_charge_percent", "installment_count")
    def _check_terms(self):
        for agreement in self:
            if agreement.down_payment < 0:
                raise ValidationError("La prima no puede ser negativa.")
            if not 0 <= agreement.finance_charge_percent <= 100:
                raise ValidationError("El cargo financiero debe estar entre 0 y 100 por ciento.")
            if agreement.installment_count < 1 or agreement.installment_count > 120:
                raise ValidationError("El convenio debe tener entre 1 y 120 cuotas.")

    def _split_amount(self, total, count):
        self.ensure_one()
        rounded = self.currency_id.round(total / count)
        amounts = [rounded] * max(count - 1, 0)
        amounts.append(total - sum(amounts))
        return amounts

    def _due_date(self, position):
        self.ensure_one()
        if self.frequency == "weekly":
            return self.first_due_date + relativedelta(weeks=position)
        if self.frequency == "biweekly":
            return self.first_due_date + relativedelta(days=15 * position)
        return self.first_due_date + relativedelta(months=position)

    def action_generate_schedule(self):
        for agreement in self:
            if agreement.state != "draft":
                raise UserError("Solo un convenio en borrador puede recalcularse.")
            if not agreement.invoice_ids:
                raise ValidationError("Seleccione al menos una factura pendiente.")
            principal = agreement.invoice_balance
            if principal <= 0:
                raise ValidationError("Las facturas seleccionadas no tienen saldo pendiente.")
            if agreement.down_payment > principal:
                raise ValidationError("La prima no puede superar el saldo de las facturas.")
            financed = principal - agreement.down_payment
            if agreement.currency_id.is_zero(financed):
                raise ValidationError("La prima cubre todo el saldo; no es necesario crear cuotas.")
            charge = agreement.currency_id.round(
                financed * agreement.finance_charge_percent / 100.0
            )
            scheduled = financed + charge
            amounts = agreement._split_amount(scheduled, agreement.installment_count)
            commands = [(5, 0, 0)]
            for index, amount in enumerate(amounts):
                commands.append(
                    (0, 0, {
                        "sequence": index + 1,
                        "due_date": agreement._due_date(index),
                        "amount_due": amount,
                    })
                )
            agreement.write({
                "principal_amount": principal,
                "financed_amount": financed,
                "finance_charge_amount": charge,
                "scheduled_amount": scheduled,
                "line_ids": commands,
            })

    def action_propose(self):
        for agreement in self:
            if agreement.state != "draft":
                raise UserError("Solo un borrador puede proponerse.")
            if not agreement.line_ids or agreement.scheduled_amount <= 0:
                raise ValidationError("Genere el calendario de cuotas antes de proponerlo.")
            duplicate = self.search_count([
                ("id", "!=", agreement.id),
                ("invoice_ids", "in", agreement.invoice_ids.ids),
                ("state", "in", ("proposed", "approved", "active", "defaulted")),
            ])
            if duplicate:
                raise ValidationError("Una factura seleccionada ya pertenece a otro convenio vigente.")
            agreement.with_context(allow_agreement_transition=True).write({"state": "proposed"})

    def action_approve(self):
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError("Solo un administrador clínico puede aprobar convenios.")
        for agreement in self:
            if agreement.state != "proposed":
                raise UserError("Solo un convenio propuesto puede aprobarse.")
            if not agreement.signer_name or not agreement.acceptance_reference:
                raise ValidationError("Registre el aceptante y la referencia verificable.")
            agreement.with_context(allow_agreement_transition=True).write({
                "state": "approved",
                "approved_at": fields.Datetime.now(),
                "approved_by_id": self.env.user.id,
            })

    def action_activate(self):
        for agreement in self:
            if agreement.state != "approved":
                raise UserError("Solo un convenio aprobado puede activarse.")
            if agreement.down_payment and not agreement.down_payment_collection_id:
                raise ValidationError("Vincule el cobro registrado de la prima antes de activar.")
            agreement.with_context(allow_agreement_transition=True).write({"state": "active"})

    def action_refresh_status(self):
        today = fields.Date.context_today(self)
        for agreement in self.filtered(lambda record: record.state in {"active", "defaulted"}):
            if agreement.currency_id.is_zero(agreement.balance_amount):
                new_state = "completed"
            elif agreement.line_ids.filtered(
                lambda line: line.due_date < today and line.balance_amount > 0
            ):
                new_state = "defaulted"
            else:
                new_state = "active"
            agreement.with_context(allow_agreement_transition=True).write({"state": new_state})

    def action_cancel(self):
        for agreement in self:
            if agreement.state in {"completed", "cancelled"}:
                raise UserError("Este convenio ya no puede cancelarse.")
            if agreement.amount_paid:
                raise ValidationError("Un convenio con abonos aplicados no puede cancelarse.")
            if not agreement.cancellation_reason:
                raise ValidationError("Indique el motivo de cancelación.")
            agreement.with_context(allow_agreement_transition=True).write({"state": "cancelled"})

    def write(self, vals):
        protected = {
            "patient_id", "company_id", "invoice_ids", "down_payment", "down_payment_collection_id",
            "finance_charge_percent", "installment_count", "frequency",
            "first_due_date", "principal_amount", "financed_amount",
            "finance_charge_amount", "scheduled_amount", "line_ids",
            "signer_name", "acceptance_reference",
        }
        if not self.env.context.get("allow_agreement_transition"):
            if "state" in vals:
                raise UserError("Utilice las acciones del convenio para cambiar su estado.")
            if protected.intersection(vals) and any(record.state != "draft" for record in self):
                raise UserError("Un convenio propuesto o aprobado no puede modificarse.")
        return super().write(vals)

    def unlink(self):
        if any(record.state != "draft" for record in self):
            raise UserError("Solo se pueden eliminar convenios en borrador.")
        return super().unlink()


class ODentalPaymentInstallment(models.Model):
    _name = "odental.payment.installment"
    _description = "Cuota de convenio O Dental"
    _order = "due_date, sequence, id"

    sequence = fields.Integer(required=True, default=1)
    agreement_id = fields.Many2one(
        "odental.payment.agreement", required=True, ondelete="cascade", index=True
    )
    organization_id = fields.Many2one(related="agreement_id.organization_id", store=True, index=True)
    company_id = fields.Many2one(related="agreement_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="agreement_id.currency_id", store=True)
    due_date = fields.Date(required=True, index=True)
    amount_due = fields.Monetary(required=True)
    allocation_ids = fields.One2many(
        "odental.installment.allocation", "installment_id", string="Abonos"
    )
    amount_paid = fields.Monetary(compute="_compute_amounts", store=True)
    balance_amount = fields.Monetary(compute="_compute_amounts", store=True)
    state = fields.Selection(
        [("pending", "Pendiente"), ("partial", "Parcial"), ("paid", "Pagada"), ("overdue", "Vencida")],
        compute="_compute_state",
    )

    @api.depends("amount_due", "allocation_ids.amount", "allocation_ids.collection_id.state")
    def _compute_amounts(self):
        for installment in self:
            valid = installment.allocation_ids.filtered(
                lambda allocation: allocation.collection_id.state == "registered"
            )
            installment.amount_paid = sum(valid.mapped("amount"))
            installment.balance_amount = max(installment.amount_due - installment.amount_paid, 0.0)

    @api.depends("amount_paid", "balance_amount", "due_date")
    def _compute_state(self):
        today = fields.Date.context_today(self)
        for installment in self:
            if installment.currency_id.is_zero(installment.balance_amount):
                installment.state = "paid"
            elif installment.amount_paid:
                installment.state = "partial"
            elif installment.due_date < today:
                installment.state = "overdue"
            else:
                installment.state = "pending"

    @api.constrains("amount_due")
    def _check_amount_due(self):
        for installment in self:
            if installment.amount_due <= 0:
                raise ValidationError("El importe de una cuota debe ser mayor que cero.")

    @api.model_create_multi
    def create(self, vals_list):
        agreements = self.env["odental.payment.agreement"].browse(
            [values.get("agreement_id") for values in vals_list if values.get("agreement_id")]
        )
        if any(agreement.state != "draft" for agreement in agreements):
            raise UserError("Solo puede crear cuotas mientras el convenio está en borrador.")
        return super().create(vals_list)

    def write(self, vals):
        protected = {"sequence", "agreement_id", "due_date", "amount_due"}
        if protected.intersection(vals) and any(
            installment.agreement_id.state != "draft" for installment in self
        ):
            raise UserError("Las cuotas de un convenio propuesto no pueden modificarse.")
        return super().write(vals)

    def unlink(self):
        if any(installment.agreement_id.state != "draft" for installment in self):
            raise UserError("Las cuotas de un convenio propuesto no pueden eliminarse.")
        return super().unlink()


class ODentalInstallmentAllocation(models.Model):
    _name = "odental.installment.allocation"
    _description = "Aplicación de abono O Dental"
    _order = "create_date desc, id desc"

    installment_id = fields.Many2one(
        "odental.payment.installment", required=True, ondelete="restrict", index=True
    )
    agreement_id = fields.Many2one(related="installment_id.agreement_id", store=True, index=True)
    organization_id = fields.Many2one(related="agreement_id.organization_id", store=True, index=True)
    company_id = fields.Many2one(related="agreement_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="agreement_id.currency_id", store=True)
    collection_id = fields.Many2one(
        "odental.clinical.collection", required=True, ondelete="restrict", index=True,
        domain="[('state', '=', 'registered'), ('company_id', '=', company_id)]",
    )
    amount = fields.Monetary(required=True)
    applied_by_id = fields.Many2one(
        "res.users", required=True, readonly=True, default=lambda self: self.env.user
    )
    applied_at = fields.Datetime(required=True, readonly=True, default=fields.Datetime.now)
    notes = fields.Char()

    @api.constrains("installment_id", "collection_id", "amount")
    def _check_allocation(self):
        for allocation in self:
            if allocation.amount <= 0:
                raise ValidationError("El abono debe ser mayor que cero.")
            if allocation.collection_id.state != "registered":
                raise ValidationError("Solo puede aplicar un cobro contablemente registrado.")
            agreement = allocation.agreement_id
            if allocation.collection_id.patient_id != agreement.patient_id:
                raise ValidationError("El cobro corresponde a otro paciente.")
            if allocation.collection_id.company_id != agreement.company_id:
                raise ValidationError("El cobro corresponde a otra compañía.")
            other_installment = sum(
                allocation.installment_id.allocation_ids.filtered(
                    lambda item: item.id != allocation.id and item.collection_id.state == "registered"
                ).mapped("amount")
            )
            if allocation.amount > allocation.installment_id.amount_due - other_installment:
                raise ValidationError("El abono supera el saldo de la cuota.")
            other_collection = self.search([
                ("id", "!=", allocation.id),
                ("collection_id", "=", allocation.collection_id.id),
            ])
            if allocation.amount + sum(other_collection.mapped("amount")) > allocation.collection_id.amount:
                raise ValidationError("La suma aplicada supera el importe del cobro.")

    def unlink(self):
        if any(record.agreement_id.state in {"completed", "cancelled"} for record in self):
            raise UserError("No puede retirar abonos de un convenio cerrado.")
        return super().unlink()
