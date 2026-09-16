from odoo import fields, models


class ODentalProfessional(models.Model):
    _name = "odental.professional"
    _description = "Profesional O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(string="Nombre del profesional", required=True, tracking=True)
    active = fields.Boolean(string="Activo", default=True)
    user_id = fields.Many2one(
        "res.users",
        string="Usuario de Odoo",
        tracking=True,
        help="Déjelo vacío si el profesional todavía no tendrá acceso al sistema.",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contacto",
        help="Ficha con teléfono, correo electrónico y dirección del profesional.",
    )
    license_number = fields.Char(string="Número de colegiación", tracking=True)
    specialty = fields.Char(string="Especialidad")
    organization_ids = fields.Many2many(
        "odental.organization", "odental_professional_organization_rel",
        "professional_id", "organization_id", required=True,
        string="Organizaciones a las que pertenece",
        help="Clínicas, universidades u otras organizaciones donde este profesional puede atender.",
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía", required=True, default=lambda self: self.env.company, index=True
    )
