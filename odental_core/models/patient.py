from odoo import api, fields, models


class ODentalPatient(models.Model):
    _name = "odental.patient"
    _description = "Paciente O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    reference = fields.Char(
        string="Código de paciente", default="Nuevo", readonly=True, copy=False, index=True
    )
    name = fields.Char(string="Nombre completo", required=True, tracking=True)
    active = fields.Boolean(string="Activo", default=True)
    identification = fields.Char(string="Identificación", index=True, tracking=True)
    birthdate = fields.Date(string="Fecha de nacimiento")
    gender = fields.Selection(
        [("female", "Femenino"), ("male", "Masculino"), ("other", "Otro"), ("unspecified", "No especificado")],
        string="Género",
    )
    mobile = fields.Char(string="Teléfono móvil")
    email = fields.Char(string="Correo electrónico")
    partner_id = fields.Many2one("res.partner", string="Contacto vinculado")
    organization_id = fields.Many2one(
        "odental.organization", string="Organización", required=True,
        ondelete="restrict", index=True, tracking=True
    )
    company_id = fields.Many2one(
        related="organization_id.company_id", string="Compañía", store=True, index=True
    )
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

    def action_new_appointment(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Nueva cita",
            "res_model": "odental.appointment",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "current",
            "context": {
                "default_patient_id": self.id,
                "default_organization_id": self.organization_id.id,
            },
        }
