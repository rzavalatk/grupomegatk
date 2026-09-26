import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


CONSENT_PURPOSES = [
    ("treatment", "Tratamiento"),
    ("referral", "Referencia profesional"),
    ("images", "Imágenes clínicas"),
    ("data_processing", "Tratamiento de datos"),
    ("research", "Docencia o investigación"),
    ("other", "Otro"),
]


class ODentalConsentTemplate(models.Model):
    _name = "odental.consent.template"
    _description = "Plantilla de consentimiento O Dental"
    _inherit = ["mail.thread"]
    _order = "name, version desc"

    name = fields.Char(required=True, tracking=True, string="Nombre")
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="restrict", index=True,
        string="Organización",
    )
    purpose = fields.Selection(CONSENT_PURPOSES, required=True, default="treatment", string="Finalidad")
    version = fields.Integer(required=True, default=1, string="Versión")
    text = fields.Html(string="Texto del consentimiento", required=True, sanitize=True)
    active = fields.Boolean(default=True, string="Activo")

    _sql_constraints = [
        (
            "template_name_version_organization_unique",
            "unique(name, version, organization_id)",
            "Ya existe esta versión de la plantilla en la organización.",
        )
    ]

    @api.constrains("version")
    def _check_version(self):
        if any(template.version <= 0 for template in self):
            raise ValidationError("La versión de la plantilla debe ser mayor que cero.")


class ODentalPatientConsent(models.Model):
    _name = "odental.patient.consent"
    _description = "Consentimiento del paciente O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

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
    professional_id = fields.Many2one(
        "odental.professional", string="Profesional responsable", ondelete="restrict"
    )
    template_id = fields.Many2one(
        "odental.consent.template", required=True, ondelete="restrict",
        string="Plantilla",
    )
    template_name = fields.Char(readonly=True, required=True, string="Nombre de la plantilla")
    template_version = fields.Integer(readonly=True, required=True, string="Versión de la plantilla")
    purpose = fields.Selection(CONSENT_PURPOSES, required=True, readonly=True, string="Finalidad")
    consent_text = fields.Html(
        string="Documento autorizado", required=True, readonly=True, sanitize=True
    )
    scope_summary = fields.Text(
        string="Resumen comprensible del alcance",
        help="Explica al paciente qué autoriza, para qué finalidad y durante cuánto tiempo.",
    )
    valid_from = fields.Date(default=fields.Date.context_today, string="Válido desde")
    valid_until = fields.Date(string="Válido hasta")
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("pending", "Pendiente"),
            ("signed", "Firmado"),
            ("rejected", "Rechazado"),
            ("revoked", "Revocado"),
            ("expired", "Vencido"),
        ],
        required=True,
        default="draft",
        tracking=True,
        index=True,
        string="Estado",
    )
    signer_type = fields.Selection(
        [("patient", "Paciente"), ("representative", "Representante")],
        default="patient",
        required=True,
        string="Tipo de firmante",
    )
    signer_name = fields.Char(string="Nombre del firmante")
    signer_identification = fields.Char(string="Identificación del firmante")
    verification_method = fields.Selection(
        [
            ("in_person", "Firma presencial"),
            ("email_otp", "Código por correo"),
            ("whatsapp_otp", "Código por WhatsApp"),
            ("secure_portal", "Portal seguro"),
            ("paper", "Documento físico digitalizado"),
        ],
        string="Método de verificación",
    )
    verification_reference = fields.Char(
        string="Referencia de verificación",
        help="Identificador técnico de la sesión. No almacena el código secreto.",
    )
    signature = fields.Binary(string="Firma o documento", attachment=True)
    signature_filename = fields.Char(string="Nombre del archivo")
    signed_at = fields.Datetime(readonly=True, string="Fecha de firma")
    signed_by_user_id = fields.Many2one("res.users", readonly=True, string="Firma registrada por")
    content_hash = fields.Char(string="Huella digital", readonly=True, copy=False, index=True)
    revocation_reason = fields.Text(string="Motivo de revocación")
    revoked_at = fields.Datetime(readonly=True, string="Fecha de revocación")
    revoked_by_user_id = fields.Many2one("res.users", readonly=True, string="Revocación registrada por")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.patient.consent"
                ) or "Nuevo"
            template = self.env["odental.consent.template"].browse(vals.get("template_id"))
            if template:
                vals.setdefault("template_name", template.name)
                vals.setdefault("template_version", template.version)
                vals.setdefault("purpose", template.purpose)
                vals.setdefault("consent_text", template.text)
        consents = super().create(vals_list)
        for consent in consents:
            consent.clinical_record_id._log_event(
                "consent_created", f"Consentimiento creado: {consent.name}"
            )
        return consents

    @api.onchange("template_id")
    def _onchange_template_id(self):
        for consent in self:
            if consent.template_id:
                consent.template_name = consent.template_id.name
                consent.template_version = consent.template_id.version
                consent.purpose = consent.template_id.purpose
                consent.consent_text = consent.template_id.text

    @api.constrains("template_id", "organization_id", "professional_id")
    def _check_relations(self):
        for consent in self:
            if consent.template_id.organization_id != consent.organization_id:
                raise ValidationError("La plantilla pertenece a otra organización.")
            if (
                consent.professional_id
                and consent.organization_id not in consent.professional_id.organization_ids
            ):
                raise ValidationError("El profesional pertenece a otra organización.")

    @api.constrains("valid_from", "valid_until")
    def _check_validity(self):
        for consent in self:
            if consent.valid_from and consent.valid_until and consent.valid_until < consent.valid_from:
                raise ValidationError("La fecha de vencimiento no puede ser anterior al inicio.")

    def _hash_payload(self):
        self.ensure_one()
        payload = {
            "patient": self.patient_id.id,
            "organization": self.organization_id.id,
            "template_name": self.template_name,
            "template_version": self.template_version,
            "purpose": self.purpose,
            "consent_text": str(self.consent_text or ""),
            "scope_summary": self.scope_summary or "",
            "valid_from": fields.Date.to_string(self.valid_from),
            "valid_until": fields.Date.to_string(self.valid_until),
            "signer_type": self.signer_type,
            "signer_name": self.signer_name or "",
            "signer_identification": self.signer_identification or "",
            "verification_method": self.verification_method or "",
            "verification_reference": self.verification_reference or "",
        }
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def write(self, vals):
        immutable_fields = {
            "clinical_record_id",
            "professional_id",
            "template_id",
            "template_name",
            "template_version",
            "purpose",
            "consent_text",
            "scope_summary",
            "valid_from",
            "valid_until",
            "signer_type",
            "signer_name",
            "signer_identification",
            "verification_method",
            "verification_reference",
            "signature",
            "signature_filename",
            "signed_at",
            "signed_by_user_id",
            "content_hash",
        }
        if not self.env.context.get("allow_consent_transition"):
            for consent in self:
                if vals.get("state") in ("signed", "revoked", "expired"):
                    raise UserError("Utilice las acciones controladas del consentimiento.")
                if (
                    consent.state in ("signed", "revoked", "expired")
                    and vals.get("state")
                    and vals["state"] != consent.state
                ):
                    raise UserError("El estado del consentimiento no puede revertirse.")
                if consent.state in ("signed", "revoked", "expired") and immutable_fields.intersection(vals):
                    raise UserError(
                        "Un consentimiento firmado no puede alterarse. Debe emitirse uno nuevo."
                    )
        if "template_id" in vals:
            template = self.env["odental.consent.template"].browse(vals["template_id"])
            vals.update(
                {
                    "template_name": template.name,
                    "template_version": template.version,
                    "purpose": template.purpose,
                    "consent_text": template.text,
                }
            )
        return super().write(vals)

    def unlink(self):
        if any(consent.state not in ("draft", "rejected") for consent in self):
            raise UserError("Este consentimiento debe conservarse como evidencia y no puede eliminarse.")
        return super().unlink()

    def action_request(self):
        drafts = self.filtered(lambda consent: consent.state == "draft")
        drafts.write({"state": "pending"})
        for consent in drafts:
            consent.clinical_record_id._log_event(
                "consent_requested",
                f"Consentimiento solicitado: {consent.name}",
                source_record=consent,
            )

    def action_sign(self):
        for consent in self:
            if consent.state not in ("draft", "pending"):
                raise UserError("Este consentimiento no está disponible para firma.")
            if not consent.signer_name or not consent.verification_method:
                raise ValidationError("Indique el firmante y el método de verificación.")
            if not consent.signature and not consent.verification_reference:
                raise ValidationError("Debe existir una firma o una referencia de verificación.")
            content_hash = consent._hash_payload()
            consent.with_context(allow_consent_transition=True).write(
                {
                    "state": "signed",
                    "signed_at": fields.Datetime.now(),
                    "signed_by_user_id": self.env.user.id,
                    "content_hash": content_hash,
                }
            )
            consent.clinical_record_id._log_event(
                "consent_signed",
                f"Consentimiento firmado: {consent.name}",
                content_hash,
                source_record=consent,
            )

    def action_reject(self):
        available = self.filtered(lambda consent: consent.state in ("draft", "pending"))
        available.write({"state": "rejected"})
        for consent in available:
            consent.clinical_record_id._log_event(
                "consent_rejected",
                f"Consentimiento rechazado: {consent.name}",
                source_record=consent,
            )

    def action_revoke(self):
        for consent in self:
            if consent.state != "signed":
                raise UserError("Solo un consentimiento firmado puede revocarse.")
            if not consent.revocation_reason:
                raise ValidationError("Debe registrar el motivo de la revocación.")
            consent.with_context(allow_consent_transition=True).write(
                {
                    "state": "revoked",
                    "revoked_at": fields.Datetime.now(),
                    "revoked_by_user_id": self.env.user.id,
                }
            )
            consent.clinical_record_id._log_event(
                "consent_revoked",
                f"Consentimiento revocado: {consent.name}",
                source_record=consent,
            )
