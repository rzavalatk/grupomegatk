from odoo import models


def _assistant_action(record, extra_context=None):
    organization = record.organization_id
    professional = record.env["odental.professional"].search(
        [
            ("user_id", "=", record.env.user.id),
            ("organization_ids", "in", [organization.id]),
        ],
        limit=1,
    )
    action = record.env.ref("odental_ai.action_odental_ai_session").read()[0]
    context = {
        "default_organization_id": organization.id,
        "default_professional_id": professional.id,
    }
    context.update(extra_context or {})
    action["context"] = context
    action["views"] = [(False, "form")]
    return action


class ODentalPatient(models.Model):
    _inherit = "odental.patient"

    def action_open_ai_assistant(self):
        self.ensure_one()
        return _assistant_action(
            self,
            {"default_patient_id": self.id},
        )


class ODentalClinicalRecord(models.Model):
    _inherit = "odental.clinical.record"

    def action_open_ai_assistant(self):
        self.ensure_one()
        return _assistant_action(
            self,
            {"default_patient_id": self.patient_id.id},
        )


class ODentalAppointment(models.Model):
    _inherit = "odental.appointment"

    def action_open_ai_assistant(self):
        self.ensure_one()
        return _assistant_action(
            self,
            {
                "default_patient_id": self.patient_id.id,
                "default_professional_id": self.professional_id.id,
                "default_appointment_id": self.id,
                "default_service_id": self.service_id.id,
                "default_site_id": self.site_id.id,
                "default_resource_ids": [(6, 0, self.resource_ids.ids)],
            },
        )
