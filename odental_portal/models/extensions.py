from odoo import fields, models


class ODentalClinicalAudit(models.Model):
    _inherit = "odental.clinical.audit"

    event_type = fields.Selection(
        selection_add=[
            ("portal_demographics_approved", "Datos del paciente aprobados desde el portal"),
            ("portal_intake_submitted", "Formulario clínico recibido desde el portal"),
            ("portal_intake_incorporated", "Formulario del portal incorporado al expediente"),
        ],
        ondelete={
            "portal_demographics_approved": "cascade",
            "portal_intake_submitted": "cascade",
            "portal_intake_incorporated": "cascade",
        },
    )


class ODentalPatient(models.Model):
    _inherit = "odental.patient"

    portal_invitation_ids = fields.One2many(
        "odental.patient.portal.invitation", "patient_id", string="Invitaciones de portal"
    )
    portal_invitation_count = fields.Integer(compute="_compute_portal_counts")
    portal_update_request_ids = fields.One2many(
        "odental.patient.update.request", "patient_id", string="Actualizaciones del portal"
    )
    portal_update_request_count = fields.Integer(compute="_compute_portal_counts")
    portal_intake_ids = fields.One2many(
        "odental.patient.intake", "patient_id", string="Formularios del portal"
    )
    portal_intake_count = fields.Integer(compute="_compute_portal_counts")

    def _compute_portal_counts(self):
        for patient in self:
            patient.portal_invitation_count = len(patient.portal_invitation_ids)
            patient.portal_update_request_count = len(patient.portal_update_request_ids)
            patient.portal_intake_count = len(patient.portal_intake_ids)

    def action_view_portal_invitations(self):
        self.ensure_one()
        return {
            "name": "Invitaciones de portal",
            "type": "ir.actions.act_window",
            "res_model": "odental.patient.portal.invitation",
            "view_mode": "list,form",
            "domain": [("patient_id", "=", self.id)],
            "context": {"default_patient_id": self.id},
        }

    def action_view_portal_updates(self):
        self.ensure_one()
        return {
            "name": "Actualizaciones del portal",
            "type": "ir.actions.act_window",
            "res_model": "odental.patient.update.request",
            "view_mode": "list,form",
            "domain": [("patient_id", "=", self.id)],
        }

    def action_view_portal_intakes(self):
        self.ensure_one()
        return {
            "name": "Formularios clínicos",
            "type": "ir.actions.act_window",
            "res_model": "odental.patient.intake",
            "view_mode": "list,form",
            "domain": [("patient_id", "=", self.id)],
        }
