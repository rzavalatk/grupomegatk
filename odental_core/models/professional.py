from odoo import fields, models


class ODentalProfessional(models.Model):
    _name = "odental.professional"
    _description = "Profesional O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    user_id = fields.Many2one("res.users", string="Usuario", tracking=True)
    partner_id = fields.Many2one("res.partner", string="Contacto")
    license_number = fields.Char(string="Número de colegiación", tracking=True)
    specialty = fields.Char(string="Especialidad")
    organization_ids = fields.Many2many(
        "odental.organization", "odental_professional_organization_rel",
        "professional_id", "organization_id", required=True,
        string="Organizaciones"
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )

