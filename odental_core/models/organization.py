from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ODentalOrganization(models.Model):
    _name = "odental.organization"
    _description = "Organización O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(string="Nombre", required=True, tracking=True)
    code = fields.Char(string="Código", required=True, copy=False, index=True)
    active = fields.Boolean(string="Activo", default=True)
    organization_type = fields.Selection(
        [
            ("individual", "Odontólogo individual"),
            ("shared", "Consultorio compartido"),
            ("clinic", "Clínica"),
            ("institution", "Institución"),
            ("university", "Universidad"),
        ],
        string="Tipo de organización",
        required=True,
        default="individual",
        tracking=True,
    )
    billing_mode = fields.Selection(
        [
            ("independent", "Facturación independiente"),
            ("centralized", "Facturación centralizada"),
            ("mixed", "Ambas modalidades"),
        ],
        string="Modalidad de facturación",
        required=True,
        default="independent",
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía", required=True,
        default=lambda self: self.env.company, index=True
    )
    owner_user_id = fields.Many2one(
        "res.users", string="Propietario/administrador", required=True,
        default=lambda self: self.env.user, tracking=True
    )
    user_ids = fields.Many2many(
        "res.users", "odental_organization_user_rel", "organization_id", "user_id",
        string="Usuarios autorizados"
    )
    site_ids = fields.One2many("odental.site", "organization_id", string="Sedes propias")
    shared_site_ids = fields.Many2many(
        "odental.site",
        "odental_site_shared_organization_rel",
        "organization_id",
        "site_id",
        string="Sedes compartidas disponibles",
        readonly=True,
    )
    notes = fields.Text(string="Notas")

    _sql_constraints = [
        ("code_company_unique", "unique(code, company_id)", "El código debe ser único por compañía."),
    ]

    @api.constrains("owner_user_id", "user_ids")
    def _check_owner_is_authorized(self):
        for organization in self:
            if organization.owner_user_id and organization.user_ids and organization.owner_user_id not in organization.user_ids:
                raise ValidationError("El propietario debe formar parte de los usuarios autorizados.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            owner_id = vals.get("owner_user_id") or self.env.user.id
            commands = vals.setdefault("user_ids", [])
            commands.append((4, owner_id))
        return super().create(vals_list)
