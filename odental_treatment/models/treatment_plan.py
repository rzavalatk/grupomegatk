import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ODentalTreatmentPlan(models.Model):
    _name = "odental.treatment.plan"
    _description = "Plan de tratamiento O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    clinical_record_id = fields.Many2one(
        "odental.clinical.record",
        string="Expediente clínico",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
    )
    patient_id = fields.Many2one(
        related="clinical_record_id.patient_id", store=True, index=True
    )
    organization_id = fields.Many2one(
        related="clinical_record_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(
        related="organization_id.company_id", store=True, index=True
    )
    responsible_professional_id = fields.Many2one(
        "odental.professional",
        string="Profesional responsable",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
    )
    billing_mode = fields.Selection(
        [
            ("centralized", "Facturación centralizada"),
            ("independent", "Facturación independiente"),
        ],
        string="Modalidad de facturación",
        required=True,
        default="centralized",
        tracking=True,
    )
    billing_company_id = fields.Many2one(
        "res.company",
        string="Compañía que factura",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    currency_id = fields.Many2one(
        related="billing_company_id.currency_id", store=True, readonly=True
    )
    line_ids = fields.One2many(
        "odental.treatment.plan.line", "plan_id", string="Procedimientos", copy=True
    )
    amount_untaxed = fields.Monetary(
        string="Subtotal", compute="_compute_amounts", store=True
    )
    amount_tax = fields.Monetary(
        string="Impuestos", compute="_compute_amounts", store=True
    )
    amount_total = fields.Monetary(
        string="Total", compute="_compute_amounts", store=True, tracking=True
    )
    progress = fields.Float(
        string="Avance (%)", compute="_compute_progress", store=True
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("offered", "Presentado"),
            ("approved", "Aprobado"),
            ("rejected", "Rechazado"),
            ("in_progress", "En tratamiento"),
            ("completed", "Completado"),
            ("cancelled", "Cancelado"),
            ("superseded", "Sustituido"),
        ],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )
    valid_until = fields.Date(string="Válido hasta", tracking=True)
    terms = fields.Text(string="Condiciones")
    clinical_notes = fields.Text(string="Notas clínicas")
    signer_name = fields.Char(string="Nombre del aceptante", copy=False)
    acceptance_method = fields.Selection(
        [
            ("in_person", "Presencial"),
            ("email_otp", "Código por correo"),
            ("whatsapp_otp", "Código por WhatsApp"),
            ("secure_portal", "Portal seguro"),
            ("paper", "Documento en papel"),
        ],
        string="Método de aceptación",
        copy=False,
    )
    acceptance_reference = fields.Char(
        string="Referencia de verificación",
        copy=False,
        help="Identificador del evento de validación; nunca almacene aquí el código secreto.",
    )
    signature = fields.Binary(string="Firma o evidencia", attachment=True, copy=False)
    signature_filename = fields.Char(copy=False)
    accepted_at = fields.Datetime(string="Aceptado el", readonly=True, copy=False)
    accepted_by_user_id = fields.Many2one(
        "res.users", string="Registrado por", readonly=True, copy=False
    )
    content_hash = fields.Char(
        string="Huella digital", readonly=True, copy=False, index=True
    )
    rejection_reason = fields.Text(string="Motivo de rechazo", copy=False)
    cancellation_reason = fields.Text(string="Motivo de cancelación", copy=False)
    version = fields.Integer(required=True, default=1, readonly=True, copy=False)
    previous_version_id = fields.Many2one(
        "odental.treatment.plan",
        string="Versión anterior",
        readonly=True,
        copy=False,
        ondelete="restrict",
    )
    revision_ids = fields.One2many(
        "odental.treatment.plan", "previous_version_id", string="Revisiones"
    )
    revision_reason = fields.Text(string="Motivo de revisión", copy=False)
    sale_order_id = fields.Many2one(
        "sale.order", string="Cotización", readonly=True, copy=False, ondelete="restrict"
    )

    @api.depends("line_ids.price_subtotal", "line_ids.price_tax", "line_ids.price_total")
    def _compute_amounts(self):
        for plan in self:
            plan.amount_untaxed = sum(plan.line_ids.mapped("price_subtotal"))
            plan.amount_tax = sum(plan.line_ids.mapped("price_tax"))
            plan.amount_total = sum(plan.line_ids.mapped("price_total"))

    @api.depends("line_ids.state")
    def _compute_progress(self):
        for plan in self:
            active_lines = plan.line_ids.filtered(lambda line: line.state != "cancelled")
            completed = active_lines.filtered(lambda line: line.state == "completed")
            plan.progress = 100.0 * len(completed) / len(active_lines) if active_lines else 0.0

    @api.onchange("clinical_record_id", "responsible_professional_id")
    def _onchange_billing_defaults(self):
        for plan in self:
            organization = plan.clinical_record_id.organization_id
            if not organization:
                continue
            if organization.billing_mode == "independent":
                plan.billing_mode = "independent"
                plan.billing_company_id = plan.responsible_professional_id.billing_company_id
            else:
                plan.billing_mode = "centralized"
                plan.billing_company_id = organization.company_id

    @api.onchange("billing_mode", "responsible_professional_id")
    def _onchange_billing_mode(self):
        for plan in self:
            if not plan.organization_id:
                continue
            if plan.billing_mode == "centralized":
                plan.billing_company_id = plan.organization_id.company_id
            else:
                plan.billing_company_id = plan.responsible_professional_id.billing_company_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.treatment.plan"
                ) or "Nuevo"
            record = self.env["odental.clinical.record"].browse(
                vals.get("clinical_record_id")
            )
            professional = self.env["odental.professional"].browse(
                vals.get("responsible_professional_id")
            )
            if record and "billing_mode" not in vals:
                vals["billing_mode"] = (
                    "independent"
                    if record.organization_id.billing_mode == "independent"
                    else "centralized"
                )
            if record and "billing_company_id" not in vals:
                if vals.get("billing_mode") == "independent" and professional:
                    vals["billing_company_id"] = professional.billing_company_id.id
                else:
                    vals["billing_company_id"] = record.organization_id.company_id.id
        plans = super().create(vals_list)
        for plan in plans:
            plan.clinical_record_id._log_event(
                "treatment_created",
                f"Plan de tratamiento creado: {plan.name}",
                source_record=plan,
            )
        return plans

    @api.constrains(
        "clinical_record_id",
        "responsible_professional_id",
        "billing_mode",
        "billing_company_id",
    )
    def _check_organization_and_billing(self):
        for plan in self:
            organization = plan.organization_id
            if organization not in plan.responsible_professional_id.organization_ids:
                raise ValidationError(
                    "El profesional responsable no pertenece a la organización del expediente."
                )
            if organization.billing_mode != "mixed" and plan.billing_mode != organization.billing_mode:
                raise ValidationError(
                    "La modalidad seleccionada no está habilitada para esta organización."
                )
            expected_company = (
                organization.company_id
                if plan.billing_mode == "centralized"
                else plan.responsible_professional_id.billing_company_id
            )
            if not expected_company:
                raise ValidationError(
                    "Configure la compañía de facturación independiente del profesional."
                )
            if plan.billing_company_id != expected_company:
                raise ValidationError(
                    "La compañía que factura no corresponde a la modalidad seleccionada."
                )

    def _hash_payload(self):
        self.ensure_one()
        signature_bytes = self.signature or b""
        if isinstance(signature_bytes, str):
            signature_bytes = signature_bytes.encode("ascii")
        payload = {
            "plan": self.name,
            "version": self.version,
            "record": self.clinical_record_id.id,
            "patient": self.patient_id.id,
            "professional": self.responsible_professional_id.id,
            "billing_mode": self.billing_mode,
            "billing_company": self.billing_company_id.id,
            "currency": self.currency_id.name,
            "valid_until": fields.Date.to_string(self.valid_until) if self.valid_until else "",
            "terms": self.terms or "",
            "clinical_notes": self.clinical_notes or "",
            "signer_name": self.signer_name or "",
            "acceptance_method": self.acceptance_method or "",
            "acceptance_reference": self.acceptance_reference or "",
            "signature_hash": (
                hashlib.sha256(signature_bytes).hexdigest() if signature_bytes else ""
            ),
            "lines": [line._snapshot_values() for line in self.line_ids.sorted("sequence")],
        }
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def _is_commercially_frozen(self):
        self.ensure_one()
        return self.state in {
            "approved",
            "in_progress",
            "completed",
            "cancelled",
            "superseded",
        }

    def write(self, vals):
        protected_fields = {
            "clinical_record_id",
            "responsible_professional_id",
            "billing_mode",
            "billing_company_id",
            "line_ids",
            "valid_until",
            "terms",
            "clinical_notes",
            "signer_name",
            "acceptance_method",
            "acceptance_reference",
            "signature",
            "signature_filename",
            "version",
            "previous_version_id",
            "accepted_at",
            "accepted_by_user_id",
            "content_hash",
            "sale_order_id",
        }
        if not self.env.context.get("allow_treatment_transition"):
            if "state" in vals:
                raise UserError("Utilice las acciones del plan para cambiar su estado.")
            for plan in self:
                if plan._is_commercially_frozen() and protected_fields.intersection(vals):
                    raise UserError(
                        "Un plan aprobado no puede alterarse. Cree una nueva revisión."
                    )
        return super().write(vals)

    def unlink(self):
        if any(plan.state not in {"draft", "rejected"} for plan in self):
            raise UserError("Solo se pueden eliminar planes en borrador o rechazados.")
        return super().unlink()

    def _validate_ready(self):
        self.ensure_one()
        if not self.line_ids:
            raise ValidationError("Agregue al menos un procedimiento al plan.")
        if self.valid_until and self.valid_until < fields.Date.context_today(self):
            raise ValidationError("La vigencia del plan no puede estar vencida.")
        if self.amount_total < 0:
            raise ValidationError("El total del plan no puede ser negativo.")

    def action_offer(self):
        for plan in self:
            if plan.state not in {"draft", "rejected"}:
                raise UserError("Solo un borrador o plan rechazado puede presentarse.")
            plan._validate_ready()
            plan.with_context(allow_treatment_transition=True).write(
                {"state": "offered", "rejection_reason": False}
            )
            plan.clinical_record_id._log_event(
                "treatment_offered",
                f"Plan presentado al paciente: {plan.name}",
                source_record=plan,
            )

    def action_approve(self):
        for plan in self:
            if plan.state != "offered":
                raise UserError("Solo un plan presentado puede aprobarse.")
            plan._validate_ready()
            if not plan.signer_name or not plan.acceptance_method:
                raise ValidationError(
                    "Registre el nombre del aceptante y el método de aceptación."
                )
            if not plan.acceptance_reference and not plan.signature:
                raise ValidationError(
                    "Registre una referencia de verificación o adjunte la evidencia firmada."
                )
            content_hash = plan._hash_payload()
            plan.with_context(allow_treatment_transition=True).write(
                {
                    "state": "approved",
                    "accepted_at": fields.Datetime.now(),
                    "accepted_by_user_id": self.env.user.id,
                    "content_hash": content_hash,
                }
            )
            plan.clinical_record_id._log_event(
                "treatment_approved",
                f"Plan aprobado: {plan.name}, versión {plan.version}",
                content_hash,
                source_record=plan,
            )

    def action_reject(self):
        for plan in self:
            if plan.state != "offered":
                raise UserError("Solo un plan presentado puede rechazarse.")
            if not plan.rejection_reason:
                raise ValidationError("Indique el motivo del rechazo.")
            plan.with_context(allow_treatment_transition=True).write({"state": "rejected"})
            plan.clinical_record_id._log_event(
                "treatment_rejected",
                f"Plan rechazado: {plan.name}",
                source_record=plan,
            )

    def action_start(self):
        for plan in self:
            if plan.state != "approved":
                raise UserError("Solo un plan aprobado puede iniciar tratamiento.")
            plan.with_context(allow_treatment_transition=True).write(
                {"state": "in_progress"}
            )
            plan.clinical_record_id._log_event(
                "treatment_started",
                f"Tratamiento iniciado: {plan.name}",
                source_record=plan,
            )

    def action_complete(self):
        for plan in self:
            if plan.state != "in_progress":
                raise UserError("Solo un tratamiento en curso puede completarse.")
            pending = plan.line_ids.filtered(
                lambda line: line.state not in {"completed", "cancelled"}
            )
            if pending:
                raise ValidationError(
                    "Complete o cancele todos los procedimientos antes de cerrar el plan."
                )
            plan.with_context(allow_treatment_transition=True).write(
                {"state": "completed"}
            )
            plan.clinical_record_id._log_event(
                "treatment_completed",
                f"Tratamiento completado: {plan.name}",
                source_record=plan,
            )

    def action_cancel(self):
        for plan in self:
            if plan.state in {"completed", "cancelled", "superseded"}:
                raise UserError("Este plan ya no puede cancelarse.")
            if not plan.cancellation_reason:
                raise ValidationError("Indique el motivo de cancelación.")
            plan.with_context(allow_treatment_transition=True).write(
                {"state": "cancelled"}
            )
            plan.clinical_record_id._log_event(
                "treatment_cancelled",
                f"Plan cancelado: {plan.name}",
                source_record=plan,
            )

    def action_create_revision(self):
        self.ensure_one()
        if self.state not in {"approved", "in_progress"}:
            raise UserError("Solo un plan aprobado o en tratamiento puede revisarse.")
        if not self.revision_reason:
            raise ValidationError("Indique el motivo de la revisión.")
        revision = self.create(
            {
                "clinical_record_id": self.clinical_record_id.id,
                "responsible_professional_id": self.responsible_professional_id.id,
                "billing_mode": self.billing_mode,
                "billing_company_id": self.billing_company_id.id,
                "valid_until": self.valid_until,
                "terms": self.terms,
                "clinical_notes": self.clinical_notes,
                "version": self.version + 1,
                "previous_version_id": self.id,
                "revision_reason": self.revision_reason,
                "line_ids": [(0, 0, line._copy_values()) for line in self.line_ids],
            }
        )
        self.with_context(allow_treatment_transition=True).write({"state": "superseded"})
        self.clinical_record_id._log_event(
            "treatment_revised",
            f"Nueva revisión de {self.name}: versión {revision.version}",
            source_record=revision,
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "odental.treatment.plan",
            "res_id": revision.id,
            "view_mode": "form",
            "target": "current",
        }

    def _ensure_invoice_partner(self):
        self.ensure_one()
        patient = self.patient_id
        if patient.partner_id:
            return patient.partner_id
        partner = self.env["res.partner"].create(
            {
                "name": patient.name,
                "email": patient.email,
                "mobile": patient.mobile,
                "company_id": False,
            }
        )
        patient.partner_id = partner
        return partner

    def action_create_quotation(self):
        self.ensure_one()
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError(
                "Solo un administrador clínico puede convertir el plan en cotización."
            )
        if self.state not in {"approved", "in_progress", "completed"}:
            raise UserError("El plan debe estar aprobado antes de cotizarse.")
        if self.sale_order_id:
            return self.action_view_quotation()
        active_lines = self.line_ids.filtered(lambda line: line.state != "cancelled")
        if not active_lines:
            raise ValidationError("El plan no contiene procedimientos facturables activos.")
        missing_products = self.line_ids.filtered(lambda line: not line.service_id.product_id)
        if missing_products:
            raise ValidationError(
                "Todos los servicios deben tener un producto facturable configurado."
            )
        wrong_products = self.line_ids.filtered(
            lambda line: line.service_id.product_id.company_id
            and line.service_id.product_id.company_id != self.billing_company_id
        )
        if wrong_products:
            raise ValidationError(
                "Hay productos que no están disponibles para la compañía que factura."
            )
        wrong_taxes = self.line_ids.mapped("tax_ids").filtered(
            lambda tax: tax.company_id and tax.company_id != self.billing_company_id
        )
        if wrong_taxes:
            raise ValidationError(
                "Hay impuestos que pertenecen a una compañía de facturación diferente."
            )
        partner = self._ensure_invoice_partner()
        pricelist = self.env["product.pricelist"].with_company(
            self.billing_company_id
        ).search(
            [
                ("currency_id", "=", self.currency_id.id),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", self.billing_company_id.id),
            ],
            limit=1,
        )
        if not pricelist:
            raise ValidationError(
                "Configure una tarifa en la moneda de la compañía que facturará."
            )
        order_values = {
            "partner_id": partner.id,
            "company_id": self.billing_company_id.id,
            "pricelist_id": pricelist.id,
            "origin": self.name,
            "client_order_ref": self.name,
            "odental_treatment_plan_id": self.id,
            "order_line": [],
        }
        for line in active_lines:
            product = line.service_id.product_id
            order_values["order_line"].append(
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "name": line.description,
                        "product_uom_qty": line.quantity,
                        "product_uom": product.uom_id.id,
                        "price_unit": line.price_unit,
                        "discount": line.discount,
                        "tax_id": [(6, 0, line.tax_ids.ids)],
                        "odental_treatment_line_id": line.id,
                    },
                )
            )
        order = self.env["sale.order"].with_company(self.billing_company_id).create(
            order_values
        )
        self.with_context(allow_treatment_transition=True).write(
            {"sale_order_id": order.id}
        )
        self.clinical_record_id._log_event(
            "quotation_created",
            f"Cotización {order.name} creada desde {self.name}",
            source_record=self,
        )
        return self.action_view_quotation()

    def action_view_quotation(self):
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError("Este plan todavía no posee una cotización.")
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": self.sale_order_id.id,
            "view_mode": "form",
            "target": "current",
        }


class ODentalTreatmentPlanLine(models.Model):
    _name = "odental.treatment.plan.line"
    _description = "Procedimiento de plan de tratamiento O Dental"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    plan_id = fields.Many2one(
        "odental.treatment.plan", required=True, ondelete="cascade", index=True
    )
    organization_id = fields.Many2one(
        related="plan_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(
        related="plan_id.billing_company_id", store=True, index=True
    )
    currency_id = fields.Many2one(related="plan_id.currency_id", store=True)
    service_id = fields.Many2one(
        "odental.service", required=True, ondelete="restrict", index=True
    )
    tooth_id = fields.Many2one("odental.tooth", string="Pieza", ondelete="restrict")
    surface = fields.Selection(
        [
            ("mesial", "Mesial"),
            ("distal", "Distal"),
            ("vestibular", "Vestibular"),
            ("lingual", "Lingual/Palatina"),
            ("occlusal", "Oclusal/Incisal"),
            ("whole", "Pieza completa"),
        ],
        string="Superficie",
    )
    description = fields.Char(required=True)
    quantity = fields.Float(required=True, default=1.0)
    price_unit = fields.Monetary(required=True, default=0.0)
    discount = fields.Float(string="Descuento (%)", default=0.0)
    tax_ids = fields.Many2many("account.tax", string="Impuestos")
    price_subtotal = fields.Monetary(compute="_compute_amounts", store=True)
    price_tax = fields.Monetary(compute="_compute_amounts", store=True)
    price_total = fields.Monetary(compute="_compute_amounts", store=True)
    professional_id = fields.Many2one(
        "odental.professional", string="Profesional asignado", ondelete="restrict"
    )
    encounter_id = fields.Many2one(
        "odental.clinical.encounter", string="Evolución relacionada", ondelete="set null"
    )
    state = fields.Selection(
        [
            ("planned", "Planificado"),
            ("scheduled", "Programado"),
            ("in_progress", "En curso"),
            ("completed", "Completado"),
            ("cancelled", "Cancelado"),
        ],
        required=True,
        default="planned",
        index=True,
    )

    @api.depends(
        "quantity",
        "price_unit",
        "discount",
        "tax_ids",
        "currency_id",
        "service_id.product_id",
    )
    def _compute_amounts(self):
        for line in self:
            discounted_price = line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_ids.compute_all(
                discounted_price,
                currency=line.currency_id,
                quantity=line.quantity,
                product=line.service_id.product_id,
                partner=line.plan_id.patient_id.partner_id,
            )
            line.price_subtotal = taxes["total_excluded"]
            line.price_total = taxes["total_included"]
            line.price_tax = taxes["total_included"] - taxes["total_excluded"]

    @api.onchange("service_id")
    def _onchange_service_id(self):
        for line in self:
            if not line.service_id:
                continue
            line.description = line.service_id.name
            line.price_unit = line.service_id.price_unit
            product = line.service_id.product_id
            line.tax_ids = product.taxes_id if product else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            plan = self.env["odental.treatment.plan"].browse(vals.get("plan_id"))
            if plan and plan._is_commercially_frozen():
                raise UserError("No se pueden agregar procedimientos a un plan aprobado.")
            service = self.env["odental.service"].browse(vals.get("service_id"))
            if service:
                vals.setdefault("description", service.name)
                vals.setdefault("price_unit", service.price_unit)
                if "tax_ids" not in vals and service.product_id:
                    vals["tax_ids"] = [(6, 0, service.product_id.taxes_id.ids)]
                vals.setdefault("professional_id", plan.responsible_professional_id.id)
        return super().create(vals_list)

    @api.constrains(
        "plan_id",
        "service_id",
        "professional_id",
        "encounter_id",
        "quantity",
        "price_unit",
        "discount",
    )
    def _check_values(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError("La cantidad debe ser mayor que cero.")
            if line.price_unit < 0:
                raise ValidationError("El precio no puede ser negativo.")
            if line.discount < 0 or line.discount > 100:
                raise ValidationError("El descuento debe estar entre 0 y 100 por ciento.")
            if line.service_id.organization_id != line.organization_id:
                raise ValidationError("El servicio pertenece a otra organización.")
            if line.professional_id and line.organization_id not in line.professional_id.organization_ids:
                raise ValidationError("El profesional asignado pertenece a otra organización.")
            if line.encounter_id and line.encounter_id.clinical_record_id != line.plan_id.clinical_record_id:
                raise ValidationError("La evolución relacionada pertenece a otro expediente.")

    def write(self, vals):
        commercial_fields = {
            "plan_id",
            "sequence",
            "service_id",
            "tooth_id",
            "surface",
            "description",
            "quantity",
            "price_unit",
            "discount",
            "tax_ids",
            "professional_id",
        }
        for line in self:
            if line.plan_id._is_commercially_frozen() and commercial_fields.intersection(vals):
                raise UserError(
                    "Los procedimientos de un plan aprobado no pueden modificarse."
                )
        return super().write(vals)

    def unlink(self):
        if any(line.plan_id._is_commercially_frozen() for line in self):
            raise UserError("No se pueden eliminar procedimientos de un plan aprobado.")
        return super().unlink()

    def _snapshot_values(self):
        self.ensure_one()
        return {
            "sequence": self.sequence,
            "service": self.service_id.id,
            "product": self.service_id.product_id.id,
            "tooth": self.tooth_id.code or "",
            "surface": self.surface or "",
            "description": self.description,
            "quantity": self.quantity,
            "price_unit": self.price_unit,
            "discount": self.discount,
            "taxes": sorted(self.tax_ids.ids),
            "subtotal": self.price_subtotal,
            "tax": self.price_tax,
            "total": self.price_total,
            "professional": self.professional_id.id,
        }

    def _copy_values(self):
        self.ensure_one()
        return {
            "sequence": self.sequence,
            "service_id": self.service_id.id,
            "tooth_id": self.tooth_id.id,
            "surface": self.surface,
            "description": self.description,
            "quantity": self.quantity,
            "price_unit": self.price_unit,
            "discount": self.discount,
            "tax_ids": [(6, 0, self.tax_ids.ids)],
            "professional_id": self.professional_id.id,
            "state": "planned",
        }
