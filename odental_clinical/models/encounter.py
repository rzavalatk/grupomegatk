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
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.clinical.encounter"
                ) or "Nuevo"
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
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def write(self, vals):
        protected_fields = {
            "clinical_record_id",
            "appointment_id",
            "professional_id",
            "encounter_datetime",
            "chief_complaint",
            "clinical_findings",
            "diagnosis_summary",
            "treatment_plan",
            "procedures_performed",
            "prescriptions",
            "private_notes",
            "version",
            "previous_version_id",
            "amendment_reason",
            "signed_at",
            "signed_by_user_id",
            "content_hash",
        }
        if not self.env.context.get("allow_clinical_transition"):
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
                    encounter.clinical_findings,
                    encounter.diagnosis_summary,
                    encounter.procedures_performed,
                ]
            ):
                raise ValidationError("Debe registrar contenido clínico antes de firmar.")
            if encounter.previous_version_id and not encounter.amendment_reason:
                raise ValidationError("Debe indicar el motivo de la rectificación.")
            content_hash = encounter._hash_payload()
            encounter.with_context(allow_clinical_transition=True).write(
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
        self.with_context(allow_clinical_transition=True).write({"state": "amended"})
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
