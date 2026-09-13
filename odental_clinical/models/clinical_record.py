from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ODentalClinicalRecord(models.Model):
    _name = "odental.clinical.record"
    _description = "Expediente clínico O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "patient_id"
    _rec_name = "patient_id"

    patient_id = fields.Many2one(
        "odental.patient", required=True, ondelete="restrict", index=True, tracking=True
    )
    organization_id = fields.Many2one(
        related="patient_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    opened_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    state = fields.Selection(
        [("active", "Activo"), ("closed", "Cerrado")],
        required=True,
        default="active",
        tracking=True,
        index=True,
    )
    blood_type = fields.Selection(
        [
            ("a_positive", "A+"),
            ("a_negative", "A-"),
            ("b_positive", "B+"),
            ("b_negative", "B-"),
            ("ab_positive", "AB+"),
            ("ab_negative", "AB-"),
            ("o_positive", "O+"),
            ("o_negative", "O-"),
            ("unknown", "No conocido"),
        ],
        default="unknown",
        tracking=True,
    )
    alerts = fields.Text(string="Alertas clínicas", tracking=True)
    general_notes = fields.Text(string="Observaciones generales")
    history_entry_ids = fields.One2many(
        "odental.medical.history.entry", "clinical_record_id", string="Antecedentes"
    )
    encounter_ids = fields.One2many(
        "odental.clinical.encounter", "clinical_record_id", string="Evoluciones"
    )
    consent_ids = fields.One2many(
        "odental.patient.consent", "clinical_record_id", string="Consentimientos"
    )

    _sql_constraints = [
        (
            "patient_unique_clinical_record",
            "unique(patient_id)",
            "El paciente ya posee un expediente clínico.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._log_event("record_created", "Expediente clínico creado")
        return records

    def _log_event(self, event_type, summary, content_hash=False, source_record=False):
        for record in self:
            source = source_record or record
            self.env["odental.clinical.audit"].sudo().create(
                {
                    "organization_id": record.organization_id.id,
                    "patient_id": record.patient_id.id,
                    "user_id": self.env.user.id,
                    "event_type": event_type,
                    "model_name": source._name,
                    "record_res_id": source.id,
                    "summary": summary,
                    "content_hash": content_hash,
                }
            )

    def action_close(self):
        active_records = self.filtered(lambda record: record.state == "active")
        active_records.write({"state": "closed"})
        active_records._log_event("record_closed", "Expediente clínico cerrado")

    def action_reopen(self):
        closed_records = self.filtered(lambda record: record.state == "closed")
        closed_records.write({"state": "active"})
        closed_records._log_event("record_reopened", "Expediente clínico reabierto")


class ODentalMedicalHistoryEntry(models.Model):
    _name = "odental.medical.history.entry"
    _description = "Antecedente médico O Dental"
    _inherit = ["mail.thread"]
    _order = "clinically_relevant desc, start_date desc, id desc"

    clinical_record_id = fields.Many2one(
        "odental.clinical.record", required=True, ondelete="cascade", index=True
    )
    patient_id = fields.Many2one(
        related="clinical_record_id.patient_id", store=True, index=True
    )
    organization_id = fields.Many2one(
        related="clinical_record_id.organization_id", store=True, index=True
    )
    category = fields.Selection(
        [
            ("allergy", "Alergia"),
            ("medication", "Medicamento actual"),
            ("condition", "Condición sistémica"),
            ("surgery", "Cirugía previa"),
            ("hospitalization", "Hospitalización"),
            ("pregnancy", "Embarazo"),
            ("anesthesia_reaction", "Reacción a anestesia"),
            ("family_history", "Antecedente familiar"),
            ("mental_health", "Salud mental"),
            ("other", "Otro"),
        ],
        required=True,
        index=True,
        tracking=True,
    )
    name = fields.Char(required=True, tracking=True)
    details = fields.Text()
    start_date = fields.Date(string="Fecha de inicio")
    end_date = fields.Date(string="Fecha de finalización")
    status = fields.Selection(
        [("active", "Activo"), ("resolved", "Resuelto"), ("inactive", "Inactivo")],
        required=True,
        default="active",
        tracking=True,
    )
    severity = fields.Selection(
        [
            ("mild", "Leve"),
            ("moderate", "Moderada"),
            ("severe", "Severa"),
            ("critical", "Crítica"),
        ],
        string="Severidad",
    )
    clinically_relevant = fields.Boolean(
        string="Relevante para atención odontológica", default=True, tracking=True
    )
    sensitivity = fields.Selection(
        [("regular", "Clínica"), ("restricted", "Restringida")],
        required=True,
        default="regular",
        tracking=True,
    )
    referral_sharing = fields.Selection(
        [
            ("never", "Nunca compartir automáticamente"),
            ("review", "Revisión profesional obligatoria"),
            ("include", "Incluir cuando sea clínicamente necesario"),
        ],
        required=True,
        default="review",
        string="Uso en referencias",
        tracking=True,
    )

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for entry in self:
            if entry.start_date and entry.end_date and entry.end_date < entry.start_date:
                raise ValidationError("La fecha final no puede ser anterior a la fecha inicial.")

    @api.model_create_multi
    def create(self, vals_list):
        entries = super().create(vals_list)
        for entry in entries:
            entry.clinical_record_id._log_event(
                "history_created",
                f"Antecedente clínico creado: {entry.category}",
                source_record=entry,
            )
        return entries

    def write(self, vals):
        result = super().write(vals)
        for entry in self:
            entry.clinical_record_id._log_event(
                "history_updated",
                f"Antecedente clínico actualizado: {entry.category}",
                source_record=entry,
            )
        return result

    def unlink(self):
        audit_values = [(entry.clinical_record_id, entry.category) for entry in self]
        result = super().unlink()
        for record, category in audit_values:
            record._log_event("history_deleted", f"Antecedente clínico eliminado: {category}")
        return result
