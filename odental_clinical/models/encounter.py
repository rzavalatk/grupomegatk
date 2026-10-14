import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ODentalClinicalEncounter(models.Model):
    _name = "odental.clinical.encounter"
    _description = "Evolución clínica O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "encounter_datetime desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True, string="Nombre")
    clinical_record_id = fields.Many2one(
        "odental.clinical.record", required=True, ondelete="restrict", index=True,
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
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True, string="Compañía")
    appointment_id = fields.Many2one(
        "odental.appointment", string="Cita relacionada", ondelete="set null", index=True
    )
    professional_id = fields.Many2one(
        "odental.professional", required=True, ondelete="restrict", index=True, tracking=True,
        string="Profesional responsable",
    )
    encounter_datetime = fields.Datetime(
        string="Fecha y hora", required=True, default=fields.Datetime.now, index=True
    )
    chief_complaint = fields.Text(string="Motivo de consulta", tracking=True)
    history_present_illness = fields.Text(
        string="Historia de la enfermedad actual", tracking=True,
        help="Relato del paciente: inicio, duración y evolución de los síntomas, factores que los alivian o agravan y atención previa.",
    )
    oral_habits = fields.Text(string="Hábitos asociados a la cavidad oral")
    additional_history = fields.Text(string="Otros antecedentes médicos u odontológicos")
    interconsultation_notes = fields.Text(string="Observaciones e interconsultas")
    pulse_bpm = fields.Char(string="Pulso (latidos/min)")
    blood_pressure = fields.Char(string="Presión arterial (mmHg)")
    temperature_celsius = fields.Char(string="Temperatura (°C)")
    respiratory_rate = fields.Char(string="Frecuencia respiratoria (resp/min)")
    clinical_findings = fields.Text(string="Hallazgos clínicos", tracking=True)
    diagnosis_summary = fields.Text(string="Diagnóstico", tracking=True)
    treatment_plan = fields.Text(string="Plan de tratamiento", tracking=True)
    procedures_performed = fields.Text(string="Procedimientos realizados", tracking=True)
    prescriptions = fields.Text(string="Indicaciones y prescripciones", tracking=True)
    private_notes = fields.Text(
        string="Notas clínicas restringidas",
        help="No se incluyen automáticamente en referencias ni accesos temporales.",
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("signed", "Firmada"),
            ("amended", "Rectificada"),
            ("cancelled", "Cancelada"),
        ],
        required=True,
        default="draft",
        tracking=True,
        index=True,
        string="Estado",
    )
    signed_at = fields.Datetime(readonly=True, string="Fecha de firma")
    signed_by_user_id = fields.Many2one("res.users", readonly=True, string="Firma registrada por")
    content_hash = fields.Char(string="Huella digital", readonly=True, copy=False, index=True)
    signature_schema_version = fields.Integer(default=1, readonly=True, copy=False)
    version = fields.Integer(required=True, default=1, readonly=True, copy=False, string="Versión")
    previous_version_id = fields.Many2one(
        "odental.clinical.encounter", readonly=True, copy=False, ondelete="restrict",
        string="Versión anterior",
    )
    amendment_ids = fields.One2many(
        "odental.clinical.encounter", "previous_version_id", string="Rectificaciones"
    )
    amendment_reason = fields.Text(string="Motivo de rectificación", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        signature_fields = ("state", "signed_at", "signed_by_user_id", "content_hash")
        defaults = self.default_get(list(signature_fields))
        for vals in vals_list:
            initial = dict(defaults, **vals)
            if initial.get("state", "draft") != "draft" or any(
                initial.get(field) for field in signature_fields[1:]
            ):
                raise UserError("Cree la evolución en borrador y utilice la acción de firma.")
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.clinical.encounter"
                ) or "Nuevo"
            vals["signature_schema_version"] = 2
        encounters = super().create(vals_list)
        for encounter in encounters:
            encounter.clinical_record_id._log_event(
                "encounter_created",
                f"Evolución clínica creada: {encounter.name}",
                source_record=encounter,
            )
        return encounters

    @api.constrains("clinical_record_id", "appointment_id", "professional_id")
    def _check_relations(self):
        for encounter in self:
            organization = encounter.organization_id
            if organization not in encounter.professional_id.organization_ids:
                raise ValidationError("El profesional no pertenece a la organización del expediente.")
            if encounter.appointment_id:
                if encounter.appointment_id.patient_id != encounter.patient_id:
                    raise ValidationError("La cita corresponde a otro paciente.")
                if encounter.appointment_id.organization_id != organization:
                    raise ValidationError("La cita corresponde a otra organización.")
                if encounter.appointment_id.professional_id != encounter.professional_id:
                    raise ValidationError("La cita corresponde a otro profesional.")

    def _hash_payload(self):
        self.ensure_one()
        payload = {
            "record": self.clinical_record_id.id,
            "patient": self.patient_id.id,
            "professional": self.professional_id.id,
            "datetime": fields.Datetime.to_string(self.encounter_datetime),
            "version": self.version,
            "chief_complaint": self.chief_complaint or "",
            "clinical_findings": self.clinical_findings or "",
            "diagnosis_summary": self.diagnosis_summary or "",
            "treatment_plan": self.treatment_plan or "",
            "procedures_performed": self.procedures_performed or "",
            "prescriptions": self.prescriptions or "",
            "private_notes": self.private_notes or "",
        }
        # Existing signed evolutions retain their original hash payload.
        if self.signature_schema_version >= 2:
            payload.update({
                "history_present_illness": self.history_present_illness or "",
                "oral_habits": self.oral_habits or "",
                "additional_history": self.additional_history or "",
                "interconsultation_notes": self.interconsultation_notes or "",
                "pulse_bpm": self.pulse_bpm or "",
                "blood_pressure": self.blood_pressure or "",
                "temperature_celsius": self.temperature_celsius or "",
                "respiratory_rate": self.respiratory_rate or "",
            })
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def write(self, vals):
        protected_fields = {
            "clinical_record_id",
            "appointment_id",
            "professional_id",
            "encounter_datetime",
            "chief_complaint",
            "history_present_illness",
            "oral_habits",
            "additional_history",
            "interconsultation_notes",
            "pulse_bpm",
            "blood_pressure",
            "temperature_celsius",
            "respiratory_rate",
            "clinical_findings",
            "diagnosis_summary",
            "treatment_plan",
            "procedures_performed",
            "prescriptions",
            "private_notes",
            "signature_schema_version",
            "version",
            "previous_version_id",
            "amendment_reason",
            "signed_at",
            "signed_by_user_id",
            "content_hash",
        }
        if {"signed_at", "signed_by_user_id", "content_hash"}.intersection(vals):
            raise UserError("Los datos de firma se generan mediante la acción de firma.")
        for encounter in self:
            if vals.get("state") in ("signed", "amended"):
                raise UserError("Utilice las acciones de firma o rectificación.")
            if (
                encounter.state in ("signed", "amended")
                and vals.get("state")
                and vals["state"] != encounter.state
            ):
                raise UserError("El estado de una evolución firmada no puede revertirse.")
            if encounter.state in ("signed", "amended") and protected_fields.intersection(vals):
                raise UserError(
                    "Una evolución firmada no puede modificarse. Cree una rectificación."
                )
        return super().write(vals)

    def unlink(self):
        if any(encounter.state in ("signed", "amended") for encounter in self):
            raise UserError("Una evolución firmada o rectificada no puede eliminarse.")
        return super().unlink()

    def action_sign(self):
        for encounter in self:
            if encounter.state != "draft":
                raise UserError("Solo las evoluciones en borrador pueden firmarse.")
            if not any(
                [
                    encounter.chief_complaint,
                    encounter.history_present_illness,
                    encounter.clinical_findings,
                    encounter.diagnosis_summary,
                    encounter.procedures_performed,
                ]
            ):
                raise ValidationError("Debe registrar contenido clínico antes de firmar.")
            if encounter.previous_version_id and not encounter.amendment_reason:
                raise ValidationError("Debe indicar el motivo de la rectificación.")
            if encounter.signature_schema_version < 2:
                super(ODentalClinicalEncounter, encounter).write(
                    {"signature_schema_version": 2}
                )
            content_hash = encounter._hash_payload()
            super(ODentalClinicalEncounter, encounter).write(
                {
                    "state": "signed",
                    "signed_at": fields.Datetime.now(),
                    "signed_by_user_id": self.env.user.id,
                    "content_hash": content_hash,
                }
            )
            encounter.clinical_record_id._log_event(
                "encounter_signed",
                f"Evolución clínica firmada: {encounter.name}, versión {encounter.version}",
                content_hash,
                source_record=encounter,
            )

    def action_create_amendment(self):
        self.ensure_one()
        if self.state != "signed":
            raise UserError("Solo una evolución firmada puede rectificarse.")
        values = {
            "clinical_record_id": self.clinical_record_id.id,
            "appointment_id": self.appointment_id.id,
            "professional_id": self.professional_id.id,
            "encounter_datetime": self.encounter_datetime,
            "chief_complaint": self.chief_complaint,
            "history_present_illness": self.history_present_illness,
            "oral_habits": self.oral_habits,
            "additional_history": self.additional_history,
            "interconsultation_notes": self.interconsultation_notes,
            "pulse_bpm": self.pulse_bpm,
            "blood_pressure": self.blood_pressure,
            "temperature_celsius": self.temperature_celsius,
            "respiratory_rate": self.respiratory_rate,
            "clinical_findings": self.clinical_findings,
            "diagnosis_summary": self.diagnosis_summary,
            "treatment_plan": self.treatment_plan,
            "procedures_performed": self.procedures_performed,
            "prescriptions": self.prescriptions,
            "private_notes": self.private_notes,
            "version": self.version + 1,
            "previous_version_id": self.id,
        }
        amendment = self.create(values)
        super(ODentalClinicalEncounter, self).write({"state": "amended"})
        self.clinical_record_id._log_event(
            "encounter_amended",
            f"Rectificación creada para {self.name}: versión {amendment.version}",
            source_record=amendment,
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "odental.clinical.encounter",
            "res_id": amendment.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_cancel(self):
        self.filtered(lambda encounter: encounter.state == "draft").write(
            {"state": "cancelled"}
        )
