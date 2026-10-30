from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


ANAMNESIS_FIELDS = {
    "anamnesis_chief_complaint",
    "anamnesis_present_illness",
    "anamnesis_oral_habits",
    "anamnesis_other_history",
    "anamnesis_positive_details",
    "anamnesis_observations",
    "anamnesis_pulse",
    "anamnesis_blood_pressure",
    "anamnesis_temperature",
    "anamnesis_respiratory_rate",
    "hx_allergies",
    "hx_blood_disorders",
    "hx_heart_disease",
    "hx_pregnancy",
    "hx_blood_pressure_changes",
    "hx_medications",
    "hx_current_medical_treatment",
    "hx_headaches",
    "hx_hepatitis",
    "hx_diabetes",
    "hx_rheumatic_fever",
    "hx_hiv_aids",
    "hx_immunosuppression",
    "hx_kidney_disease",
    "hx_respiratory_disease",
    "hx_hormonal_disorders",
    "hx_gastric_disorders",
    "hx_emotional_disorders",
    "hx_loss_of_consciousness",
    "hx_sinusitis",
    "hx_surgeries",
    "hx_extractions",
    "hx_oral_diseases",
    "hx_oral_appliances",
}


class ODentalPatientClinical(models.Model):
    _inherit = "odental.patient"

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if "organization_id" in fields_list and "organization_id" not in values:
            # Respect record rules and the active company; never choose an
            # arbitrary organization when the user has several possibilities.
            organizations = self.env["odental.organization"].search(
                [("company_id", "=", self.env.company.id)], limit=2
            )
            if len(organizations) == 1:
                values["organization_id"] = organizations.id
        return values

    def action_open_clinical_record(self):
        self.ensure_one()
        self.check_access_rights("read")
        self.check_access_rule("read")
        records = self.env["odental.clinical.record"]
        records.check_access_rights("read")
        record = records.search([("patient_id", "=", self.id)], limit=1)
        if not record:
            records.check_access_rights("create")
        # Opening this action does not create or reopen an expediente.
        # The user saves a new record explicitly; the existing unique
        # constraint remains the protection against concurrent duplicates.
        return {
            "type": "ir.actions.act_window",
            "name": "Expediente clínico",
            "res_model": "odental.clinical.record",
            "res_id": record.id or False,
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "current",
            "context": {"default_patient_id": self.id},
        }


class ODentalClinicalRecord(models.Model):
    _name = "odental.clinical.record"
    _description = "Expediente clínico O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "patient_id"
    _rec_name = "patient_id"

    patient_id = fields.Many2one(
        "odental.patient", required=True, ondelete="restrict", index=True, tracking=True,
        string="Paciente",
    )
    organization_id = fields.Many2one(
        related="patient_id.organization_id", store=True, index=True,
        string="Organización",
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True, string="Compañía")
    opened_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True, string="Fecha de apertura")
    state = fields.Selection(
        [("active", "Activo"), ("closed", "Cerrado")],
        required=True,
        default="active",
        tracking=True,
        index=True,
        string="Estado",
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
        string="Grupo sanguíneo",
    )
    alerts = fields.Text(string="Alertas clínicas", tracking=True)
    general_notes = fields.Text(string="Observaciones generales")
    anamnesis_chief_complaint = fields.Text(string="Motivo de consulta")
    anamnesis_present_illness = fields.Text(string="Historia de la enfermedad actual")
    # An unmarked checkbox means "not recorded", never a confirmed negative.
    hx_allergies = fields.Boolean(string="Alergias")
    hx_blood_disorders = fields.Boolean(string="Discrasias sanguíneas")
    hx_heart_disease = fields.Boolean(string="Cardiopatías")
    hx_pregnancy = fields.Boolean(string="Embarazo")
    hx_blood_pressure_changes = fields.Boolean(string="Alteraciones de tensión arterial")
    hx_medications = fields.Boolean(string="Ingesta de medicamentos")
    hx_current_medical_treatment = fields.Boolean(string="Tratamiento médico actual")
    hx_headaches = fields.Boolean(string="Cefaleas")
    hx_hepatitis = fields.Boolean(string="Hepatitis")
    hx_diabetes = fields.Boolean(string="Diabetes")
    hx_rheumatic_fever = fields.Boolean(string="Fiebre reumática")
    hx_hiv_aids = fields.Boolean(string="VIH/SIDA")
    hx_immunosuppression = fields.Boolean(string="Inmunosupresión")
    hx_kidney_disease = fields.Boolean(string="Patologías renales")
    hx_respiratory_disease = fields.Boolean(string="Patologías respiratorias")
    hx_hormonal_disorders = fields.Boolean(string="Trastornos hormonales")
    hx_gastric_disorders = fields.Boolean(string="Trastornos gástricos")
    hx_emotional_disorders = fields.Boolean(string="Trastornos emocionales")
    hx_loss_of_consciousness = fields.Boolean(string="Pérdida de conciencia")
    hx_sinusitis = fields.Boolean(string="Sinusitis")
    hx_surgeries = fields.Boolean(string="Cirugías (incluso orales)")
    hx_extractions = fields.Boolean(string="Exodoncias")
    hx_oral_diseases = fields.Boolean(string="Enfermedades orales")
    hx_oral_appliances = fields.Boolean(string="Aparatología oral")
    anamnesis_oral_habits = fields.Text(string="Hábitos asociados a la cavidad oral")
    anamnesis_other_history = fields.Text(string="Otras patologías o antecedentes médicos u odontológicos")
    anamnesis_positive_details = fields.Text(string="Detalles de respuestas positivas")
    anamnesis_observations = fields.Text(string="Observaciones e interconsultas")
    # Text keeps missing vital signs empty instead of displaying a misleading 0.
    anamnesis_pulse = fields.Char(string="Pulso (lpm)")
    anamnesis_blood_pressure = fields.Char(string="Presión arterial (mmHg)")
    anamnesis_temperature = fields.Char(string="Temperatura (°C)")
    anamnesis_respiratory_rate = fields.Char(string="Frecuencia respiratoria (rpm)")
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
        for record, values in zip(records, vals_list):
            record._log_event("record_created", "Expediente clínico creado")
            if any(values.get(field) for field in ANAMNESIS_FIELDS):
                record._log_event("anamnesis_updated", "Anamnesis registrada")
        return records

    def write(self, vals):
        changed_fields = ANAMNESIS_FIELDS.intersection(vals)
        changed_records = self.filtered(
            lambda record: any(record[field] != vals[field] for field in changed_fields)
        ) if changed_fields else self.browse()
        if changed_records.filtered(lambda record: record.state == "closed"):
            raise UserError("Reabra el expediente antes de modificar la anamnesis.")
        result = super().write(vals)
        for record in changed_records:
            record._log_event("anamnesis_updated", "Anamnesis actualizada")
        return result

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
        "odental.clinical.record", required=True, ondelete="cascade", index=True,
        string="Expediente clínico",
    )
    patient_id = fields.Many2one(
        related="clinical_record_id.patient_id", store=True, index=True,
        string="Paciente",
    )
    organization_id = fields.Many2one(
        related="clinical_record_id.organization_id", store=True, index=True,
        string="Organización",
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
        string="Categoría",
    )
    name = fields.Char(required=True, tracking=True, string="Nombre")
    details = fields.Text(string="Detalles")
    start_date = fields.Date(string="Fecha de inicio")
    end_date = fields.Date(string="Fecha de finalización")
    status = fields.Selection(
        [("active", "Activo"), ("resolved", "Resuelto"), ("inactive", "Inactivo")],
        required=True,
        default="active",
        tracking=True,
        string="Estado",
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
        string="Confidencialidad",
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
