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

    name = fields.Char(
        string="Nombre interno",
        required=True,
        help="Nombre corto utilizado para identificar y reservar este recurso en la agenda.",
    )
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
    brand = fields.Char(
        string="Marca",
        help="Fabricante o marca comercial del equipo.",
    )
    model = fields.Char(
        string="Modelo",
        help="Modelo comercial indicado por el fabricante.",
    )
    serial_number = fields.Char(
        string="Número de serie",
        copy=False,
        index=True,
        help="Número de serie único impreso en el equipo.",
    )
    inventory_code = fields.Char(
        string="Código de inventario",
        copy=False,
        index=True,
        help="Código interno o etiqueta patrimonial asignada por la clínica.",
    )
    equipment_status = fields.Selection(
        [
            ("available", "Disponible"),
            ("loaned", "Entregado"),
            ("maintenance", "En mantenimiento"),
            ("out_of_service", "Fuera de servicio"),
        ],
        string="Estado operativo",
        default="available",
        required=True,
        help="Indica si el equipo puede reservarse y utilizarse en este momento.",
    )
    current_condition = fields.Selection(
        [
            ("good", "Bueno"),
            ("fair", "Regular"),
            ("damaged", "Dañado"),
        ],
        string="Condición actual",
        default="good",
        required=True,
        help="Condición física general observada en la revisión más reciente.",
    )
    condition_notes = fields.Text(
        string="Detalles de la condición",
        help="Registre rayaduras, botones defectuosos, piezas faltantes u otros daños visibles.",
    )
    description = fields.Text(
        string="Descripción",
        help="Características, accesorios incluidos y restricciones de uso del equipo.",
    )
    image_1920 = fields.Image(string="Fotografía principal", max_width=1920, max_height=1920)
    photo_ids = fields.One2many(
        "odental.resource.photo", "resource_id", string="Fotografías"
    )
    handover_ids = fields.One2many(
        "odental.resource.handover", "resource_id", string="Entregas y devoluciones"
    )
    maintenance_ids = fields.One2many(
        "odental.resource.maintenance", "resource_id", string="Mantenimientos"
    )
    notes = fields.Text(
        string="Notas operativas",
        help="Información adicional para recepción o administración.",
    )

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


class ODentalResourcePhoto(models.Model):
    _name = "odental.resource.photo"
    _description = "Fotografía de equipo O Dental"
    _order = "taken_at desc, id desc"

    resource_id = fields.Many2one(
        "odental.resource", string="Equipo", required=True, ondelete="cascade", index=True
    )
    organization_id = fields.Many2one(
        related="resource_id.organization_id", store=True, index=True
    )
    name = fields.Char(string="Descripción", required=True, default="Fotografía del equipo")
    image_1920 = fields.Image(
        string="Fotografía", required=True, max_width=1920, max_height=1920
    )
    taken_at = fields.Datetime(string="Fecha", default=fields.Datetime.now, required=True)
    uploaded_by_id = fields.Many2one(
        "res.users", string="Registrada por", default=lambda self: self.env.user, readonly=True
    )


class ODentalResourceHandover(models.Model):
    _name = "odental.resource.handover"
    _description = "Entrega y devolución de equipo O Dental"
    _order = "delivered_at desc, id desc"

    resource_id = fields.Many2one(
        "odental.resource", string="Equipo", required=True, ondelete="cascade", index=True
    )
    organization_id = fields.Many2one(
        related="resource_id.organization_id", store=True, index=True
    )
    receiver_partner_id = fields.Many2one(
        "res.partner", string="Recibido por", required=True, ondelete="restrict"
    )
    delivered_at = fields.Datetime(
        string="Fecha y hora de entrega", default=fields.Datetime.now, required=True
    )
    delivered_by_id = fields.Many2one(
        "res.users", string="Entregado por", default=lambda self: self.env.user, required=True
    )
    checkout_condition = fields.Selection(
        [("good", "Bueno"), ("fair", "Regular"), ("damaged", "Dañado")],
        string="Condición al entregar",
        required=True,
        default="good",
    )
    checkout_notes = fields.Text(string="Observaciones de entrega")
    returned_at = fields.Datetime(string="Fecha y hora de devolución")
    returned_to_id = fields.Many2one("res.users", string="Recibido de vuelta por")
    return_condition = fields.Selection(
        [("good", "Bueno"), ("fair", "Regular"), ("damaged", "Dañado")],
        string="Condición al devolver",
    )
    return_notes = fields.Text(string="Observaciones de devolución")
    state = fields.Selection(
        [("open", "Entregado"), ("returned", "Devuelto")],
        string="Estado",
        compute="_compute_state",
        store=True,
    )

    @api.depends("returned_at")
    def _compute_state(self):
        for handover in self:
            handover.state = "returned" if handover.returned_at else "open"

    @api.model_create_multi
    def create(self, vals_list):
        handovers = super().create(vals_list)
        for handover in handovers:
            if handover.resource_id.resource_type != "equipment":
                raise ValidationError("Las entregas y devoluciones solo aplican a equipos.")
            other_open = self.search_count(
                [
                    ("resource_id", "=", handover.resource_id.id),
                    ("id", "!=", handover.id),
                    ("returned_at", "=", False),
                ]
            )
            if other_open:
                raise ValidationError("Este equipo ya tiene una entrega pendiente de devolución.")
            if handover.returned_at:
                handover.resource_id.write(
                    {
                        "equipment_status": "available",
                        "current_condition": handover.return_condition,
                        "condition_notes": handover.return_notes,
                    }
                )
            else:
                handover.resource_id.write(
                    {
                        "equipment_status": "loaned",
                        "current_condition": handover.checkout_condition,
                        "condition_notes": handover.checkout_notes,
                    }
                )
        return handovers

    def write(self, vals):
        result = super().write(vals)
        for handover in self.filtered("returned_at"):
            handover.resource_id.write(
                {
                    "equipment_status": "available",
                    "current_condition": handover.return_condition,
                    "condition_notes": handover.return_notes,
                }
            )
        return result

    @api.onchange("returned_at")
    def _onchange_returned_at(self):
        for handover in self:
            if handover.returned_at:
                handover.returned_to_id = handover.returned_to_id or self.env.user
                handover.return_condition = (
                    handover.return_condition or handover.resource_id.current_condition
                )

    @api.constrains("delivered_at", "returned_at", "return_condition", "returned_to_id")
    def _check_return(self):
        for handover in self:
            if handover.returned_at and handover.returned_at < handover.delivered_at:
                raise ValidationError("La devolución no puede ser anterior a la entrega.")
            if handover.returned_at and (not handover.return_condition or not handover.returned_to_id):
                raise ValidationError(
                    "Al registrar la devolución indique la condición y quién recibió el equipo."
                )


class ODentalResourceMaintenance(models.Model):
    _name = "odental.resource.maintenance"
    _description = "Mantenimiento de equipo O Dental"
    _order = "start_date desc, id desc"

    resource_id = fields.Many2one(
        "odental.resource", string="Equipo", required=True, ondelete="cascade", index=True
    )
    organization_id = fields.Many2one(
        related="resource_id.organization_id", store=True, index=True
    )
    maintenance_type = fields.Selection(
        [("preventive", "Preventivo"), ("corrective", "Correctivo")],
        string="Tipo",
        required=True,
        default="preventive",
    )
    state = fields.Selection(
        [
            ("planned", "Planificado"),
            ("in_progress", "En proceso"),
            ("done", "Finalizado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        required=True,
        default="planned",
    )
    start_date = fields.Date(string="Fecha de inicio", default=fields.Date.context_today, required=True)
    end_date = fields.Date(string="Fecha de finalización")
    provider_partner_id = fields.Many2one("res.partner", string="Proveedor o técnico")
    issue_description = fields.Text(string="Falla o motivo", required=True)
    work_performed = fields.Text(string="Trabajo realizado")
    cost = fields.Monetary(string="Costo")
    currency_id = fields.Many2one(
        related="resource_id.company_id.currency_id", readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        maintenances = super().create(vals_list)
        for maintenance in maintenances:
            if maintenance.resource_id.resource_type != "equipment":
                raise ValidationError("El historial de mantenimiento solo aplica a equipos.")
            maintenance._sync_resource_status()
        return maintenances

    def write(self, vals):
        result = super().write(vals)
        if "state" in vals:
            self._sync_resource_status()
        return result

    def _sync_resource_status(self):
        for maintenance in self:
            resource = maintenance.resource_id
            if maintenance.state == "in_progress":
                resource.equipment_status = "maintenance"
            elif (
                maintenance.state in {"done", "cancelled"}
                and resource.equipment_status == "maintenance"
            ):
                has_other_active = self.search_count(
                    [
                        ("resource_id", "=", resource.id),
                        ("id", "!=", maintenance.id),
                        ("state", "=", "in_progress"),
                    ]
                )
                if not has_other_active:
                    resource.equipment_status = "available"

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for maintenance in self:
            if maintenance.end_date and maintenance.end_date < maintenance.start_date:
                raise ValidationError("La fecha de finalización no puede ser anterior al inicio.")
