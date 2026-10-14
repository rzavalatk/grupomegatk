from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class ODentalSpecialtyReport(models.TransientModel):
    _name = "odental.specialty.report"
    _description = "Resumen de profesionales por especialidad"

    organization_id = fields.Many2one(
        "odental.organization", string="Clínica / organización", required=True,
    )
    total_professionals = fields.Integer(string="Profesionales activos", readonly=True)
    without_specialty_count = fields.Integer(string="Sin especialidad asignada", readonly=True)
    line_ids = fields.One2many(
        "odental.specialty.report.line", "report_id", string="Especialidades", readonly=True,
    )

    def _check_organization(self):
        self.ensure_one()
        organization = self.env["odental.organization"].search([
            ("id", "=", self.organization_id.id),
            ("company_id", "in", self.env.companies.ids),
        ], limit=1)
        if not organization:
            raise AccessError(_("No tiene acceso a la clínica seleccionada."))
        return organization

    def action_generate(self):
        self.ensure_one()
        organization = self._check_organization()
        professionals = self.env["odental.professional"].search([
            ("organization_ids", "in", organization.id),
            ("company_id", "=", organization.company_id.id),
            ("active", "=", True),
        ])
        specialties = self.env["odental.specialty"].search([
            "|", ("company_id", "=", False),
            ("company_id", "=", organization.company_id.id),
        ])
        counts = {specialty.id: 0 for specialty in specialties}
        without_specialty = 0
        for professional in professionals:
            if not professional.specialty_ids:
                without_specialty += 1
            for specialty in professional.specialty_ids:
                if specialty.id in counts:
                    counts[specialty.id] += 1
        self.write({
            "total_professionals": len(professionals),
            "without_specialty_count": without_specialty,
            "line_ids": [(5, 0, 0)] + [
                (0, 0, {"specialty_id": specialty.id, "professional_count": counts[specialty.id]})
                for specialty in specialties
            ],
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Profesionales por especialidad"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }


class ODentalSpecialtyReportLine(models.TransientModel):
    _name = "odental.specialty.report.line"
    _description = "Conteo de profesionales por especialidad"
    _order = "specialty_id"

    report_id = fields.Many2one("odental.specialty.report", required=True, ondelete="cascade")
    specialty_id = fields.Many2one("odental.specialty", required=True, readonly=True)
    professional_count = fields.Integer(string="Profesionales", readonly=True)

    def action_open_professionals(self):
        self.ensure_one()
        organization = self.report_id._check_organization()
        if self.specialty_id.company_id and self.specialty_id.company_id != organization.company_id:
            raise UserError(_("La especialidad no corresponde a esta clínica."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Profesionales: %s") % self.specialty_id.name,
            "res_model": "odental.professional",
            "view_mode": "list,form",
            "target": "current",
            "domain": [
                ("organization_ids", "in", organization.id),
                ("company_id", "=", organization.company_id.id),
                ("active", "=", True),
                ("specialty_ids", "in", self.specialty_id.id),
            ],
        }
