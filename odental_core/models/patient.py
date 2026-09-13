from odoo import api, fields, models


class ODentalPatient(models.Model):
    _name = "odental.patient"
    _description = "Paciente O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    reference = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    identification = fields.Char(string="Identificación", index=True, tracking=True)
    birthdate = fields.Date(string="Fecha de nacimiento")
    gender = fields.Selection(
        [("female", "Femenino"), ("male", "Masculino"), ("other", "Otro"), ("unspecified", "No especificado")]
    )
    mobile = fields.Char()
    email = fields.Char()
    partner_id = fields.Many2one("res.partner", string="Contacto vinculado")
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="restrict", index=True, tracking=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    responsible_partner_id = fields.Many2one(
        "res.partner", string="Padre, madre o representante"
    )
    notes = fields.Text(string="Notas generales")

    _sql_constraints = [
        (
            "identification_organization_unique",
            "unique(identification, organization_id)",
            "Ya existe un paciente con esta identificación en la organización.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("reference", "Nuevo") == "Nuevo":
                vals["reference"] = self.env["ir.sequence"].next_by_code("odental.patient") or "Nuevo"
        return super().create(vals_list)

    def name_get(self):
        return [(record.id, f"{record.reference} - {record.name}") for record in self]

