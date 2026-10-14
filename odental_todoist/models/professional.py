from odoo import _, models
from odoo.exceptions import AccessError, UserError


class ODentalProfessional(models.Model):
    _inherit = "odental.professional"

    def action_open_my_todoist_settings(self):
        self.ensure_one()
        if self.user_id != self.env.user or self.company_id not in self.env.companies:
            raise AccessError(_("Solo el profesional titular puede configurar su Todoist."))
        organizations = self.organization_ids.filtered(
            lambda organization: organization.company_id == self.company_id
        )
        if not organizations:
            raise UserError(_("Primero vincule al profesional con su clínica."))
        action = self.env["ir.actions.actions"]._for_xml_id(
            "odental_todoist.action_odental_todoist_connect"
        )
        action["context"] = {
            "default_professional_id": self.id,
            **({"default_organization_id": organizations.id} if len(organizations) == 1 else {}),
        }
        return action
