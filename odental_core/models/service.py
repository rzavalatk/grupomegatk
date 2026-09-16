from odoo import api, fields, models


class ODentalService(models.Model):
    _name = "odental.service"
    _description = "Servicio clínico O Dental"
    _order = "name"

    name = fields.Char(string="Nombre del servicio", required=True, tracking=True)
    code = fields.Char(string="Código interno", required=True, index=True)
    active = fields.Boolean(string="Activo", default=True)
    organization_id = fields.Many2one(
        "odental.organization", string="Organización", required=True,
        ondelete="cascade", index=True,
    )
    company_id = fields.Many2one(
        related="organization_id.company_id", string="Empresa de facturación",
        store=True, index=True,
    )
    duration_minutes = fields.Integer(
        string="Duración de la atención (minutos)", required=True, default=30,
        help="Tiempo clínico habitual que se reservará en la agenda.",
    )
    preparation_minutes = fields.Integer(
        string="Preparación previa (minutos)", default=0,
        help="Tiempo que debe bloquearse antes de la cita para preparar el consultorio.",
    )
    cleaning_minutes = fields.Integer(
        string="Limpieza posterior (minutos)", default=0,
        help="Tiempo que debe bloquearse después de la cita para limpieza y desinfección.",
    )
    require_room = fields.Boolean(
        string="Requiere consultorio", default=True,
        help="Exige reservar un consultorio físico para poder programar la cita.",
    )
    require_chair = fields.Boolean(
        string="Requiere sillón o unidad dental", default=True,
        help="Exige un consultorio que incluya sillón o una unidad dental reservada por separado.",
    )
    require_assistant = fields.Boolean(
        string="Requiere asistente", default=False,
        help="Actívelo solo cuando la cita no pueda programarse sin una persona asignada como asistente.",
    )
    require_equipment = fields.Boolean(
        string="Requiere equipo adicional", default=False,
        help="Exige reservar al menos un equipo compartido además del consultorio.",
    )
    professional_duration_ids = fields.One2many(
        "odental.service.duration", "service_id", string="Duración por profesional",
        help="Use esta tabla únicamente cuando un profesional necesite una duración distinta a la general.",
    )

    _sql_constraints = [
        ("code_organization_unique", "unique(code, organization_id)", "El código debe ser único por organización."),
        ("duration_positive", "check(duration_minutes > 0)", "La duración debe ser mayor que cero."),
        ("preparation_nonnegative", "check(preparation_minutes >= 0)", "La preparación no puede ser negativa."),
        ("cleaning_nonnegative", "check(cleaning_minutes >= 0)", "La limpieza no puede ser negativa."),
    ]

    def duration_for(self, professional):
        self.ensure_one()
        override = self.professional_duration_ids.filtered(lambda line: line.professional_id == professional)[:1]
        return override.duration_minutes if override else self.duration_minutes


class ODentalServiceDuration(models.Model):
    _name = "odental.service.duration"
    _description = "Duración de servicio por profesional"

    service_id = fields.Many2one("odental.service", required=True, ondelete="cascade")
    professional_id = fields.Many2one("odental.professional", required=True, ondelete="cascade")
    duration_minutes = fields.Integer(required=True)

    _sql_constraints = [
        ("service_professional_unique", "unique(service_id, professional_id)", "Ya existe una duración para este profesional."),
        ("duration_positive", "check(duration_minutes > 0)", "La duración debe ser mayor que cero."),
    ]
