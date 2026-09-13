import hashlib
import hmac
import secrets
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ODentalPatientPortalInvitation(models.Model):
    _name = "odental.patient.portal.invitation"
    _description = "Invitación al portal O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    patient_id = fields.Many2one(
        "odental.patient", required=True, ondelete="restrict", index=True, tracking=True
    )
    organization_id = fields.Many2one(
        related="patient_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    delivery_channel = fields.Selection(
        [("email", "Correo"), ("whatsapp", "WhatsApp"), ("in_person", "Presencial")],
        required=True,
        default="whatsapp",
    )
    recipient = fields.Char(required=True)
    valid_hours = fields.Integer(string="Horas de vigencia", required=True, default=24)
    expires_at = fields.Datetime(readonly=True, copy=False, index=True)
    max_attempts = fields.Integer(required=True, default=5)
    token_hash = fields.Char(readonly=True, copy=False, index=True)
    token_hint = fields.Char(readonly=True, copy=False)
    otp_hash = fields.Char(readonly=True, copy=False)
    otp_attempts = fields.Integer(readonly=True, copy=False)
    locked_until = fields.Datetime(readonly=True, copy=False)
    used_at = fields.Datetime(readonly=True, copy=False)
    used_ip_address = fields.Char(readonly=True, copy=False)
    revoked_at = fields.Datetime(readonly=True, copy=False)
    revoked_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    revocation_reason = fields.Text(copy=False)
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("active", "Activa"),
            ("used", "Utilizada"),
            ("expired", "Vencida"),
            ("revoked", "Revocada"),
        ],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )

    _sql_constraints = [
        (
            "patient_active_token_unique",
            "unique(token_hash)",
            "La invitación ya existe.",
        )
    ]

    @api.onchange("patient_id", "delivery_channel")
    def _onchange_recipient(self):
        for invitation in self:
            if invitation.delivery_channel == "email":
                invitation.recipient = invitation.patient_id.email
            elif invitation.delivery_channel == "whatsapp":
                invitation.recipient = invitation.patient_id.mobile

    @api.constrains("valid_hours", "max_attempts")
    def _check_limits(self):
        for invitation in self:
            if invitation.valid_hours < 1 or invitation.valid_hours > 168:
                raise ValidationError("La vigencia debe estar entre 1 y 168 horas.")
            if invitation.max_attempts < 3 or invitation.max_attempts > 10:
                raise ValidationError("Los intentos permitidos deben estar entre 3 y 10.")

    @staticmethod
    def _digest(value):
        return hashlib.sha256((value or "").encode("utf-8")).hexdigest()

    def write(self, vals):
        protected = {
            "patient_id", "organization_id", "delivery_channel", "recipient",
            "valid_hours", "max_attempts", "expires_at", "token_hash", "token_hint",
            "otp_hash", "otp_attempts", "locked_until", "used_at", "used_ip_address",
            "revoked_at", "revoked_by_id", "state",
        }
        if protected.intersection(vals) and not self.env.context.get("allow_portal_invitation_transition"):
            if any(record.state != "draft" for record in self) or "state" in vals:
                raise UserError("Utilice las acciones controladas de la invitación.")
        return super().write(vals)

    def unlink(self):
        if any(record.state != "draft" for record in self):
            raise UserError("Solo se pueden eliminar invitaciones en borrador.")
        return super().unlink()

    def action_prepare_access(self):
        self.ensure_one()
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError("Solo un administrador clínico puede generar invitaciones.")
        if self.state not in {"draft", "active"}:
            raise UserError("Esta invitación ya no puede regenerarse.")
        if not (self.recipient or "").strip():
            raise ValidationError("Registre el destino de la invitación.")
        other_active = self.search(
            [
                ("patient_id", "=", self.patient_id.id),
                ("state", "=", "active"),
                ("id", "!=", self.id),
            ],
            limit=1,
        )
        if other_active:
            raise ValidationError(
                "El paciente ya tiene una invitación activa. Revoque la anterior antes de crear otra."
            )
        token = secrets.token_urlsafe(32)
        otp = f"{secrets.randbelow(1000000):06d}"
        expires_at = fields.Datetime.now() + timedelta(hours=self.valid_hours)
        self.with_context(allow_portal_invitation_transition=True).write(
            {
                "state": "active",
                "expires_at": expires_at,
                "token_hash": self._digest(token),
                "token_hint": token[-6:],
                "otp_hash": self._digest(otp),
                "otp_attempts": 0,
                "locked_until": False,
            }
        )
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        access_url = f"{base_url}/odental/register/{token}"
        credentials = self.env["odental.patient.portal.credentials"].create(
            {"invitation_id": self.id, "access_url": access_url, "otp": otp}
        )
        return {
            "name": "Acceso temporal del paciente",
            "type": "ir.actions.act_window",
            "res_model": "odental.patient.portal.credentials",
            "res_id": credentials.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_revoke(self):
        for invitation in self:
            if invitation.state != "active":
                raise UserError("Solo una invitación activa puede revocarse.")
            if not invitation.revocation_reason:
                raise ValidationError("Indique el motivo de revocación.")
            invitation.with_context(allow_portal_invitation_transition=True).write(
                {
                    "state": "revoked",
                    "revoked_at": fields.Datetime.now(),
                    "revoked_by_id": self.env.user.id,
                    "token_hash": False,
                    "otp_hash": False,
                }
            )

    @api.model
    def _find_by_token(self, token):
        if not token:
            return self.browse()
        invitation = self.sudo().search(
            [("token_hash", "=", self._digest(token)), ("state", "=", "active")], limit=1
        )
        if invitation and invitation.expires_at <= fields.Datetime.now():
            invitation.with_context(allow_portal_invitation_transition=True).write(
                {"state": "expired", "token_hash": False, "otp_hash": False}
            )
            return self.browse()
        return invitation

    def _verify_otp(self, code):
        self.ensure_one()
        now = fields.Datetime.now()
        if self.state != "active" or self.expires_at <= now:
            return False, "La invitación venció o ya no está disponible."
        if self.locked_until and self.locked_until > now:
            return False, "Demasiados intentos. Intente nuevamente más tarde."
        supplied = self._digest((code or "").strip())
        if not self.otp_hash or not hmac.compare_digest(supplied, self.otp_hash):
            attempts = self.otp_attempts + 1
            values = {"otp_attempts": attempts}
            if attempts >= self.max_attempts:
                values.update({"locked_until": now + timedelta(minutes=15), "otp_attempts": 0})
            self.with_context(allow_portal_invitation_transition=True).write(values)
            return False, "El código temporal no es válido."
        self.with_context(allow_portal_invitation_transition=True).write(
            {"otp_attempts": 0, "locked_until": False}
        )
        return True, False

    def _mark_used(self, ip_address):
        self.ensure_one()
        self.with_context(allow_portal_invitation_transition=True).write(
            {
                "state": "used",
                "used_at": fields.Datetime.now(),
                "used_ip_address": ip_address,
                "token_hash": False,
                "otp_hash": False,
            }
        )

    @api.model
    def _cron_expire_invitations(self):
        expired = self.search(
            [("state", "=", "active"), ("expires_at", "<=", fields.Datetime.now())]
        )
        expired.with_context(allow_portal_invitation_transition=True).write(
            {"state": "expired", "token_hash": False, "otp_hash": False}
        )
