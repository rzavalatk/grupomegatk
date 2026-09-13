import hashlib
import hmac
import json
import logging
import re
from datetime import timedelta
from uuid import uuid4

import requests

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


_logger = logging.getLogger(__name__)
PHONE_RE = re.compile(r"\D+")
SUPPORTED_ACTIONS = {
    "confirm": "Confirmar cita",
    "cancel": "Solicitar cancelación",
    "reschedule": "Solicitar reprogramación",
    "offer_accept": "Aceptar espacio",
    "offer_decline": "Rechazar espacio",
}


def normalize_phone(value):
    return PHONE_RE.sub("", value or "")


class ODentalWhatsAppAccount(models.Model):
    _name = "odental.whatsapp.account"
    _description = "Cuenta WhatsApp Cloud O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "organization_id, name"

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="cascade", index=True, tracking=True
    )
    phone_number_id = fields.Char(required=True, copy=False, index=True, tracking=True)
    business_account_id = fields.Char(string="WhatsApp Business Account ID", copy=False)
    display_phone = fields.Char(string="Número visible", tracking=True)
    api_base_url = fields.Char(
        required=True, default="https://graph.facebook.com", groups="odental_core.group_odental_admin"
    )
    graph_api_version = fields.Char(
        required=True, default="v23.0",
        help="Versión habilitada en la aplicación de Meta. Puede actualizarse sin cambiar código.",
    )
    webhook_key = fields.Char(required=True, default=lambda self: uuid4().hex, copy=False, readonly=True)
    webhook_url = fields.Char(compute="_compute_webhook_url")
    credentials_configured = fields.Boolean(compute="_compute_credentials_configured")
    automatic_delivery = fields.Boolean(
        default=False, tracking=True,
        help="Actívelo solo después de aprobar las plantillas y verificar el webhook en Meta.",
    )
    auto_apply_confirmations = fields.Boolean(default=True)
    auto_apply_cancellations = fields.Boolean(default=False)
    auto_apply_slot_offers = fields.Boolean(default=True)
    max_attempts = fields.Integer(default=5, required=True)
    request_timeout_seconds = fields.Integer(default=15, required=True)
    message_ids = fields.One2many(
        "odental.communication.message", "whatsapp_account_id", string="Mensajes", readonly=True
    )
    event_ids = fields.One2many(
        "odental.whatsapp.event", "account_id", string="Eventos", readonly=True
    )

    _sql_constraints = [
        ("phone_number_id_unique", "unique(phone_number_id)", "Este Phone Number ID ya está configurado."),
        ("webhook_key_unique", "unique(webhook_key)", "La clave pública del webhook debe ser única."),
    ]

    @api.depends("webhook_key")
    def _compute_webhook_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        for account in self:
            account.webhook_url = (
                f"{base_url.rstrip('/')}/odental/whatsapp/webhook/{account.webhook_key}"
                if base_url and account.webhook_key else False
            )

    def _secret_key(self, kind):
        self.ensure_one()
        if kind not in {"access_token", "app_secret", "verify_token_hash"}:
            raise ValidationError("Tipo de credencial no permitido.")
        return f"odental_whatsapp.{self.webhook_key}.{kind}"

    def _get_secret(self, kind):
        self.ensure_one()
        return self.env["ir.config_parameter"].sudo().get_param(self._secret_key(kind), "")

    def _set_secret(self, kind, value):
        self.ensure_one()
        self.env["ir.config_parameter"].sudo().set_param(self._secret_key(kind), value or "")

    def _compute_credentials_configured(self):
        for account in self:
            account.credentials_configured = account._has_credentials()

    def _has_credentials(self):
        self.ensure_one()
        return bool(
            self._get_secret("access_token")
            and self._get_secret("app_secret")
            and self._get_secret("verify_token_hash")
        )

    @api.constrains("graph_api_version", "max_attempts", "request_timeout_seconds")
    def _check_settings(self):
        for account in self:
            if not re.fullmatch(r"v\d+\.\d+", account.graph_api_version or ""):
                raise ValidationError("La versión de Graph API debe tener el formato vNN.N.")
            if not 1 <= account.max_attempts <= 10:
                raise ValidationError("Los reintentos deben estar entre 1 y 10.")
            if not 5 <= account.request_timeout_seconds <= 60:
                raise ValidationError("El tiempo de espera debe estar entre 5 y 60 segundos.")

    @api.constrains("automatic_delivery")
    def _check_delivery_credentials(self):
        for account in self:
            if account.automatic_delivery and not account._has_credentials():
                raise ValidationError(
                    "Configure token de acceso, secreto de aplicación y token de verificación antes de activar entregas."
                )

    def action_configure_credentials(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "odental.whatsapp.credentials.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_account_id": self.id},
        }

    def action_clear_credentials(self):
        if not self.env.user.has_group("odental_core.group_odental_admin"):
            raise AccessError("Solo el administrador O Dental puede borrar credenciales.")
        for account in self:
            for kind in ("access_token", "app_secret", "verify_token_hash"):
                account._set_secret(kind, "")
            account.automatic_delivery = False
        return True

    def _verify_challenge_token(self, token):
        self.ensure_one()
        expected = self._get_secret("verify_token_hash")
        received = hashlib.sha256((token or "").encode()).hexdigest()
        return bool(expected and hmac.compare_digest(expected, received))

    def _verify_signature(self, raw_body, signature_header):
        self.ensure_one()
        secret = self._get_secret("app_secret")
        if not secret or not signature_header or not signature_header.startswith("sha256="):
            return False
        expected = "sha256=" + hmac.new(
            secret.encode(), raw_body, digestmod=hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)

    def _messages_endpoint(self):
        self.ensure_one()
        return "%s/%s/%s/messages" % (
            self.api_base_url.rstrip("/"), self.graph_api_version, self.phone_number_id
        )

    def _post_message(self, payload):
        self.ensure_one()
        token = self._get_secret("access_token")
        if not token:
            raise ValidationError("La cuenta no tiene un token de acceso configurado.")
        response = requests.post(
            self._messages_endpoint(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=self.request_timeout_seconds,
        )
        try:
            data = response.json()
        except ValueError:
            data = {}
        if not response.ok:
            error = data.get("error", {}) if isinstance(data, dict) else {}
            code = error.get("code") or response.status_code
            message = str(error.get("message") or "Respuesta no válida del proveedor")[:300]
            raise UserError(f"WhatsApp rechazó el envío ({code}): {message}")
        provider_id = ((data.get("messages") or [{}])[0]).get("id")
        if not provider_id:
            raise UserError("WhatsApp aceptó la solicitud sin devolver un identificador de mensaje.")
        return provider_id


class ODentalOrganization(models.Model):
    _inherit = "odental.organization"

    whatsapp_account_ids = fields.One2many(
        "odental.whatsapp.account", "organization_id", string="Números de WhatsApp"
    )
    whatsapp_default_account_id = fields.Many2one(
        "odental.whatsapp.account", string="Número predeterminado",
        domain="[('organization_id', '=', id), ('active', '=', True)]",
    )

    @api.constrains("whatsapp_default_account_id")
    def _check_default_whatsapp_account(self):
        for organization in self:
            account = organization.whatsapp_default_account_id
            if account and account.organization_id != organization:
                raise ValidationError("El número predeterminado pertenece a otra organización.")


class ODentalPatient(models.Model):
    _inherit = "odental.patient"

    whatsapp_wa_id = fields.Char(
        string="Identificador WhatsApp", compute="_compute_whatsapp_wa_id", store=True, index=True
    )

    @api.depends("mobile")
    def _compute_whatsapp_wa_id(self):
        for patient in self:
            patient.whatsapp_wa_id = normalize_phone(patient.mobile)


class ODentalCommunicationTemplate(models.Model):
    _inherit = "odental.communication.template"

    whatsapp_template_name = fields.Char(
        string="Nombre aprobado en Meta",
        help="Nombre exacto de la plantilla aprobada en WhatsApp Manager.",
    )
    whatsapp_account_id = fields.Many2one(
        "odental.whatsapp.account", string="Número de salida",
        domain="[('organization_id', '=', organization_id), ('active', '=', True)]",
        help="Permite usar números distintos para agenda, cobros u otras comunicaciones.",
    )
    whatsapp_language_code = fields.Char(default="es", string="Idioma Meta")
    whatsapp_template_status = fields.Selection(
        [("draft", "Borrador"), ("pending", "En revisión"),
         ("approved", "Aprobada"), ("rejected", "Rechazada")],
        default="draft", required=True,
    )
    whatsapp_body_parameter_names = fields.Char(
        string="Variables de cuerpo",
        help="Variables separadas por coma, en el orden aprobado por Meta; por ejemplo patient_name,appointment_datetime.",
    )
    whatsapp_action_mode = fields.Selection(
        [("none", "Sin botones"), ("appointment", "Confirmar/cancelar/reprogramar"),
         ("slot_offer", "Aceptar/rechazar espacio")],
        default="none", required=True,
    )

    @api.constrains("channel", "whatsapp_template_status", "whatsapp_template_name", "whatsapp_body_parameter_names")
    def _check_whatsapp_template(self):
        for template in self:
            if template.channel != "whatsapp":
                continue
            if template.whatsapp_template_status == "approved" and not template.whatsapp_template_name:
                raise ValidationError("Una plantilla aprobada necesita el nombre registrado en Meta.")
            if template.whatsapp_account_id and template.whatsapp_account_id.organization_id != template.organization_id:
                raise ValidationError("El número de salida pertenece a otra organización.")
            names = template._whatsapp_parameter_names()
            allowed = {
                "patient_name", "service_name", "professional_name", "organization_name",
                "appointment_datetime", "offer_expires_at",
            }
            unknown = set(names) - allowed
            if unknown:
                raise ValidationError("Variables WhatsApp no permitidas: %s" % ", ".join(sorted(unknown)))

    def _whatsapp_parameter_names(self):
        self.ensure_one()
        return [item.strip() for item in (self.whatsapp_body_parameter_names or "").split(",") if item.strip()]


class ODentalCommunicationMessage(models.Model):
    _inherit = "odental.communication.message"

    state = fields.Selection(selection_add=[("sending", "Enviando"), ("read", "Leído")], ondelete={
        "sending": "set default", "read": "set default",
    })
    whatsapp_account_id = fields.Many2one(
        "odental.whatsapp.account", readonly=True, copy=False, index=True
    )
    whatsapp_provider_message_id = fields.Char(readonly=True, copy=False, index=True)
    whatsapp_payload_digest = fields.Char(readonly=True, copy=False)
    whatsapp_next_retry_at = fields.Datetime(readonly=True, copy=False, index=True)
    whatsapp_action_token_ids = fields.One2many(
        "odental.whatsapp.action.token", "message_id", string="Acciones", readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("channel") == "whatsapp" and not vals.get("whatsapp_account_id"):
                organization = self.env["odental.organization"].browse(vals.get("organization_id"))
                template = self.env["odental.communication.template"].search([
                    ("organization_id", "=", organization.id),
                    ("message_type", "=", vals.get("message_type")),
                    ("channel", "=", "whatsapp"), ("active", "=", True),
                ], limit=1)
                account = template.whatsapp_account_id or organization.whatsapp_default_account_id
                vals["whatsapp_account_id"] = account.id or False
        return super().create(vals_list)

    def action_requeue(self):
        result = super().action_requeue()
        for message in self.filtered(lambda item: item.channel == "whatsapp"):
            template = message._whatsapp_template()
            account = template.whatsapp_account_id or message.organization_id.whatsapp_default_account_id
            message.with_context(odental_whatsapp_transition=True).write({
                "whatsapp_account_id": account.id or False,
            })
        return result

    def write(self, vals):
        protected = {
            "whatsapp_account_id", "whatsapp_provider_message_id",
            "whatsapp_payload_digest", "whatsapp_next_retry_at",
        }
        if protected.intersection(vals) and not self.env.context.get("odental_whatsapp_transition"):
            raise UserError("Los datos del proveedor solo cambian desde el conector WhatsApp.")
        return super().write(vals)

    def _whatsapp_template(self):
        self.ensure_one()
        return self.env["odental.communication.template"].search([
            ("organization_id", "=", self.organization_id.id),
            ("message_type", "=", self.message_type),
            ("channel", "=", "whatsapp"),
            ("active", "=", True),
            ("whatsapp_template_status", "=", "approved"),
        ], limit=1)

    def _whatsapp_context_values(self):
        self.ensure_one()
        if not self.appointment_id:
            return {}
        return self.appointment_id._message_values(slot_offer=self.slot_offer_id)

    def _new_action_token(self, action):
        self.ensure_one()
        existing = self.whatsapp_action_token_ids.filtered(
            lambda item: item.action == action and item.state == "active"
        )[:1]
        if existing:
            return existing.token
        token = self.env["odental.whatsapp.action.token"].sudo().with_context(
            odental_whatsapp_token_create=True
        ).create({"message_id": self.id, "action": action})
        return token.token

    def _whatsapp_payload(self):
        self.ensure_one()
        template = self._whatsapp_template()
        if not template:
            raise ValidationError(
                "Configure y marque como aprobada la plantilla Meta para este tipo de mensaje."
            )
        values = self._whatsapp_context_values()
        components = []
        names = template._whatsapp_parameter_names()
        if names:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": str(values.get(name, ""))} for name in names],
            })
        actions = []
        if template.whatsapp_action_mode == "appointment" and self.appointment_id:
            actions = ["confirm", "cancel", "reschedule"]
        elif template.whatsapp_action_mode == "slot_offer" and self.slot_offer_id:
            actions = ["offer_accept", "offer_decline"]
        for index, action in enumerate(actions):
            components.append({
                "type": "button", "sub_type": "quick_reply", "index": str(index),
                "parameters": [{"type": "payload", "payload": self._new_action_token(action)}],
            })
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalize_phone(self.recipient),
            "type": "template",
            "template": {
                "name": template.whatsapp_template_name,
                "language": {"code": template.whatsapp_language_code or "es"},
                **({"components": components} if components else {}),
            },
        }

    def _whatsapp_fail(self, error):
        self.ensure_one()
        account = self.whatsapp_account_id
        attempts = self.attempt_count + 1
        exhausted = not account or attempts >= account.max_attempts
        delay_minutes = min(60, 2 ** min(attempts, 6))
        self.with_context(
            odental_message_transition=True, odental_whatsapp_transition=True
        ).write({
            "state": "blocked" if exhausted else "failed",
            "attempt_count": attempts,
            "last_error": str(error)[:500],
            "blocking_reason": "Máximo de reintentos alcanzado." if exhausted else False,
            "whatsapp_next_retry_at": False if exhausted else fields.Datetime.now() + timedelta(minutes=delay_minutes),
        })

    def action_send_whatsapp(self):
        for message in self:
            if message.channel != "whatsapp" or message.state not in {"queued", "failed"}:
                continue
            account = message.whatsapp_account_id
            if not account or not account.active or not account.automatic_delivery:
                message._whatsapp_fail("No hay una cuenta WhatsApp activa y habilitada para entrega.")
                continue
            if not message.patient_id.appointment_messages_consent:
                message._whatsapp_fail("El paciente revocó el consentimiento de comunicaciones.")
                continue
            try:
                payload = message._whatsapp_payload()
                digest = hashlib.sha256(
                    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()
                message.with_context(
                    odental_message_transition=True, odental_whatsapp_transition=True
                ).write({"state": "sending", "last_error": False})
                provider_id = account._post_message(payload)
                message.with_context(
                    odental_message_transition=True, odental_whatsapp_transition=True
                ).write({
                    "state": "sent", "sent_at": fields.Datetime.now(),
                    "attempt_count": message.attempt_count + 1,
                    "external_reference": provider_id,
                    "whatsapp_provider_message_id": provider_id,
                    "whatsapp_payload_digest": digest,
                    "whatsapp_next_retry_at": False,
                })
            except (requests.RequestException, UserError, ValidationError) as exc:
                _logger.warning("Fallo de entrega WhatsApp para %s: %s", message.name, exc)
                message._whatsapp_fail(exc)
        return True

    @api.model
    def _cron_send_whatsapp(self):
        now = fields.Datetime.now()
        messages = self.search([
            ("channel", "=", "whatsapp"),
            ("state", "in", ("queued", "failed")),
            ("scheduled_at", "<=", now),
            "|", ("whatsapp_next_retry_at", "=", False),
            ("whatsapp_next_retry_at", "<=", now),
        ], order="scheduled_at, id", limit=50)
        messages.action_send_whatsapp()

    def _apply_provider_status(self, status, error_message=False):
        self.ensure_one()
        values = {}
        if status == "sent" and self.state == "sending":
            values = {"state": "sent", "sent_at": self.sent_at or fields.Datetime.now()}
        elif status == "delivered" and self.state in {"sending", "sent"}:
            values = {"state": "delivered", "delivered_at": fields.Datetime.now()}
        elif status == "read" and self.state in {"sending", "sent", "delivered"}:
            values = {"state": "read", "delivered_at": self.delivered_at or fields.Datetime.now()}
        elif status == "failed" and self.state not in {"cancelled", "blocked"}:
            self._whatsapp_fail(error_message or "Entrega rechazada por WhatsApp.")
            return
        if values:
            self.with_context(
                odental_message_transition=True, odental_whatsapp_transition=True
            ).write(values)


class ODentalWhatsAppActionToken(models.Model):
    _name = "odental.whatsapp.action.token"
    _description = "Acción interactiva WhatsApp O Dental"
    _order = "id desc"

    token = fields.Char(required=True, default=lambda self: uuid4().hex, readonly=True, copy=False, index=True)
    message_id = fields.Many2one(
        "odental.communication.message", required=True, ondelete="cascade", readonly=True, index=True
    )
    organization_id = fields.Many2one(related="message_id.organization_id", store=True, index=True)
    action = fields.Selection(list(SUPPORTED_ACTIONS.items()), required=True, readonly=True)
    state = fields.Selection(
        [("active", "Activo"), ("used", "Utilizado"), ("revoked", "Revocado")],
        default="active", required=True, readonly=True, index=True,
    )
    used_at = fields.Datetime(readonly=True)

    _sql_constraints = [("token_unique", "unique(token)", "El token de respuesta debe ser único.")]

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("odental_whatsapp_token_create"):
            raise AccessError("Los tokens solo se crean al preparar mensajes interactivos.")
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get("odental_whatsapp_token_transition"):
            raise UserError("Los tokens de respuesta son inmutables.")
        return super().write(vals)

    def unlink(self):
        raise UserError("Los tokens de respuesta no se eliminan.")

    def _consume(self, wa_id):
        self.ensure_one()
        if self.state != "active":
            raise ValidationError("Esta respuesta ya fue utilizada o revocada.")
        if self.message_id.patient_id.whatsapp_wa_id != normalize_phone(wa_id):
            raise AccessError("La respuesta no pertenece al paciente destinatario.")
        request_record = self.env["odental.whatsapp.request"].sudo().with_context(
            odental_whatsapp_request_create=True
        ).create({
            "organization_id": self.organization_id.id,
            "account_id": self.message_id.whatsapp_account_id.id,
            "patient_id": self.message_id.patient_id.id,
            "appointment_id": self.message_id.appointment_id.id,
            "slot_offer_id": self.message_id.slot_offer_id.id,
            "source_message_id": self.message_id.id,
            "action": self.action,
        })
        self.with_context(odental_whatsapp_token_transition=True).write({
            "state": "used", "used_at": fields.Datetime.now(),
        })
        request_record._auto_apply_if_allowed()
        return request_record


class ODentalWhatsAppRequest(models.Model):
    _name = "odental.whatsapp.request"
    _description = "Solicitud recibida por WhatsApp O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "received_at desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    organization_id = fields.Many2one("odental.organization", required=True, readonly=True, index=True)
    account_id = fields.Many2one("odental.whatsapp.account", required=True, readonly=True, index=True)
    patient_id = fields.Many2one("odental.patient", required=True, readonly=True, index=True)
    appointment_id = fields.Many2one("odental.appointment", readonly=True, index=True)
    slot_offer_id = fields.Many2one("odental.slot.offer", readonly=True, index=True)
    source_message_id = fields.Many2one("odental.communication.message", readonly=True, index=True)
    action = fields.Selection(list(SUPPORTED_ACTIONS.items()), required=True, readonly=True, tracking=True)
    requested_start_datetime = fields.Datetime(
        string="Nueva fecha solicitada", tracking=True,
        help="Recepción puede completar esta fecha antes de aplicar una reprogramación.",
    )
    received_at = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
    state = fields.Selection(
        [("pending", "Pendiente"), ("applied", "Aplicada"), ("rejected", "Rechazada"),
         ("failed", "No aplicada")], default="pending", required=True, readonly=True, tracking=True,
    )
    processed_at = fields.Datetime(readonly=True)
    processed_by = fields.Many2one("res.users", readonly=True)
    processing_note = fields.Char(readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("odental_whatsapp_request_create"):
            raise AccessError("Las solicitudes solo se crean desde respuestas verificadas de WhatsApp.")
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("odental.whatsapp.request") or "Nuevo"
        return super().create(vals_list)

    def write(self, vals):
        protected = {"state", "processed_at", "processed_by", "processing_note"}
        if protected.intersection(vals) and not self.env.context.get("odental_whatsapp_request_transition"):
            raise UserError("Utilice las acciones de la solicitud.")
        return super().write(vals)

    @api.constrains("organization_id", "account_id", "patient_id", "appointment_id", "slot_offer_id")
    def _check_scope(self):
        for record in self:
            if record.account_id.organization_id != record.organization_id:
                raise ValidationError("La cuenta WhatsApp pertenece a otra organización.")
            if record.patient_id.organization_id != record.organization_id:
                raise ValidationError("El paciente pertenece a otra organización.")
            if record.appointment_id and record.appointment_id.patient_id != record.patient_id:
                raise ValidationError("La cita no corresponde al paciente.")
            if record.slot_offer_id and record.slot_offer_id.patient_id != record.patient_id:
                raise ValidationError("La oferta no corresponde al paciente.")

    def _auto_apply_if_allowed(self):
        for record in self.filtered(lambda item: item.state == "pending"):
            account = record.account_id
            allowed = (
                (record.action == "confirm" and account.auto_apply_confirmations)
                or (record.action == "cancel" and account.auto_apply_cancellations)
                or (record.action in {"offer_accept", "offer_decline"} and account.auto_apply_slot_offers)
            )
            if allowed:
                record.action_apply()

    def action_apply(self):
        for record in self:
            if record.state != "pending":
                raise UserError("La solicitud ya fue procesada.")
            try:
                if record.action == "confirm":
                    record.appointment_id.action_register_patient_confirmation()
                elif record.action == "cancel":
                    record.appointment_id.action_register_patient_cancellation()
                elif record.action == "reschedule":
                    if not record.requested_start_datetime:
                        raise ValidationError("Indique la nueva fecha antes de aplicar la reprogramación.")
                    record.appointment_id.write({"start_datetime": record.requested_start_datetime})
                elif record.action == "offer_accept":
                    record.slot_offer_id.action_accept()
                elif record.action == "offer_decline":
                    record.slot_offer_id.action_decline()
                record.with_context(odental_whatsapp_request_transition=True).write({
                    "state": "applied", "processed_at": fields.Datetime.now(),
                    "processed_by": self.env.user.id, "processing_note": "Aplicada mediante flujo controlado.",
                })
            except (UserError, ValidationError) as exc:
                record.with_context(odental_whatsapp_request_transition=True).write({
                    "state": "failed", "processed_at": fields.Datetime.now(),
                    "processed_by": self.env.user.id, "processing_note": str(exc)[:300],
                })
                if not self.env.context.get("odental_whatsapp_webhook"):
                    raise
        return True

    def action_reject(self):
        for record in self:
            if record.state != "pending":
                raise UserError("La solicitud ya fue procesada.")
            record.with_context(odental_whatsapp_request_transition=True).write({
                "state": "rejected", "processed_at": fields.Datetime.now(),
                "processed_by": self.env.user.id, "processing_note": "Rechazada por el equipo clínico.",
            })


class ODentalWhatsAppEvent(models.Model):
    _name = "odental.whatsapp.event"
    _description = "Evento webhook WhatsApp O Dental"
    _order = "received_at desc, id desc"

    account_id = fields.Many2one("odental.whatsapp.account", required=True, readonly=True, index=True)
    organization_id = fields.Many2one(related="account_id.organization_id", store=True, index=True)
    event_key = fields.Char(required=True, readonly=True, copy=False, index=True)
    event_type = fields.Selection(
        [("message", "Mensaje entrante"), ("status", "Estado de entrega")],
        required=True, readonly=True, index=True,
    )
    provider_message_id = fields.Char(readonly=True, index=True)
    wa_id = fields.Char(string="Remitente WhatsApp", readonly=True, index=True)
    message_kind = fields.Char(readonly=True)
    text_preview = fields.Char(readonly=True)
    payload_digest = fields.Char(required=True, readonly=True)
    received_at = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
    state = fields.Selection(
        [("processed", "Procesado"), ("ignored", "Ignorado"), ("failed", "Fallido")],
        required=True, readonly=True,
    )
    processing_note = fields.Char(readonly=True)
    request_id = fields.Many2one("odental.whatsapp.request", readonly=True)

    _sql_constraints = [("event_key_unique", "unique(event_key)", "Este evento ya fue recibido.")]

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("odental_whatsapp_event_create"):
            raise AccessError("Los eventos solo se crean desde el webhook verificado.")
        return super().create(vals_list)

    def write(self, vals):
        raise UserError("Los eventos WhatsApp son inmutables.")

    def unlink(self):
        raise UserError("Los eventos WhatsApp son inmutables.")

    @api.model
    def ingest_payload(self, account, payload):
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        values_list = []
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                metadata_phone_id = (value.get("metadata") or {}).get("phone_number_id")
                if metadata_phone_id and metadata_phone_id != account.phone_number_id:
                    continue
                for status in value.get("statuses", []):
                    status_id = status.get("id") or "unknown"
                    status_name = status.get("status") or "unknown"
                    message = self.env["odental.communication.message"].sudo().search([
                        ("whatsapp_provider_message_id", "=", status_id),
                        ("whatsapp_account_id", "=", account.id),
                    ], limit=1)
                    if message:
                        errors = status.get("errors") or []
                        error_message = str(errors[0].get("title") or errors[0].get("message") or "") if errors else False
                        message._apply_provider_status(status_name, error_message)
                    values_list.append({
                        "account_id": account.id,
                        "event_key": f"status:{status_id}:{status_name}",
                        "event_type": "status", "provider_message_id": status_id,
                        "wa_id": normalize_phone(status.get("recipient_id")),
                        "message_kind": status_name, "payload_digest": digest,
                        "state": "processed" if message else "ignored",
                        "processing_note": "Estado vinculado al mensaje." if message else "Mensaje de origen no encontrado.",
                    })
                for incoming in value.get("messages", []):
                    provider_id = incoming.get("id") or ""
                    if provider_id and self.sudo().search_count([
                        ("event_key", "=", f"message:{provider_id}")
                    ]):
                        continue
                    event_values = self._process_incoming(account, incoming, digest)
                    values_list.append(event_values)
        for event_values in values_list:
            if not self.sudo().search_count([("event_key", "=", event_values["event_key"])]):
                self.sudo().with_context(odental_whatsapp_event_create=True).create(event_values)
        return True

    @api.model
    def _process_incoming(self, account, incoming, digest):
        provider_id = incoming.get("id") or uuid4().hex
        wa_id = normalize_phone(incoming.get("from"))
        kind = incoming.get("type") or "unsupported"
        token_value = False
        text_value = ""
        if kind == "button":
            button = incoming.get("button") or {}
            token_value = button.get("payload")
            text_value = button.get("text") or ""
        elif kind == "interactive":
            interactive = incoming.get("interactive") or {}
            reply = interactive.get("button_reply") or interactive.get("list_reply") or {}
            token_value = reply.get("id")
            text_value = reply.get("title") or ""
        elif kind == "text":
            text_value = ((incoming.get("text") or {}).get("body") or "").strip()
        request_record = False
        note = "Mensaje sin acción reconocida."
        state = "ignored"
        try:
            if token_value:
                token = self.env["odental.whatsapp.action.token"].sudo().search([
                    ("token", "=", token_value), ("state", "=", "active"),
                ], limit=1)
                if token and token.organization_id == account.organization_id:
                    request_record = token.with_context(odental_whatsapp_webhook=True)._consume(wa_id)
                    note, state = "Respuesta interactiva verificada.", "processed"
            elif text_value:
                action = self._strict_text_action(text_value)
                if action:
                    request_record = self._request_from_text(account, wa_id, action)
                    note, state = "Respuesta textual vinculada a la comunicación más reciente.", "processed"
        except (AccessError, UserError, ValidationError) as exc:
            note, state = str(exc)[:300], "failed"
        return {
            "account_id": account.id,
            "event_key": f"message:{provider_id}",
            "event_type": "message", "provider_message_id": provider_id,
            "wa_id": wa_id, "message_kind": kind,
            "text_preview": text_value[:160], "payload_digest": digest,
            "state": state, "processing_note": note,
            "request_id": request_record.id if request_record else False,
        }

    @api.model
    def _strict_text_action(self, text_value):
        normalized = " ".join(text_value.upper().replace("Í", "I").split())
        return {
            "SI": "confirm", "CONFIRMAR": "confirm", "CONFIRMO": "confirm",
            "CANCELAR": "cancel", "CANCELO": "cancel",
            "REPROGRAMAR": "reschedule",
        }.get(normalized)

    @api.model
    def _request_from_text(self, account, wa_id, action):
        patient = self.env["odental.patient"].sudo().search([
            ("organization_id", "=", account.organization_id.id),
            ("whatsapp_wa_id", "=", wa_id),
        ], limit=1)
        if not patient:
            raise ValidationError("No se encontró un paciente para este número.")
        message = self.env["odental.communication.message"].sudo().search([
            ("patient_id", "=", patient.id),
            ("whatsapp_account_id", "=", account.id),
            ("appointment_id", "!=", False),
            ("state", "in", ("sent", "delivered", "read")),
            ("sent_at", ">=", fields.Datetime.now() - timedelta(days=7)),
        ], order="sent_at desc, id desc", limit=1)
        if not message:
            raise ValidationError("No existe una comunicación reciente a la cual aplicar la respuesta.")
        request_record = self.env["odental.whatsapp.request"].sudo().with_context(
            odental_whatsapp_request_create=True
        ).create({
            "organization_id": account.organization_id.id,
            "account_id": account.id,
            "patient_id": patient.id,
            "appointment_id": message.appointment_id.id,
            "source_message_id": message.id,
            "action": action,
        })
        request_record.with_context(odental_whatsapp_webhook=True)._auto_apply_if_allowed()
        return request_record
