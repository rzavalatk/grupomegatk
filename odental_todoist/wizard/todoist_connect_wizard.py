from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class ODentalTodoistConnectWizard(models.TransientModel):
    _name = "odental.todoist.connect.wizard"
    _description = "Conectar mi Todoist a la disponibilidad clínica"

    professional_id = fields.Many2one("odental.professional", required=True)
    organization_id = fields.Many2one("odental.organization", required=True)
    project_name = fields.Char(string="Nombre si se crea el proyecto", help="Se usa si no indica un enlace o ID.")
    project_reference = fields.Char(
        string="Enlace o ID del proyecto existente",
        help="Opcional: copie el enlace desde Todoist. Debe ser un proyecto personal y privado de su cuenta.",
    )
    pilot_patient_id = fields.Many2one("odental.patient", string="Paciente de prueba", required=True)
    api_token = fields.Char(string="Token personal de Todoist", required=True)
    label_name = fields.Char(string="Etiqueta de reunión", default="reunión", required=True)
    default_duration_minutes = fields.Integer(
        string="Duración si Todoist no indica una", default=60, required=True,
    )
    source_timezone = fields.Char(string="Zona horaria", default="America/Tegucigalpa", required=True)

    @api.onchange("organization_id")
    def _suggest_project_name(self):
        for wizard in self:
            if wizard.organization_id and not wizard.project_name:
                wizard.project_name = f"{wizard.organization_id.name.strip()} | Agenda clínica"

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        professionals = self.env["odental.professional"].search([
            ("user_id", "=", self.env.user.id),
            ("company_id", "=", self.env.company.id),
        ])
        if len(professionals) == 1:
            professional = professionals
            result["professional_id"] = professional.id
            organizations = professional.organization_ids.filtered(
                lambda item: item.company_id == self.env.company
            )
            if len(organizations) == 1:
                result["organization_id"] = organizations.id
                result["project_name"] = f"{organizations.name.strip()} | Agenda clínica"
                connection = self.env["odental.todoist.connection"].sudo().search([
                    ("professional_id", "=", professional.id),
                    ("organization_id", "=", organizations.id),
                ], limit=1)
                if connection:
                    result["project_name"] = connection.project_name
                    result["project_reference"] = connection.project_reference or connection.project_id
        return result

    def action_connect(self):
        self.ensure_one()
        professional = self.professional_id
        organization = self.organization_id
        if not professional or professional.user_id != self.env.user:
            raise AccessError("Solo el profesional titular puede conectar su Todoist.")
        if (organization not in professional.organization_ids or
                organization.company_id != self.env.company or
                organization.company_id not in self.env.user.company_ids):
            raise AccessError("La organización no está autorizada para este profesional.")
        if professional.company_id != organization.company_id:
            raise AccessError("El profesional debe pertenecer a la compañía de la clínica.")
        if self.pilot_patient_id.organization_id != organization:
            raise AccessError("Seleccione un paciente de prueba de esta organización.")
        if not self.label_name.strip():
            raise UserError("Indique una etiqueta que bloqueará la agenda.")
        if not 0 < self.default_duration_minutes <= 1440:
            raise UserError("Indique una duración predeterminada de 1 a 1440 minutos.")
        connections = self.env["odental.todoist.connection"]
        # Validate the token against Todoist before storing any credential.
        todoist_user_id = connections._fetch_user_id(self.api_token)
        connection = connections.sudo().search([
            ("professional_id", "=", professional.id),
            ("organization_id", "=", organization.id),
        ], limit=1)
        if (connection and connection.todoist_user_id
                and connection.todoist_user_id != todoist_user_id
                and self.env["odental.todoist.mirror"].sudo().search_count([
                    ("connection_id", "=", connection.id),
                ])):
            raise UserError("Desconecte la cuenta anterior antes de vincular otra cuenta Todoist.")
        reference = (self.project_reference or "").strip()
        if reference:
            project = connections._select_clinical_project(self.api_token, reference)
            project_id = str(project["id"])
            project_name = project["name"]
        else:
            project_name = (self.project_name or "").strip()
            if not project_name or len(project_name) > 120:
                raise UserError("Indique un nombre breve para el proyecto privado.")
            project_id = connections._find_or_create_clinical_project(
                self.api_token, project_name,
            )
            reference = project_id
        other_connection = connections.sudo().search([
            ("todoist_user_id", "=", todoist_user_id),
            ("project_id", "=", project_id),
            ("id", "!=", connection.id if connection else 0),
        ], limit=1)
        if other_connection:
            raise UserError("Ese proyecto ya está asignado a otra conexión clínica.")
        values = {
            "professional_id": professional.id,
            "organization_id": organization.id,
            "pilot_patient_id": self.pilot_patient_id.id,
            "api_token": self.api_token,
            "todoist_user_id": todoist_user_id,
            "project_id": project_id,
            "project_name": project_name,
            "project_reference": reference,
            "label_name": self.label_name.strip(),
            "default_duration_minutes": self.default_duration_minutes,
            "source_timezone": self.source_timezone.strip(),
            "active": True,
        }
        if connection:
            connection.write(values)
        else:
            connection = connections.sudo().create(values)
        connection._sync_one()
        self.unlink()  # Do not leave the submitted token in a transient record.
        return {"type": "ir.actions.act_window", "res_model": "odental.todoist.connection",
                "view_mode": "form", "res_id": connection.id, "target": "current"}
