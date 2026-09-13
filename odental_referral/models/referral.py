import base64
import binascii
import hashlib
import hmac
import json
import secrets
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


REFERRAL_ACTIVE_STATES = {"active"}


class ODentalReferral(models.Model):
    _name = "odental.referral"
    _description = "Referencia profesional O Dental"
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
    referring_professional_id = fields.Many2one(
        "odental.professional",
        string="Profesional que refiere",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
    )
    recipient_professional_id = fields.Many2one(
        "odental.professional",
        string="Profesional receptor registrado",
        ondelete="restrict",
        tracking=True,
    )
    recipient_name = fields.Char(string="Profesional receptor", required=True, tracking=True)
    recipient_email = fields.Char(string="Correo del receptor")
    recipient_mobile = fields.Char(string="Teléfono del receptor")
    recipient_license = fields.Char(string="Colegiación del receptor")
    recipient_specialty = fields.Char(string="Especialidad")
    referral_reason = fields.Text(string="Motivo de la referencia", required=True)
    clinical_question = fields.Text(string="Pregunta para el especialista")
    scope_summary = fields.Text(
        string="Resumen del alcance",
        compute="_compute_scope_summary",
        store=True,
    )
    scope_content_hash = fields.Char(
        string="Huella del contenido compartido",
        readonly=True,
        copy=False,
        index=True,
    )
    share_alerts = fields.Boolean(
        string="Compartir alertas clínicas necesarias",
        help="Incluye únicamente las alertas generales visibles del expediente.",
    )
    history_entry_ids = fields.Many2many(
        "odental.medical.history.entry",
        "odental_referral_history_rel",
        "referral_id",
        "history_id",
        string="Antecedentes seleccionados",
    )
    encounter_ids = fields.Many2many(
        "odental.clinical.encounter",
        "odental_referral_encounter_rel",
        "referral_id",
        "encounter_id",
        string="Evoluciones seleccionadas",
    )
    odontogram_ids = fields.Many2many(
        "odental.odontogram",
        "odental_referral_odontogram_rel",
        "referral_id",
        "odontogram_id",
        string="Odontogramas seleccionados",
    )
    image_ids = fields.Many2many(
        "odental.clinical.image",
        "odental_referral_image_rel",
        "referral_id",
        "image_id",
        string="Imágenes seleccionadas",
    )
    treatment_plan_ids = fields.Many2many(
        "odental.treatment.plan",
        "odental_referral_treatment_rel",
        "referral_id",
        "treatment_id",
        string="Planes seleccionados",
        help="En el portal externo se comparte contenido clínico, no importes ni datos de cobro.",
    )
    restricted_data_justification = fields.Text(
        string="Justificación de información restringida"
    )
    access_level = fields.Selection(
        [("read", "Solo lectura"), ("read_report", "Lectura y entrega de informe")],
        required=True,
        default="read_report",
        tracking=True,
    )
    allow_file_download = fields.Boolean(
        string="Permitir descarga de archivos",
        help="Cuando está desactivado, el portal permite visualización en línea cuando sea posible.",
    )
    valid_days = fields.Integer(string="Días de vigencia", required=True, default=15)
    expires_at = fields.Datetime(string="Vence el", readonly=True, copy=False, index=True)
    max_access_count = fields.Integer(string="Máximo de accesos", required=True, default=20)
    access_count = fields.Integer(string="Accesos realizados", readonly=True, copy=False)
    last_access_at = fields.Datetime(string="Último acceso", readonly=True, copy=False)
    consent_template_id = fields.Many2one(
        "odental.consent.template", string="Plantilla de consentimiento", ondelete="restrict"
    )
    consent_id = fields.Many2one(
        "odental.patient.consent",
        string="Consentimiento del paciente",
        readonly=True,
        copy=False,
        ondelete="restrict",
    )
    consent_state = fields.Selection(
        related="consent_id.state", string="Estado del consentimiento", readonly=True
    )
    consent_access_token_hash = fields.Char(
        readonly=True, copy=False, index=True, groups="odental_core.group_odental_admin"
    )
    consent_access_token_hint = fields.Char(readonly=True, copy=False)
    consent_otp_hash = fields.Char(
        readonly=True, copy=False, groups="odental_core.group_odental_admin"
    )
    consent_otp_attempts = fields.Integer(readonly=True, copy=False)
    consent_otp_locked_until = fields.Datetime(readonly=True, copy=False)
    consent_expires_at = fields.Datetime(
        string="Consentimiento digital vence el", readonly=True, copy=False, index=True
    )
    authorized_at = fields.Datetime(string="Autorizado el", readonly=True, copy=False)
    authorized_by_user_id = fields.Many2one(
        "res.users", string="Autorizado por", readonly=True, copy=False
    )
    activated_at = fields.Datetime(readonly=True, copy=False)
    revoked_at = fields.Datetime(readonly=True, copy=False)
    revoked_by_user_id = fields.Many2one("res.users", readonly=True, copy=False)
    revocation_reason = fields.Text(string="Motivo de revocación", copy=False)
    access_token_hash = fields.Char(readonly=True, copy=False, index=True, groups="odental_core.group_odental_admin")
    access_token_hint = fields.Char(readonly=True, copy=False)
    otp_hash = fields.Char(readonly=True, copy=False, groups="odental_core.group_odental_admin")
    otp_attempts = fields.Integer(readonly=True, copy=False)
    otp_locked_until = fields.Datetime(readonly=True, copy=False)
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("awaiting_consent", "Esperando consentimiento"),
            ("active", "Acceso activo"),
            ("report_submitted", "Informe recibido"),
            ("closed", "Cerrada"),
            ("revoked", "Revocada"),
            ("rejected", "Rechazada"),
            ("expired", "Vencida"),
            ("invalidated", "Invalidada por cambio clínico"),
        ],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )
    report_ids = fields.One2many(
        "odental.referral.report", "referral_id", string="Informes externos"
    )
    access_log_ids = fields.One2many(
        "odental.referral.access.log", "referral_id", string="Bitácora de acceso"
    )

    @api.depends(
        "recipient_name",
        "referral_reason",
        "share_alerts",
        "history_entry_ids",
        "encounter_ids",
        "odontogram_ids",
        "image_ids",
        "treatment_plan_ids",
        "valid_days",
        "access_level",
        "allow_file_download",
    )
    def _compute_scope_summary(self):
        for referral in self:
            parts = []
            if referral.share_alerts:
                parts.append("alertas clínicas necesarias")
            if referral.history_entry_ids:
                names = ", ".join(referral.history_entry_ids.mapped("name"))
                parts.append(f"antecedentes: {names}")
            if referral.encounter_ids:
                names = ", ".join(referral.encounter_ids.mapped("name"))
                parts.append(f"evoluciones: {names}")
            if referral.odontogram_ids:
                names = ", ".join(referral.odontogram_ids.mapped("name"))
                parts.append(f"odontogramas: {names}")
            if referral.image_ids:
                names = ", ".join(referral.image_ids.mapped("filename"))
                parts.append(f"imágenes: {names}")
            if referral.treatment_plan_ids:
                names = ", ".join(referral.treatment_plan_ids.mapped("name"))
                parts.append(f"planes clínicos: {names}")
            selected = ", ".join(parts) if parts else "ningún dato clínico seleccionado"
            access_description = (
                "consulta y entrega de un informe"
                if referral.access_level == "read_report"
                else "solo consulta"
            )
            download_description = (
                "con descarga de archivos autorizada"
                if referral.allow_file_download
                else "sin descarga de archivos"
            )
            referral.scope_summary = (
                f"Compartir con {referral.recipient_name or 'el profesional receptor'}: "
                f"{selected}, durante {referral.valid_days or 0} día(s). "
                f"Acceso: {access_description}, {download_description}. "
                f"Finalidad: {referral.referral_reason or 'pendiente de definir'}."
            )

    @api.onchange("recipient_professional_id")
    def _onchange_recipient_professional_id(self):
        for referral in self:
            professional = referral.recipient_professional_id
            if professional:
                referral.recipient_name = professional.name
                referral.recipient_email = professional.partner_id.email
                referral.recipient_mobile = professional.partner_id.mobile
                referral.recipient_license = professional.license_number
                referral.recipient_specialty = professional.specialty

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.referral"
                ) or "Nuevo"
        referrals = super().create(vals_list)
        for referral in referrals:
            referral.clinical_record_id._log_event(
                "referral_created",
                f"Referencia creada: {referral.name}",
                source_record=referral,
            )
        return referrals

    @api.constrains("valid_days", "max_access_count")
    def _check_limits(self):
        for referral in self:
            if referral.valid_days < 1 or referral.valid_days > 90:
                raise ValidationError("La vigencia debe estar entre 1 y 90 días.")
            if referral.max_access_count < 1 or referral.max_access_count > 500:
                raise ValidationError("El máximo de accesos debe estar entre 1 y 500.")

    @api.constrains(
        "clinical_record_id",
        "referring_professional_id",
        "recipient_professional_id",
        "consent_template_id",
        "history_entry_ids",
        "encounter_ids",
        "odontogram_ids",
        "image_ids",
        "treatment_plan_ids",
    )
    def _check_scope_relations(self):
        for referral in self:
            record = referral.clinical_record_id
            organization = referral.organization_id
            if organization not in referral.referring_professional_id.organization_ids:
                raise ValidationError("El profesional que refiere pertenece a otra organización.")
            if referral.consent_template_id:
                if referral.consent_template_id.organization_id != organization:
                    raise ValidationError("La plantilla de consentimiento pertenece a otra organización.")
                if referral.consent_template_id.purpose != "referral":
                    raise ValidationError("La plantilla debe ser para referencias profesionales.")
            for scoped_records in (
                referral.history_entry_ids,
                referral.encounter_ids,
                referral.odontogram_ids,
                referral.image_ids,
                referral.treatment_plan_ids,
            ):
                if any(item.clinical_record_id != record for item in scoped_records):
                    raise ValidationError("La selección contiene información de otro expediente.")
            if referral.history_entry_ids.filtered(lambda item: item.referral_sharing == "never"):
                raise ValidationError("Un antecedente seleccionado está marcado para no compartirse.")
            if referral.image_ids.filtered(lambda item: item.referral_sharing == "never"):
                raise ValidationError("Una imagen seleccionada está marcada para no compartirse.")
            unsigned_encounters = referral.encounter_ids.filtered(
                lambda item: item.state != "signed"
            )
            if unsigned_encounters:
                raise ValidationError("Solo pueden compartirse evoluciones firmadas vigentes.")
            unsigned_charts = referral.odontogram_ids.filtered(lambda item: item.state != "signed")
            if unsigned_charts:
                raise ValidationError("Solo pueden compartirse odontogramas firmados.")
            unfinished_images = referral.image_ids.filtered(
                lambda item: item.state not in {"final", "archived"}
            )
            if unfinished_images:
                raise ValidationError("Solo pueden compartirse imágenes clínicas finalizadas.")
            unapproved_plans = referral.treatment_plan_ids.filtered(
                lambda item: item.state not in {"approved", "in_progress", "completed"}
            )
            if unapproved_plans:
                raise ValidationError("Solo pueden compartirse planes aprobados.")
            has_restricted = bool(
                referral.history_entry_ids.filtered(
                    lambda item: item.sensitivity == "restricted"
                )
                or referral.image_ids.filtered(
                    lambda item: item.sensitivity == "restricted"
                )
            )
            if has_restricted and not referral.restricted_data_justification:
                raise ValidationError(
                    "Justifique por qué la información restringida es necesaria para esta referencia."
                )

    def _scope_is_empty(self):
        self.ensure_one()
        return not any(
            [
                self.share_alerts,
                self.history_entry_ids,
                self.encounter_ids,
                self.odontogram_ids,
                self.image_ids,
                self.treatment_plan_ids,
            ]
        )

    def _validate_ready(self):
        self.ensure_one()
        if not self.recipient_email and not self.recipient_mobile:
            raise ValidationError("Registre el correo o teléfono del profesional receptor.")
        if self._scope_is_empty():
            raise ValidationError("Seleccione únicamente la información clínica necesaria.")
        self._check_scope_relations()

    def _scope_payload(self):
        self.ensure_one()
        return {
            "record": self.clinical_record_id.id,
            "patient": self.patient_id.id,
            "recipient": {
                "name": self.recipient_name,
                "email": self.recipient_email or "",
                "mobile": self.recipient_mobile or "",
                "license": self.recipient_license or "",
            },
            "purpose": self.referral_reason,
            "clinical_question": self.clinical_question or "",
            "access_level": self.access_level,
            "allow_file_download": self.allow_file_download,
            "restricted_data_justification": self.restricted_data_justification or "",
            "alerts": self.clinical_record_id.alerts if self.share_alerts else "",
            "history": [
                {
                    "id": entry.id,
                    "category": entry.category,
                    "name": entry.name,
                    "details": entry.details or "",
                    "status": entry.status,
                    "severity": entry.severity or "",
                    "start_date": fields.Date.to_string(entry.start_date),
                    "end_date": fields.Date.to_string(entry.end_date),
                    "sensitivity": entry.sensitivity,
                }
                for entry in self.history_entry_ids.sorted("id")
            ],
            "encounters": [
                {"id": item.id, "content_hash": item.content_hash}
                for item in self.encounter_ids.sorted("id")
            ],
            "odontograms": [
                {"id": item.id, "content_hash": item.content_hash}
                for item in self.odontogram_ids.sorted("id")
            ],
            "images": [
                {"id": item.id, "file_hash": item.file_hash}
                for item in self.image_ids.sorted("id")
            ],
            "treatment_plans": [
                {"id": item.id, "content_hash": item.content_hash}
                for item in self.treatment_plan_ids.sorted("id")
            ],
        }

    def _calculate_scope_hash(self):
        self.ensure_one()
        serialized = json.dumps(
            self._scope_payload(), ensure_ascii=False, sort_keys=True
        ).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def _scope_matches(self):
        self.ensure_one()
        return bool(
            self.scope_content_hash
            and hmac.compare_digest(
                self.scope_content_hash, self._calculate_scope_hash()
            )
        )

    def _invalidate_changed_scope(self):
        self.ensure_one()
        if self.state not in {"awaiting_consent", "active"}:
            return
        was_awaiting = self.state == "awaiting_consent"
        self.with_context(allow_referral_transition=True).write(
            {
                "state": "invalidated",
                "access_token_hash": False,
                "otp_hash": False,
                "consent_access_token_hash": False,
                "consent_otp_hash": False,
            }
        )
        if was_awaiting and self.consent_id.state in {"draft", "pending"}:
            self.consent_id.sudo().action_reject()
        self._log_access(
            "scope_invalidated",
            False,
            "El contenido clínico seleccionado cambió después del consentimiento",
        )
        self.clinical_record_id._log_event(
            "referral_invalidated",
            f"Referencia invalidada por cambio clínico: {self.name}",
            source_record=self,
        )

    def write(self, vals):
        internal_fields = {
            "state",
            "scope_content_hash",
            "authorized_at",
            "authorized_by_user_id",
            "activated_at",
            "expires_at",
            "access_count",
            "last_access_at",
            "access_token_hash",
            "access_token_hint",
            "otp_hash",
            "otp_attempts",
            "otp_locked_until",
            "consent_access_token_hash",
            "consent_access_token_hint",
            "consent_otp_hash",
            "consent_otp_attempts",
            "consent_otp_locked_until",
            "consent_expires_at",
            "revoked_at",
            "revoked_by_user_id",
        }
        protected_fields = {
            "clinical_record_id",
            "referring_professional_id",
            "recipient_professional_id",
            "recipient_name",
            "recipient_email",
            "recipient_mobile",
            "recipient_license",
            "recipient_specialty",
            "referral_reason",
            "clinical_question",
            "share_alerts",
            "history_entry_ids",
            "encounter_ids",
            "odontogram_ids",
            "image_ids",
            "treatment_plan_ids",
            "restricted_data_justification",
            "access_level",
            "allow_file_download",
            "valid_days",
            "max_access_count",
            "consent_template_id",
            "consent_id",
        }
        if not self.env.context.get("allow_referral_transition"):
            if internal_fields.intersection(vals):
                raise UserError("Utilice las acciones controladas de la referencia.")
            for referral in self:
                if referral.state != "draft" and protected_fields.intersection(vals):
                    raise UserError(
                        "El alcance quedó congelado al solicitar el consentimiento. "
                        "Cree otra referencia si necesita modificarlo."
                    )
        return super().write(vals)

    def unlink(self):
        if any(referral.state != "draft" for referral in self):
            raise UserError("Solo pueden eliminarse referencias en borrador.")
        return super().unlink()

    def action_request_consent(self):
        for referral in self:
            if referral.state != "draft":
                raise UserError("Solo una referencia en borrador puede solicitar consentimiento.")
            referral._validate_ready()
            if not referral.consent_template_id:
                raise ValidationError("Seleccione una plantilla de consentimiento para referencia.")
            consent = self.env["odental.patient.consent"].create(
                {
                    "clinical_record_id": referral.clinical_record_id.id,
                    "professional_id": referral.referring_professional_id.id,
                    "template_id": referral.consent_template_id.id,
                    "scope_summary": referral.scope_summary,
                    "valid_until": fields.Date.context_today(referral)
                    + timedelta(days=referral.valid_days),
                }
            )
            consent.action_request()
            referral.with_context(allow_referral_transition=True).write(
                {
                    "consent_id": consent.id,
                    "scope_content_hash": referral._calculate_scope_hash(),
                    "state": "awaiting_consent",
                }
            )
            referral.clinical_record_id._log_event(
                "referral_consent_requested",
                f"Consentimiento solicitado para {referral.name}",
                source_record=referral,
            )
            token, code, access_url, expires_at = referral._issue_consent_credentials()
            wizard = self.env["odental.referral.credentials.wizard"].create(
                {
                    "referral_id": referral.id,
                    "credential_purpose": "patient",
                    "access_url": access_url,
                    "one_time_code": code,
                    "expires_at": expires_at,
                }
            )
            return {
                "type": "ir.actions.act_window",
                "res_model": "odental.referral.credentials.wizard",
                "res_id": wizard.id,
                "view_mode": "form",
                "target": "new",
            }
        return True

    def action_view_consent(self):
        self.ensure_one()
        if not self.consent_id:
            raise UserError("Esta referencia todavía no posee un consentimiento.")
        return {
            "type": "ir.actions.act_window",
            "res_model": "odental.patient.consent",
            "res_id": self.consent_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_reissue_consent_credentials(self):
        self.ensure_one()
        self._check_activation_authority()
        if self.state != "awaiting_consent" or self.consent_id.state != "pending":
            raise UserError("Este consentimiento ya no admite credenciales nuevas.")
        if not self._scope_matches():
            raise ValidationError(
                "La información clínica cambió y requiere una referencia nueva."
            )
        token, code, access_url, expires_at = self._issue_consent_credentials()
        wizard = self.env["odental.referral.credentials.wizard"].create(
            {
                "referral_id": self.id,
                "credential_purpose": "patient",
                "access_url": access_url,
                "one_time_code": code,
                "expires_at": expires_at,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "odental.referral.credentials.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def _check_activation_authority(self):
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError("Solo un administrador clínico puede habilitar acceso externo.")

    def _consent_is_current(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        return bool(
            self.consent_id
            and self.consent_id.state == "signed"
            and (not self.consent_id.valid_from or self.consent_id.valid_from <= today)
            and (not self.consent_id.valid_until or self.consent_id.valid_until >= today)
        )

    @staticmethod
    def _token_digest(token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _otp_digest(token, code):
        return hashlib.sha256(f"{token}:{code}".encode("utf-8")).hexdigest()

    def _issue_consent_credentials(self):
        self.ensure_one()
        token = secrets.token_urlsafe(32)
        code = f"{secrets.randbelow(1000000):06d}"
        expires_at = fields.Datetime.now() + timedelta(hours=48)
        self.with_context(allow_referral_transition=True).write(
            {
                "consent_access_token_hash": self._token_digest(token),
                "consent_access_token_hint": f"{token[:4]}…{token[-4:]}",
                "consent_otp_hash": self._otp_digest(token, code),
                "consent_otp_attempts": 0,
                "consent_otp_locked_until": False,
                "consent_expires_at": expires_at,
            }
        )
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return token, code, f"{base_url}/odental/referral/consent/{token}", expires_at

    @api.model
    def _find_by_consent_token(self, raw_token):
        if not raw_token:
            return self.browse()
        digest = self._token_digest(raw_token)
        referral = self.sudo().search(
            [
                ("consent_access_token_hash", "=", digest),
                ("state", "=", "awaiting_consent"),
            ],
            limit=1,
        )
        if not referral:
            return referral
        referral._expire_access()
        if (
            referral.state != "awaiting_consent"
            or referral.consent_id.state != "pending"
        ):
            return self.browse()
        return referral

    def _verify_consent_otp(
        self, raw_token, code, ip_address=False, user_agent=False
    ):
        self.ensure_one()
        self.env.cr.execute(
            "SELECT id FROM odental_referral WHERE id = %s FOR UPDATE", [self.id]
        )
        self.invalidate_recordset(
            ["consent_otp_hash", "consent_otp_attempts", "consent_otp_locked_until"]
        )
        now = fields.Datetime.now()
        if self.consent_otp_locked_until and self.consent_otp_locked_until > now:
            self._log_access(
                "consent_otp_locked",
                False,
                "Intento de consentimiento durante bloqueo temporal",
                ip_address,
                user_agent,
            )
            return False, "Demasiados intentos. Espere 15 minutos antes de reintentar."
        candidate = self._otp_digest(raw_token, (code or "").strip())
        if not self.consent_otp_hash or not hmac.compare_digest(
            candidate, self.consent_otp_hash
        ):
            attempts = self.consent_otp_attempts + 1
            values = {"consent_otp_attempts": attempts}
            if attempts >= 5:
                values.update(
                    {
                        "consent_otp_locked_until": now + timedelta(minutes=15),
                        "consent_otp_attempts": 0,
                    }
                )
            self.with_context(allow_referral_transition=True).write(values)
            self._log_access(
                "consent_otp_failed",
                False,
                "Código de consentimiento incorrecto",
                ip_address,
                user_agent,
            )
            return False, "Código incorrecto. Verifique la información recibida."
        self.with_context(allow_referral_transition=True).write(
            {
                "consent_otp_hash": False,
                "consent_otp_attempts": 0,
                "consent_otp_locked_until": False,
            }
        )
        self._log_access(
            "consent_otp_verified",
            True,
            "Identidad del firmante validada mediante segundo factor",
            ip_address,
            user_agent,
        )
        return True, False

    def _portal_sign_consent(
        self,
        signer_name,
        signer_identification=False,
        signer_type="patient",
        ip_address=False,
        user_agent=False,
    ):
        self.ensure_one()
        if self.state != "awaiting_consent" or self.consent_id.state != "pending":
            raise UserError("Este consentimiento ya no está disponible para firma.")
        if self.consent_otp_hash:
            raise UserError("Primero debe verificarse el código temporal del firmante.")
        if not self._scope_matches():
            self._invalidate_changed_scope()
            raise UserError("La información clínica cambió y requiere un consentimiento nuevo.")
        signer_name = (signer_name or "").strip()
        signer_identification = (signer_identification or "").strip()
        if not signer_name:
            raise ValidationError("Indique el nombre completo del firmante.")
        if not signer_identification:
            raise ValidationError("Indique la identificación del firmante.")
        if signer_type not in {"patient", "representative"}:
            raise ValidationError("El tipo de firmante no es válido.")
        verification_reference = (
            f"referral-consent:{self.id}:{fields.Datetime.to_string(fields.Datetime.now())}:"
            f"{ip_address or ''}:{(user_agent or '')[:500]}"
        )
        consent = self.consent_id.sudo()
        consent.write(
            {
                "signer_type": signer_type,
                "signer_name": signer_name,
                "signer_identification": signer_identification,
                "verification_method": "secure_portal",
                "verification_reference": hashlib.sha256(
                    verification_reference.encode("utf-8")
                ).hexdigest(),
            }
        )
        consent.action_sign()
        self.with_context(allow_referral_transition=True).write(
            {
                "consent_access_token_hash": False,
                "consent_otp_hash": False,
            }
        )
        self._log_access(
            "consent_signed",
            True,
            "Consentimiento digital firmado por el paciente",
            ip_address,
            user_agent,
        )
        return consent

    def _issue_credentials(self):
        self.ensure_one()
        token = secrets.token_urlsafe(32)
        code = f"{secrets.randbelow(1000000):06d}"
        now = fields.Datetime.now()
        expires_at = now + timedelta(days=self.valid_days)
        self.with_context(allow_referral_transition=True).write(
            {
                "access_token_hash": self._token_digest(token),
                "access_token_hint": f"{token[:4]}…{token[-4:]}",
                "otp_hash": self._otp_digest(token, code),
                "otp_attempts": 0,
                "otp_locked_until": False,
                "expires_at": expires_at,
            }
        )
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return token, code, f"{base_url}/odental/referral/{token}", expires_at

    def action_activate(self):
        self.ensure_one()
        self._check_activation_authority()
        if self.state != "awaiting_consent":
            raise UserError("La referencia debe estar esperando el consentimiento del paciente.")
        self._validate_ready()
        if not self._scope_matches():
            raise ValidationError(
                "La información clínica cambió después de solicitar el consentimiento. "
                "Cree una nueva referencia con el alcance actualizado."
            )
        if not self._consent_is_current():
            raise ValidationError("El paciente debe firmar un consentimiento vigente para esta referencia.")
        token, code, access_url, expires_at = self._issue_credentials()
        self.with_context(allow_referral_transition=True).write(
            {
                "state": "active",
                "authorized_at": fields.Datetime.now(),
                "authorized_by_user_id": self.env.user.id,
                "activated_at": fields.Datetime.now(),
                "consent_access_token_hash": False,
                "consent_otp_hash": False,
            }
        )
        self.clinical_record_id._log_event(
            "referral_activated",
            f"Acceso temporal activado: {self.name}",
            source_record=self,
        )
        wizard = self.env["odental.referral.credentials.wizard"].create(
            {
                "referral_id": self.id,
                "credential_purpose": "recipient",
                "access_url": access_url,
                "one_time_code": code,
                "expires_at": expires_at,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "odental.referral.credentials.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_reissue_credentials(self):
        self.ensure_one()
        self._check_activation_authority()
        if self.state != "active":
            raise UserError("Solo puede renovarse el acceso de una referencia activa.")
        if not self._scope_matches() or not self._consent_is_current():
            raise ValidationError(
                "El alcance clínico o el consentimiento ya no permiten renovar el acceso."
            )
        token, code, access_url, expires_at = self._issue_credentials()
        wizard = self.env["odental.referral.credentials.wizard"].create(
            {
                "referral_id": self.id,
                "credential_purpose": "recipient",
                "access_url": access_url,
                "one_time_code": code,
                "expires_at": expires_at,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "odental.referral.credentials.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_revoke(self):
        for referral in self:
            referral._check_activation_authority()
            if referral.state not in REFERRAL_ACTIVE_STATES:
                raise UserError("Solo puede revocarse una referencia con acceso vigente.")
            if not referral.revocation_reason:
                raise ValidationError("Indique el motivo de la revocación.")
            referral.with_context(allow_referral_transition=True).write(
                {
                    "state": "revoked",
                    "revoked_at": fields.Datetime.now(),
                    "revoked_by_user_id": self.env.user.id,
                    "access_token_hash": False,
                    "otp_hash": False,
                }
            )
            referral.clinical_record_id._log_event(
                "referral_revoked",
                f"Acceso temporal revocado: {referral.name}",
                source_record=referral,
            )

    def action_reject(self):
        for referral in self:
            if referral.state not in {"draft", "awaiting_consent"}:
                raise UserError("Esta referencia ya no puede rechazarse.")
            if referral.consent_id.state in {"draft", "pending"}:
                referral.consent_id.action_reject()
            referral.with_context(allow_referral_transition=True).write(
                {
                    "state": "rejected",
                    "consent_access_token_hash": False,
                    "consent_otp_hash": False,
                }
            )
            referral.clinical_record_id._log_event(
                "referral_rejected",
                f"Referencia rechazada: {referral.name}",
                source_record=referral,
            )

    def action_close(self):
        for referral in self:
            referral._check_activation_authority()
            if referral.state not in {"active", "report_submitted", "expired", "invalidated"}:
                raise UserError("Esta referencia no está lista para cerrarse.")
            referral.with_context(allow_referral_transition=True).write(
                {"state": "closed", "access_token_hash": False, "otp_hash": False}
            )
            referral.clinical_record_id._log_event(
                "referral_closed",
                f"Referencia cerrada: {referral.name}",
                source_record=referral,
            )

    def _expire_access(self):
        now = fields.Datetime.now()
        for referral in self.filtered(
            lambda item: item.state in {"awaiting_consent", "active"}
            and not item._scope_matches()
        ):
            referral._invalidate_changed_scope()
        for referral in self.filtered(
            lambda item: item.state == "awaiting_consent"
            and item.consent_expires_at
            and item.consent_expires_at <= now
        ):
            if referral.consent_id.state in {"draft", "pending"}:
                referral.consent_id.sudo().action_reject()
            referral.with_context(allow_referral_transition=True).write(
                {
                    "state": "expired",
                    "consent_access_token_hash": False,
                    "consent_otp_hash": False,
                }
            )
            referral.clinical_record_id._log_event(
                "referral_expired",
                f"Solicitud de consentimiento vencida: {referral.name}",
                source_record=referral,
            )
        for referral in self.filtered(
            lambda item: item.state in REFERRAL_ACTIVE_STATES
            and (
                (item.expires_at and item.expires_at <= now)
                or not item._consent_is_current()
                or item.access_count >= item.max_access_count
            )
        ):
            referral.with_context(allow_referral_transition=True).write(
                {"state": "expired", "access_token_hash": False, "otp_hash": False}
            )
            referral.clinical_record_id._log_event(
                "referral_expired",
                f"Acceso temporal vencido: {referral.name}",
                source_record=referral,
            )

    @api.model
    def _cron_expire_referrals(self):
        referrals = self.search(
            [("state", "in", ["awaiting_consent", "active"])]
        )
        referrals._expire_access()

    @api.model
    def _find_by_token(self, raw_token):
        if not raw_token:
            return self.browse()
        digest = self._token_digest(raw_token)
        referral = self.sudo().search(
            [("access_token_hash", "=", digest), ("state", "in", list(REFERRAL_ACTIVE_STATES))],
            limit=1,
        )
        if referral:
            referral._expire_access()
        return referral if referral.state in REFERRAL_ACTIVE_STATES else self.browse()

    def _verify_otp(
        self, raw_token, code, ip_address=False, user_agent=False
    ):
        self.ensure_one()
        self.env.cr.execute(
            "SELECT id FROM odental_referral WHERE id = %s FOR UPDATE", [self.id]
        )
        self.invalidate_recordset(["otp_hash", "otp_attempts", "otp_locked_until"])
        now = fields.Datetime.now()
        if self.otp_locked_until and self.otp_locked_until > now:
            self._log_access(
                "otp_locked",
                False,
                "Intento durante bloqueo temporal",
                ip_address,
                user_agent,
            )
            return False, "Demasiados intentos. Espere 15 minutos antes de reintentar."
        candidate = self._otp_digest(raw_token, (code or "").strip())
        if not self.otp_hash or not hmac.compare_digest(candidate, self.otp_hash):
            attempts = self.otp_attempts + 1
            values = {"otp_attempts": attempts}
            if attempts >= 5:
                values.update(
                    {"otp_locked_until": now + timedelta(minutes=15), "otp_attempts": 0}
                )
            self.with_context(allow_referral_transition=True).write(values)
            self._log_access(
                "otp_failed",
                False,
                "Código de verificación incorrecto",
                ip_address,
                user_agent,
            )
            return False, "Código incorrecto. Verifique la información recibida."
        self.with_context(allow_referral_transition=True).write(
            {"otp_hash": False, "otp_attempts": 0, "otp_locked_until": False}
        )
        self._log_access(
            "otp_verified",
            True,
            "Identidad validada mediante segundo factor",
            ip_address,
            user_agent,
        )
        return True, False

    def _register_view(self, ip_address=False, user_agent=False):
        self.ensure_one()
        self.env.cr.execute(
            "SELECT id FROM odental_referral WHERE id = %s FOR UPDATE", [self.id]
        )
        self.invalidate_recordset(
            ["state", "expires_at", "access_count", "max_access_count"]
        )
        self._expire_access()
        if self.state not in REFERRAL_ACTIVE_STATES:
            return False
        self.with_context(allow_referral_transition=True).write(
            {"access_count": self.access_count + 1, "last_access_at": fields.Datetime.now()}
        )
        self._log_access("view", True, "Información clínica temporal consultada", ip_address, user_agent)
        self.clinical_record_id._log_event(
            "referral_accessed",
            f"Referencia consultada por receptor externo: {self.name}",
            source_record=self,
        )
        return True

    def _log_access(
        self, event_type, success, details=False, ip_address=False, user_agent=False
    ):
        self.ensure_one()
        return self.env["odental.referral.access.log"].sudo().create(
            {
                "referral_id": self.id,
                "event_type": event_type,
                "success": success,
                "details": details,
                "ip_address": ip_address,
                "user_agent": (user_agent or "")[:500],
            }
        )


class ODentalReferralReport(models.Model):
    _name = "odental.referral.report"
    _description = "Informe externo de referencia O Dental"
    _order = "submitted_at desc, id desc"
    _rec_name = "author_name"

    referral_id = fields.Many2one(
        "odental.referral", required=True, ondelete="restrict", index=True
    )
    organization_id = fields.Many2one(
        related="referral_id.organization_id", store=True, index=True
    )
    patient_id = fields.Many2one(related="referral_id.patient_id", store=True, index=True)
    author_name = fields.Char(required=True, readonly=True)
    summary = fields.Text(string="Informe y recomendaciones", required=True, readonly=True)
    file_data = fields.Binary(string="Documento adjunto", attachment=True, readonly=True)
    filename = fields.Char(readonly=True)
    file_hash = fields.Char(string="Huella SHA-256", readonly=True, index=True)
    content_hash = fields.Char(
        string="Huella del informe", required=True, readonly=True, copy=False, index=True
    )
    submitted_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    state = fields.Selection(
        [("submitted", "Pendiente de revisión"), ("reviewed", "Revisado"), ("rejected", "Descartado")],
        required=True,
        default="submitted",
        readonly=True,
        index=True,
    )
    review_notes = fields.Text(string="Notas de revisión")
    reviewed_at = fields.Datetime(readonly=True)
    reviewed_by_user_id = fields.Many2one("res.users", readonly=True)

    _sql_constraints = [
        (
            "referral_unique_report",
            "unique(referral_id)",
            "Esta referencia ya posee un informe externo.",
        )
    ]

    @api.model
    def _file_hash(self, encoded_file):
        if not encoded_file:
            return False
        try:
            raw = base64.b64decode(encoded_file, validate=True)
        except (binascii.Error, ValueError, TypeError) as error:
            raise ValidationError("El informe adjunto no es un archivo válido.") from error
        if len(raw) > 10 * 1024 * 1024:
            raise ValidationError("El informe adjunto no puede superar 10 MB.")
        return hashlib.sha256(raw).hexdigest()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            referral = self.env["odental.referral"].browse(vals.get("referral_id"))
            if not referral or referral.state != "active":
                raise ValidationError("La referencia ya no acepta informes externos.")
            if referral.access_level != "read_report":
                raise ValidationError("La referencia no autorizó la entrega de informes.")
            if referral.report_ids:
                raise ValidationError("Esta referencia ya posee un informe externo.")
            if not (vals.get("summary") or "").strip():
                raise ValidationError("El informe debe incluir hallazgos o recomendaciones.")
            vals["summary"] = vals["summary"].strip()
            vals["author_name"] = referral.recipient_name
            vals.setdefault("submitted_at", fields.Datetime.now())
            if vals.get("file_data"):
                vals["file_hash"] = self._file_hash(vals["file_data"])
            payload = {
                "referral": referral.id,
                "author": vals["author_name"],
                "summary": vals.get("summary") or "",
                "file_hash": vals.get("file_hash") or "",
                "submitted_at": fields.Datetime.to_string(
                    fields.Datetime.to_datetime(vals["submitted_at"])
                ),
            }
            vals["content_hash"] = hashlib.sha256(
                json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()
        reports = super().create(vals_list)
        for report in reports:
            referral = report.referral_id
            referral.with_context(allow_referral_transition=True).write(
                {
                    "state": "report_submitted",
                    "access_token_hash": False,
                    "otp_hash": False,
                }
            )
            referral._log_access("report_submitted", True, "Informe externo recibido")
            referral.clinical_record_id._log_event(
                "referral_report_submitted",
                f"Informe externo recibido para {referral.name}",
                report.content_hash,
                source_record=report,
            )
        return reports

    def write(self, vals):
        immutable = {
            "referral_id",
            "author_name",
            "summary",
            "file_data",
            "filename",
            "file_hash",
            "content_hash",
            "submitted_at",
        }
        if immutable.intersection(vals):
            raise UserError("El informe externo recibido es inmutable.")
        if "state" in vals and not self.env.context.get("allow_report_review"):
            raise UserError("Utilice las acciones de revisión del informe.")
        return super().write(vals)

    def unlink(self):
        raise UserError("Los informes externos deben conservarse como evidencia clínica.")

    def _review(self, state):
        if not self.env.user.has_group("odental_core.group_odental_professional"):
            raise AccessError("Solo un profesional clínico puede revisar este informe.")
        for report in self:
            if report.state != "submitted":
                raise UserError("Este informe ya fue revisado.")
            report.with_context(allow_report_review=True).write(
                {
                    "state": state,
                    "reviewed_at": fields.Datetime.now(),
                    "reviewed_by_user_id": self.env.user.id,
                }
            )
            report.referral_id.clinical_record_id._log_event(
                "referral_report_reviewed",
                f"Informe externo revisado para {report.referral_id.name}",
                report.content_hash,
                source_record=report,
            )

    def action_mark_reviewed(self):
        self._review("reviewed")

    def action_reject_report(self):
        self._review("rejected")


class ODentalReferralAccessLog(models.Model):
    _name = "odental.referral.access.log"
    _description = "Bitácora de acceso temporal O Dental"
    _order = "occurred_at desc, id desc"
    _rec_name = "event_type"

    referral_id = fields.Many2one(
        "odental.referral", required=True, ondelete="restrict", index=True
    )
    organization_id = fields.Many2one(
        related="referral_id.organization_id", store=True, index=True
    )
    patient_id = fields.Many2one(related="referral_id.patient_id", store=True, index=True)
    occurred_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    event_type = fields.Selection(
        [
            ("otp_verified", "Código verificado"),
            ("otp_failed", "Código incorrecto"),
            ("otp_locked", "Acceso bloqueado"),
            ("consent_otp_verified", "Código del paciente verificado"),
            ("consent_otp_failed", "Código del paciente incorrecto"),
            ("consent_otp_locked", "Consentimiento bloqueado"),
            ("consent_signed", "Consentimiento digital firmado"),
            ("view", "Consulta clínica"),
            ("file_view", "Archivo visualizado"),
            ("file_download", "Archivo descargado"),
            ("report_submitted", "Informe enviado"),
            ("scope_invalidated", "Alcance clínico modificado"),
        ],
        required=True,
        readonly=True,
        index=True,
    )
    success = fields.Boolean(readonly=True)
    details = fields.Char(readonly=True)
    ip_address = fields.Char(readonly=True)
    user_agent = fields.Char(readonly=True)

    def write(self, vals):
        if not self.env.su:
            raise UserError("La bitácora de acceso no puede modificarse.")
        return super().write(vals)

    def unlink(self):
        if not self.env.su:
            raise UserError("La bitácora de acceso no puede eliminarse.")
        return super().unlink()
