from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


_AUDIT_CREATE_TOKEN = object()


class ODentalAcademicAudit(models.Model):
    _name = "odental.academic.audit"
    _description = "Auditoría académica O Dental"
    _order = "occurred_at desc, id desc"
    _rec_name = "summary"

    occurred_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="restrict", index=True, readonly=True
    )
    case_id = fields.Many2one(
        "odental.academic.case", required=True, ondelete="restrict", index=True, readonly=True
    )
    submission_id = fields.Many2one(
        "odental.academic.submission", ondelete="restrict", index=True, readonly=True
    )
    user_id = fields.Many2one(
        "res.users", required=True, ondelete="restrict", index=True, readonly=True
    )
    event_type = fields.Selection(
        [
            ("case_activated", "Caso activado"),
            ("case_completed", "Caso finalizado"),
            ("case_revoked", "Acceso revocado"),
            ("access_expired", "Acceso vencido"),
            ("submission_submitted", "Trabajo enviado"),
            ("submission_approved", "Trabajo aprobado"),
            ("submission_rejected", "Trabajo devuelto"),
            ("submission_applied", "Trabajo aplicado"),
            ("submission_revised", "Revisión creada"),
        ],
        required=True,
        readonly=True,
        index=True,
    )
    summary = fields.Char(required=True, readonly=True)
    content_hash = fields.Char(readonly=True, copy=False, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("odental_academic_audit_create") is not _AUDIT_CREATE_TOKEN:
            raise AccessError("La auditoría académica solo se genera desde acciones controladas.")
        return super().create(vals_list)

    @api.model
    def _record(self, case, event_type, summary, submission=False, content_hash=False):
        return self.sudo().with_context(
            odental_academic_audit_create=_AUDIT_CREATE_TOKEN
        ).create(
            {
                "organization_id": case.organization_id.id,
                "case_id": case.id,
                "submission_id": submission.id if submission else False,
                "user_id": self.env.user.id,
                "event_type": event_type,
                "summary": summary,
                "content_hash": content_hash,
            }
        )

    def write(self, vals):
        raise UserError("Los eventos de auditoría académica son inmutables.")

    def unlink(self):
        raise UserError("Los eventos de auditoría académica se conservan como evidencia.")

