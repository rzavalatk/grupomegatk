from odoo import fields, models
from odoo.exceptions import ValidationError


class ODentalClinicalAudit(models.Model):
    _name = "odental.clinical.audit"
    _description = "Auditoría clínica O Dental"
    _order = "occurred_at desc, id desc"
    _rec_name = "summary"

    occurred_at = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="restrict", index=True
    )
    patient_id = fields.Many2one(
        "odental.patient", required=True, ondelete="restrict", index=True
    )
    user_id = fields.Many2one(
        "res.users", required=True, default=lambda self: self.env.user, ondelete="restrict"
    )
    event_type = fields.Selection(
        [
            ("record_created", "Expediente creado"),
            ("record_closed", "Expediente cerrado"),
            ("record_reopened", "Expediente reabierto"),
            ("history_created", "Antecedente creado"),
            ("history_updated", "Antecedente actualizado"),
            ("history_deleted", "Antecedente eliminado"),
            ("encounter_created", "Evolución creada"),
            ("encounter_signed", "Evolución firmada"),
            ("encounter_amended", "Evolución rectificada"),
            ("consent_created", "Consentimiento creado"),
            ("consent_requested", "Consentimiento solicitado"),
            ("consent_signed", "Consentimiento firmado"),
            ("consent_rejected", "Consentimiento rechazado"),
            ("consent_revoked", "Consentimiento revocado"),
        ],
        required=True,
        index=True,
    )
    model_name = fields.Char(required=True, index=True)
    record_res_id = fields.Integer(required=True, index=True)
    summary = fields.Char(required=True)
    content_hash = fields.Char(string="Huella digital", readonly=True, index=True)

    def init(self):
        self.env.cr.execute(
            "CREATE INDEX IF NOT EXISTS odental_clinical_audit_record_idx "
            "ON odental_clinical_audit (model_name, record_res_id)"
        )

    def write(self, vals):
        if not self.env.su:
            raise ValidationError("Los eventos de auditoría no se pueden modificar.")
        return super().write(vals)

    def unlink(self):
        if not self.env.su:
            raise ValidationError("Los eventos de auditoría no se pueden eliminar.")
        return super().unlink()

