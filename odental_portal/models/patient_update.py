import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ODentalPatientUpdateRequest(models.Model):
    _name = "odental.patient.update.request"
    _description = "Solicitud de actualización de paciente O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "submitted_at desc, id desc"

    name = fields.Char(default="Nueva", readonly=True, copy=False, index=True)
    patient_id = fields.Many2one(
        "odental.patient", required=True, ondelete="restrict", index=True, tracking=True
    )
    organization_id = fields.Many2one(
        related="patient_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    invitation_id = fields.Many2one(
        "odental.patient.portal.invitation", readonly=True, copy=False, ondelete="restrict"
    )
    previous_values_json = fields.Text(readonly=True, copy=False)
    requested_name = fields.Char(required=True)
    requested_identification = fields.Char()
    requested_birthdate = fields.Date()
    requested_mobile = fields.Char()
    requested_email = fields.Char()
    submitted_at = fields.Datetime(required=True, readonly=True, default=fields.Datetime.now)
    submitted_ip_address = fields.Char(readonly=True)
    submitted_user_agent = fields.Char(readonly=True)
    reviewed_at = fields.Datetime(readonly=True, copy=False)
    reviewed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    review_notes = fields.Text()
    state = fields.Selection(
        [("submitted", "Pendiente"), ("approved", "Aprobada"), ("rejected", "Rechazada")],
        required=True,
        default="submitted",
        tracking=True,
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not self.env.context.get("odental_portal_submission"):
                raise AccessError("Las solicitudes se crean únicamente desde el portal seguro.")
            if vals.get("name", "Nueva") == "Nueva":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.patient.update.request"
                ) or "Nueva"
            patient = self.env["odental.patient"].browse(vals.get("patient_id"))
            vals["previous_values_json"] = json.dumps(
                {
                    "name": patient.name or "",
                    "identification": patient.identification or "",
                    "birthdate": fields.Date.to_string(patient.birthdate),
                    "mobile": patient.mobile or "",
                    "email": patient.email or "",
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        return super().create(vals_list)

    def write(self, vals):
        protected = {
            "patient_id", "organization_id", "invitation_id", "previous_values_json",
            "requested_name", "requested_identification", "requested_birthdate",
            "requested_mobile", "requested_email", "submitted_at", "submitted_ip_address",
            "submitted_user_agent", "state", "reviewed_at", "reviewed_by_id",
        }
        if protected.intersection(vals) and not self.env.context.get("allow_patient_update_transition"):
            raise UserError("La solicitud enviada es inmutable; utilice las acciones de revisión.")
        return super().write(vals)

    def unlink(self):
        raise UserError("Las solicitudes del portal se conservan como evidencia.")

    def action_approve(self):
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError("Solo un administrador clínico puede aprobar cambios de paciente.")
        for update in self:
            if update.state != "submitted":
                raise UserError("La solicitud ya fue revisada.")
            update.patient_id.write(
                {
                    "name": update.requested_name,
                    "identification": update.requested_identification,
                    "birthdate": update.requested_birthdate,
                    "mobile": update.requested_mobile,
                    "email": update.requested_email,
                }
            )
            update.with_context(allow_patient_update_transition=True).write(
                {
                    "state": "approved",
                    "reviewed_at": fields.Datetime.now(),
                    "reviewed_by_id": self.env.user.id,
                }
            )
            record = self.env["odental.clinical.record"].search(
                [("patient_id", "=", update.patient_id.id)], limit=1
            )
            if record:
                record._log_event(
                    "portal_demographics_approved",
                    f"Actualización demográfica aprobada: {update.name}",
                    source_record=update,
                )

    def action_reject(self):
        for update in self:
            if update.state != "submitted":
                raise UserError("La solicitud ya fue revisada.")
            if not update.review_notes:
                raise ValidationError("Indique el motivo o las observaciones del rechazo.")
            update.with_context(allow_patient_update_transition=True).write(
                {
                    "state": "rejected",
                    "reviewed_at": fields.Datetime.now(),
                    "reviewed_by_id": self.env.user.id,
                }
            )
