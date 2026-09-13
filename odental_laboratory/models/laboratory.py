from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


LAB_EVENT_TYPES = [
    ("created", "Caso creado"), ("sent", "Enviado al laboratorio"),
    ("received", "Trabajo recibido"), ("fitting", "Prueba clínica"),
    ("rework", "Retrabajo solicitado"), ("accepted", "Trabajo aceptado"),
    ("cancelled", "Caso cancelado"), ("purchase", "Orden de compra creada"),
]


class ODentalLaboratory(models.Model):
    _name = "odental.laboratory"
    _description = "Laboratorio dental O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    organization_id = fields.Many2one("odental.organization", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    partner_id = fields.Many2one("res.partner", string="Proveedor", required=True, ondelete="restrict")
    email = fields.Char(related="partner_id.email", readonly=False)
    phone = fields.Char(related="partner_id.phone", readonly=False)
    default_turnaround_days = fields.Integer(string="Días de entrega habituales", default=7)
    notes = fields.Text()

    @api.constrains("default_turnaround_days")
    def _check_turnaround(self):
        if any(lab.default_turnaround_days < 0 for lab in self):
            raise ValidationError("Los días de entrega no pueden ser negativos.")


class ODentalLabCase(models.Model):
    _name = "odental.lab.case"
    _description = "Caso de laboratorio dental O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "requested_date desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    clinical_record_id = fields.Many2one("odental.clinical.record", required=True, ondelete="restrict", index=True)
    patient_id = fields.Many2one(related="clinical_record_id.patient_id", store=True, index=True)
    organization_id = fields.Many2one(related="clinical_record_id.organization_id", store=True, index=True)
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id", store=True)
    treatment_line_id = fields.Many2one("odental.treatment.plan.line", string="Procedimiento", ondelete="restrict")
    tooth_id = fields.Many2one("odental.tooth", string="Pieza dental", ondelete="restrict")
    laboratory_id = fields.Many2one("odental.laboratory", required=True, ondelete="restrict", tracking=True)
    responsible_professional_id = fields.Many2one(
        "odental.professional", string="Profesional responsable", required=True,
        ondelete="restrict", tracking=True
    )
    work_type = fields.Selection(
        [("crown", "Corona"), ("bridge", "Puente"), ("denture", "Prótesis"),
         ("inlay", "Inlay/Onlay"), ("veneer", "Carilla"), ("aligner", "Alineador"),
         ("splint", "Férula"), ("model", "Modelo"), ("other", "Otro")],
        required=True, tracking=True
    )
    shade = fields.Char(string="Color/tono")
    material = fields.Char(string="Material solicitado")
    instructions = fields.Text(required=True)
    requested_date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    sent_date = fields.Date(readonly=True, copy=False)
    expected_return_date = fields.Date(string="Entrega esperada", tracking=True)
    received_date = fields.Date(readonly=True, copy=False)
    accepted_date = fields.Date(readonly=True, copy=False)
    estimated_cost = fields.Monetary(currency_field="currency_id")
    actual_cost = fields.Monetary(currency_field="currency_id")
    purchase_product_id = fields.Many2one(
        "product.product", string="Servicio de laboratorio", domain="[('type', '=', 'service')]",
        ondelete="restrict", check_company=True
    )
    purchase_order_id = fields.Many2one("purchase.order", string="Orden de compra", readonly=True, copy=False)
    state = fields.Selection(
        [("draft", "Preparación"), ("sent", "En laboratorio"), ("received", "Recibido"),
         ("fitting", "Prueba clínica"), ("rework", "Retrabajo"),
         ("accepted", "Aceptado"), ("cancelled", "Cancelado")],
        required=True, default="draft", tracking=True, index=True
    )
    rework_count = fields.Integer(readonly=True, copy=False)
    rework_reason = fields.Text(copy=False)
    cancellation_reason = fields.Text(copy=False)
    event_ids = fields.One2many("odental.lab.case.event", "case_id", string="Trazabilidad", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("odental.lab.case") or "Nuevo"
        cases = super().create(vals_list)
        for case in cases:
            case._log_event("created", "Caso de laboratorio creado")
            case.clinical_record_id._log_event(
                "lab_case_created", f"Caso de laboratorio creado: {case.name}", source_record=case
            )
        return cases

    @api.constrains(
        "clinical_record_id", "treatment_line_id", "laboratory_id",
        "responsible_professional_id", "tooth_id", "estimated_cost", "actual_cost"
    )
    def _check_case(self):
        for case in self:
            if case.laboratory_id.organization_id != case.organization_id:
                raise ValidationError("El laboratorio no pertenece a la organización del expediente.")
            if case.organization_id not in case.responsible_professional_id.organization_ids:
                raise ValidationError("El profesional no pertenece a la organización del expediente.")
            if case.treatment_line_id and case.treatment_line_id.organization_id != case.organization_id:
                raise ValidationError("El procedimiento pertenece a otra organización.")
            if case.treatment_line_id and case.treatment_line_id.plan_id.clinical_record_id != case.clinical_record_id:
                raise ValidationError("El procedimiento pertenece a otro expediente.")
            if case.tooth_id and case.treatment_line_id.tooth_id and case.tooth_id != case.treatment_line_id.tooth_id:
                raise ValidationError("La pieza no coincide con el procedimiento seleccionado.")
            if case.estimated_cost < 0 or case.actual_cost < 0:
                raise ValidationError("Los costos no pueden ser negativos.")

    @api.onchange("laboratory_id", "requested_date")
    def _onchange_expected_date(self):
        for case in self:
            if case.laboratory_id and case.requested_date and not case.expected_return_date:
                case.expected_return_date = fields.Date.add(
                    case.requested_date, days=case.laboratory_id.default_turnaround_days
                )

    @api.onchange("treatment_line_id")
    def _onchange_treatment_line(self):
        for case in self:
            if case.treatment_line_id:
                case.tooth_id = case.treatment_line_id.tooth_id

    def write(self, vals):
        protected = {"state", "sent_date", "received_date", "accepted_date", "rework_count", "purchase_order_id"}
        if protected.intersection(vals) and not self.env.context.get("odental_lab_transition"):
            raise UserError("Utilice las acciones del caso para cambiar su estado o documentos.")
        clinical = {"clinical_record_id", "treatment_line_id", "tooth_id", "laboratory_id", "work_type", "material", "shade", "instructions"}
        if clinical.intersection(vals) and any(case.state in {"accepted", "cancelled"} for case in self):
            raise UserError("Un caso cerrado es inmutable.")
        return super().write(vals)

    def _log_event(self, event_type, note):
        self.ensure_one()
        self.env["odental.lab.case.event"].sudo().with_context(odental_lab_event=True).create({
            "case_id": self.id, "event_type": event_type, "note": note,
            "user_id": self.env.user.id,
        })

    def _transition(self, values, event_type, note):
        self.ensure_one()
        self.with_context(odental_lab_transition=True).write(values)
        self._log_event(event_type, note)

    def action_send(self):
        for case in self:
            if case.state not in {"draft", "rework"}:
                raise UserError("Solo un caso en preparación o retrabajo puede enviarse.")
            if not case.instructions or not case.expected_return_date:
                raise ValidationError("Complete las instrucciones y la fecha de entrega esperada.")
            case._transition({"state": "sent", "sent_date": fields.Date.context_today(case)}, "sent", "Trabajo enviado al laboratorio")
            case.clinical_record_id._log_event("lab_case_sent", f"Caso enviado: {case.name}", source_record=case)

    def action_receive(self):
        for case in self:
            if case.state != "sent":
                raise UserError("Solo un trabajo enviado puede recibirse.")
            case._transition({"state": "received", "received_date": fields.Date.context_today(case)}, "received", "Trabajo recibido del laboratorio")
            case.clinical_record_id._log_event("lab_case_received", f"Caso recibido: {case.name}", source_record=case)

    def action_fitting(self):
        for case in self:
            if case.state != "received":
                raise UserError("La prueba clínica requiere un trabajo recibido.")
            case._transition({"state": "fitting"}, "fitting", "Trabajo enviado a prueba clínica")

    def action_accept(self):
        for case in self:
            if case.state not in {"received", "fitting"}:
                raise UserError("Solo un trabajo recibido o en prueba puede aceptarse.")
            case._transition({"state": "accepted", "accepted_date": fields.Date.context_today(case)}, "accepted", "Trabajo aceptado clínicamente")
            case.clinical_record_id._log_event("lab_case_accepted", f"Caso aceptado: {case.name}", source_record=case)

    def action_rework(self):
        for case in self:
            if case.state not in {"received", "fitting"}:
                raise UserError("Solo un trabajo recibido o en prueba puede volver a laboratorio.")
            if not case.rework_reason:
                raise ValidationError("Indique el motivo del retrabajo.")
            case._transition(
                {"state": "rework", "rework_count": case.rework_count + 1},
                "rework", f"Retrabajo solicitado: {case.rework_reason}"
            )
            case.clinical_record_id._log_event("lab_case_rework", f"Retrabajo solicitado: {case.name}", source_record=case)

    def action_cancel(self):
        for case in self:
            if case.state in {"accepted", "cancelled"}:
                raise UserError("El caso ya está cerrado.")
            if not case.cancellation_reason:
                raise ValidationError("Indique el motivo de cancelación.")
            case._transition({"state": "cancelled"}, "cancelled", f"Caso cancelado: {case.cancellation_reason}")

    def action_create_purchase_order(self):
        self.ensure_one()
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError("Solo un administrador clínico puede crear la orden de compra.")
        if self.purchase_order_id:
            return self.action_view_purchase_order()
        if not self.purchase_product_id:
            raise ValidationError("Configure el servicio facturable del laboratorio.")
        product = self.purchase_product_id
        planned = fields.Datetime.to_datetime(
            self.expected_return_date or fields.Date.context_today(self)
        )
        order = self.env["purchase.order"].with_company(self.company_id).create({
            "partner_id": self.laboratory_id.partner_id.id,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "origin": self.name,
            "odental_lab_case_id": self.id,
            "order_line": [(0, 0, {
                "product_id": product.id, "name": f"{self.name} — {dict(self._fields['work_type'].selection)[self.work_type]}",
                "product_qty": 1, "product_uom": product.uom_po_id.id,
                "price_unit": self.estimated_cost, "date_planned": planned,
            })],
        })
        self.with_context(odental_lab_transition=True).write({"purchase_order_id": order.id})
        self._log_event("purchase", f"Orden de compra {order.name} creada en borrador")
        return self.action_view_purchase_order()

    def action_view_purchase_order(self):
        self.ensure_one()
        if not self.purchase_order_id:
            raise UserError("Este caso todavía no tiene orden de compra.")
        return {
            "type": "ir.actions.act_window", "res_model": "purchase.order",
            "res_id": self.purchase_order_id.id, "view_mode": "form", "target": "current",
        }


class ODentalLabCaseEvent(models.Model):
    _name = "odental.lab.case.event"
    _description = "Evento de laboratorio O Dental"
    _order = "occurred_at desc, id desc"

    case_id = fields.Many2one("odental.lab.case", required=True, ondelete="cascade", index=True)
    organization_id = fields.Many2one(related="case_id.organization_id", store=True, index=True)
    occurred_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user, readonly=True)
    event_type = fields.Selection(LAB_EVENT_TYPES, required=True, readonly=True)
    note = fields.Text(required=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("odental_lab_event"):
            raise AccessError("Los eventos solo se generan desde el flujo del caso.")
        return super().create(vals_list)

    def write(self, vals):
        raise UserError("La trazabilidad del laboratorio es inmutable.")

    def unlink(self):
        raise UserError("La trazabilidad del laboratorio es inmutable.")


class ODentalClinicalRecord(models.Model):
    _inherit = "odental.clinical.record"

    lab_case_ids = fields.One2many("odental.lab.case", "clinical_record_id", string="Casos de laboratorio")


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    odental_lab_case_id = fields.Many2one(
        "odental.lab.case", string="Caso de laboratorio O Dental", readonly=True, copy=False, index=True
    )


class ODentalClinicalAudit(models.Model):
    _inherit = "odental.clinical.audit"

    event_type = fields.Selection(
        selection_add=[
            ("lab_case_created", "Caso de laboratorio creado"),
            ("lab_case_sent", "Caso enviado al laboratorio"),
            ("lab_case_received", "Caso recibido del laboratorio"),
            ("lab_case_rework", "Retrabajo solicitado"),
            ("lab_case_accepted", "Caso de laboratorio aceptado"),
        ],
        ondelete={
            "lab_case_created": "cascade", "lab_case_sent": "cascade",
            "lab_case_received": "cascade", "lab_case_rework": "cascade",
            "lab_case_accepted": "cascade",
        },
    )
