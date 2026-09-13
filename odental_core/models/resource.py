from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ODentalSite(models.Model):
    _name = "odental.site"
    _description = "Sede O Dental"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    active = fields.Boolean(string="Activo", default=True)
    organization_id = fields.Many2one(
        "odental.organization", string="Organización", required=True,
        ondelete="cascade", index=True,
    )
    company_id = fields.Many2one(
        related="organization_id.company_id", string="Empresa de facturación",
        store=True, index=True,
    )
    address = fields.Char(string="Dirección")
    shared_with_organization_ids = fields.Many2many(
        "odental.organization",
        "odental_site_shared_organization_rel",
        "site_id",
        "organization_id",
        string="Disponible para organizaciones",
        help="Organizaciones independientes autorizadas para reservar esta sede.",
    )

    def is_available_to(self, organization):
        self.ensure_one()
        return self.organization_id == organization or organization in self.shared_with_organization_ids


class ODentalResource(models.Model):
    _name = "odental.resource"
    _description = "Recurso reservable O Dental"
    _order = "resource_type, name"

    name = fields.Char(string="Nombre", required=True)
    active = fields.Boolean(string="Activo", default=True)
    resource_type = fields.Selection(
        [
            ("room", "Consultorio"),
            ("chair", "Sillón/unidad dental"),
            ("equipment", "Equipo"),
            ("assistant", "Asistente"),
        ],
        string="Tipo de recurso",
        required=True,
        index=True,
    )
    organization_id = fields.Many2one(
        "odental.organization", string="Organización", required=True,
        ondelete="cascade", index=True,
    )
    company_id = fields.Many2one(
        related="organization_id.company_id", string="Empresa de facturación",
        store=True, index=True,
    )
    site_id = fields.Many2one("odental.site", string="Sede", required=True, ondelete="restrict")
    includes_chair = fields.Boolean(
        string="Incluye sillón o unidad dental",
        help="Actívelo cuando el sillón forma parte fija del consultorio. Así no tendrá que registrarlo por separado.",
    )
    assignment_mode = fields.Selection(
        [
            ("fixed", "Profesional fijo"),
            ("shift", "Por turno o reserva"),
        ],
        string="Modo de asignación",
        required=True,
        default="shift",
        help="Indica si el consultorio tiene un profesional habitual o si cambia según cada turno o reserva.",
    )
    fixed_professional_id = fields.Many2one(
        "odental.professional",
        string="Profesional fijo",
        ondelete="restrict",
        help="Profesional que el sistema propondrá automáticamente al reservar este consultorio.",
    )
    user_id = fields.Many2one("res.users", string="Usuario vinculado")
    shared_with_organization_ids = fields.Many2many(
        "odental.organization",
        "odental_resource_shared_organization_rel",
        "resource_id",
        "organization_id",
        string="Disponible para organizaciones",
        help="Organizaciones independientes autorizadas para reservar este recurso.",
    )
    notes = fields.Text(string="Notas")

    @api.onchange("resource_type")
    def _onchange_resource_type(self):
        for resource in self:
            if resource.resource_type == "room":
                resource.includes_chair = True
            elif resource.includes_chair:
                resource.includes_chair = False
            if resource.resource_type != "room":
                resource.assignment_mode = "shift"
                resource.fixed_professional_id = False

    def is_available_to(self, organization):
        self.ensure_one()
        return self.organization_id == organization or organization in self.shared_with_organization_ids

    @api.constrains("organization_id", "site_id")
    def _check_site_owner(self):
        for resource in self:
            if resource.site_id.organization_id != resource.organization_id:
                raise ValidationError("El recurso y su sede deben pertenecer a la misma organización propietaria.")

    @api.constrains("resource_type", "assignment_mode", "fixed_professional_id", "organization_id")
    def _check_room_assignment(self):
        for resource in self:
            if resource.resource_type != "room":
                if resource.fixed_professional_id:
                    raise ValidationError("Solo un consultorio puede tener un profesional fijo.")
                continue
            if resource.assignment_mode == "fixed" and not resource.fixed_professional_id:
                raise ValidationError("Seleccione el profesional fijo de este consultorio.")
            if resource.assignment_mode != "fixed" and resource.fixed_professional_id:
                raise ValidationError("El profesional fijo solo aplica a la modalidad de asignación fija.")
            if (
                resource.fixed_professional_id
                and resource.organization_id not in resource.fixed_professional_id.organization_ids
            ):
                raise ValidationError("El profesional fijo no pertenece a la organización del consultorio.")
