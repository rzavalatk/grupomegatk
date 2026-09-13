from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


_AUDIT_CREATE_TOKEN = object()


class ODentalAIAudit(models.Model):
    _name = "odental.ai.audit"
    _description = "Auditoría del asistente IA O Dental"
    _order = "occurred_at desc, id desc"
    _rec_name = "summary"

    occurred_at = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="restrict", index=True
    )
    patient_id = fields.Many2one("odental.patient", ondelete="restrict", index=True)
    session_id = fields.Many2one(
        "odental.ai.session", required=True, ondelete="restrict", index=True
    )
    action_id = fields.Many2one("odental.ai.action", ondelete="restrict", index=True)
    user_id = fields.Many2one(
        "res.users", required=True, default=lambda self: self.env.user, ondelete="restrict"
    )
    event_type = fields.Selection(
        [
            ("captured", "Instrucción capturada"),
            ("analyzed", "Propuesta analizada"),
            ("confirmed", "Propuesta confirmada"),
            ("executed", "Acción ejecutada"),
            ("undone", "Acción deshecha"),
            ("cancelled", "Sesión cancelada"),
        ],
        required=True,
        index=True,
    )
    summary = fields.Char(required=True)
    content_hash = fields.Char(readonly=True, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("odental_ai_audit") is not _AUDIT_CREATE_TOKEN:
            raise AccessError("La auditoría se genera únicamente desde acciones controladas.")
        return super().create(vals_list)

    @api.model
    def _record_event(
        self, session, event_type, summary, action=False, content_hash=False
    ):
        values = {
            "organization_id": session.organization_id.id,
            "patient_id": session.patient_id.id,
            "session_id": session.id,
            "action_id": action.id if action else False,
            "user_id": self.env.user.id,
            "event_type": event_type,
            "summary": summary,
            "content_hash": content_hash,
        }
        return self.sudo().with_context(odental_ai_audit=_AUDIT_CREATE_TOKEN).create(
            values
        )

    def write(self, vals):
        raise ValidationError("Los eventos de auditoría de IA son inmutables.")

    def unlink(self):
        raise ValidationError("Los eventos de auditoría de IA no se pueden eliminar.")
