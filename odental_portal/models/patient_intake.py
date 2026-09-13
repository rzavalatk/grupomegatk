from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ODentalPatientIntake(models.Model):
    _name = "odental.patient.intake"
    _description = "Formulario clínico del paciente O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "submitted_at desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    patient_id = fields.Many2one(
        "odental.patient", required=True, ondelete="restrict", index=True, tracking=True
    )
    organization_id = fields.Many2one(
        related="patient_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    clinical_record_id = fields.Many2one(
        "odental.clinical.record", required=True, ondelete="restrict", index=True
    )
    invitation_id = fields.Many2one(
        "odental.patient.portal.invitation", readonly=True, copy=False, ondelete="restrict"
    )
    allergies = fields.Text(string="Alergias")
    medications = fields.Text(string="Medicamentos actuales")
    medical_conditions = fields.Text(string="Condiciones médicas")
    surgeries = fields.Text(string="Cirugías u hospitalizaciones")
    anesthesia_reactions = fields.Text(string="Reacciones a anestesia")
    pregnancy = fields.Boolean(string="Embarazo declarado")
    pregnancy_details = fields.Char(string="Detalle de embarazo")
    other_information = fields.Text(string="Otra información relevante")
    truth_confirmed = fields.Boolean(string="Declaración confirmada", required=True)
    submitted_at = fields.Datetime(required=True, readonly=True, default=fields.Datetime.now)
    submitted_ip_address = fields.Char(readonly=True)
    submitted_user_agent = fields.Char(readonly=True)
    reviewed_at = fields.Datetime(readonly=True, copy=False)
    reviewed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    review_notes = fields.Text()
    incorporated_entry_ids = fields.Many2many(
        "odental.medical.history.entry",
        "odental_intake_history_rel",
        "intake_id",
        "history_id",
        string="Antecedentes incorporados",
        readonly=True,
        copy=False,
    )
    state = fields.Selection(
        [
            ("submitted", "Pendiente"),
            ("reviewed", "Revisado"),
            ("incorporated", "Incorporado"),
            ("rejected", "Rechazado"),
        ],
        required=True,
        default="submitted",
        tracking=True,
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not self.env.context.get("odental_portal_submission"):
                raise AccessError("Los formularios se crean únicamente desde el portal seguro.")
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.patient.intake"
                ) or "Nuevo"
        records = super().create(vals_list)
        for intake in records:
            intake.clinical_record_id._log_event(
                "portal_intake_submitted",
                f"Formulario clínico recibido: {intake.name}",
                source_record=intake,
            )
        return records

    @api.constrains("patient_id", "clinical_record_id", "truth_confirmed")
    def _check_relationships(self):
        for intake in self:
            if intake.clinical_record_id.patient_id != intake.patient_id:
                raise ValidationError("El expediente no corresponde al paciente.")
            if not intake.truth_confirmed:
                raise ValidationError("El paciente debe confirmar la veracidad de la información.")

    def write(self, vals):
        protected = {
            "patient_id", "organization_id", "clinical_record_id", "invitation_id",
            "allergies", "medications", "medical_conditions", "surgeries",
            "anesthesia_reactions", "pregnancy", "pregnancy_details",
            "other_information", "truth_confirmed", "submitted_at",
            "submitted_ip_address", "submitted_user_agent", "state",
            "reviewed_at", "reviewed_by_id", "incorporated_entry_ids",
        }
        if protected.intersection(vals) and not self.env.context.get("allow_intake_transition"):
            raise UserError("El formulario enviado es inmutable; utilice las acciones de revisión.")
        return super().write(vals)

    def unlink(self):
        raise UserError("Los formularios recibidos se conservan como evidencia clínica.")

    def action_review(self):
        for intake in self:
            if intake.state != "submitted":
                raise UserError("Este formulario ya fue revisado.")
            intake.with_context(allow_intake_transition=True).write(
                {
                    "state": "reviewed",
                    "reviewed_at": fields.Datetime.now(),
                    "reviewed_by_id": self.env.user.id,
                }
            )

    def _history_values(self):
        self.ensure_one()
        values = []
        mapping = [
            ("allergy", "Alergias declaradas", self.allergies),
            ("medication", "Medicamentos declarados", self.medications),
            ("condition", "Condiciones médicas declaradas", self.medical_conditions),
            ("surgery", "Cirugías u hospitalizaciones declaradas", self.surgeries),
            ("anesthesia_reaction", "Reacciones a anestesia declaradas", self.anesthesia_reactions),
            ("other", "Otra información declarada", self.other_information),
        ]
        for category, name, details in mapping:
            if (details or "").strip():
                values.append(
                    {
                        "clinical_record_id": self.clinical_record_id.id,
                        "category": category,
                        "name": name,
                        "details": details.strip(),
                        "status": "active",
                        "sensitivity": "regular",
                        "referral_sharing": "review",
                    }
                )
        if self.pregnancy:
            values.append(
                {
                    "clinical_record_id": self.clinical_record_id.id,
                    "category": "pregnancy",
                    "name": "Embarazo declarado por el paciente",
                    "details": self.pregnancy_details or "Sin detalle adicional",
                    "status": "active",
                    "sensitivity": "regular",
                    "referral_sharing": "review",
                }
            )
        return values

    def action_incorporate(self):
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError("Solo un administrador clínico puede incorporar antecedentes.")
        for intake in self:
            if intake.state != "reviewed":
                raise UserError("Revise el formulario antes de incorporarlo.")
            values = intake._history_values()
            if not values:
                raise ValidationError("El formulario no contiene antecedentes para incorporar.")
            entries = self.env["odental.medical.history.entry"].create(values)
            intake.with_context(allow_intake_transition=True).write(
                {"state": "incorporated", "incorporated_entry_ids": [(6, 0, entries.ids)]}
            )
            intake.clinical_record_id._log_event(
                "portal_intake_incorporated",
                f"Formulario incorporado al expediente: {intake.name}",
                source_record=intake,
            )

    def action_reject(self):
        for intake in self:
            if intake.state not in {"submitted", "reviewed"}:
                raise UserError("Este formulario ya no puede rechazarse.")
            if not intake.review_notes:
                raise ValidationError("Indique el motivo o las observaciones del rechazo.")
            intake.with_context(allow_intake_transition=True).write(
                {
                    "state": "rejected",
                    "reviewed_at": fields.Datetime.now(),
                    "reviewed_by_id": self.env.user.id,
                }
            )
