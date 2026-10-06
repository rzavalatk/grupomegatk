from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class ODentalAppointment(models.Model):
    _name = "odental.appointment"
    _description = "Cita O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_datetime desc"

    name = fields.Char(string="Número de cita", default="Nuevo", readonly=True, copy=False, index=True)
    entry_type = fields.Selection(
        [("clinical", "Cita clínica"), ("busy", "No disponible")],
        default="clinical", required=True, index=True,
    )
    active = fields.Boolean(string="Activo", default=True)
    organization_id = fields.Many2one(
        "odental.organization", string="Organización", required=True, ondelete="restrict", index=True
    )
    company_id = fields.Many2one(
        related="organization_id.company_id", string="Compañía", store=True, index=True
    )
    patient_id = fields.Many2one(
        "odental.patient", string="Paciente", ondelete="restrict", index=True, tracking=True
    )
    professional_id = fields.Many2one(
        "odental.professional", string="Profesional responsable", required=True,
        ondelete="restrict", index=True, tracking=True
    )
    service_id = fields.Many2one(
        "odental.service", string="Servicio", ondelete="restrict", tracking=True
    )
    service_requires_assistant = fields.Boolean(
        related="service_id.require_assistant",
        string="El servicio requiere asistente",
        readonly=True,
    )
    site_id = fields.Many2one(
        "odental.site", string="Sede", ondelete="restrict"
    )
    resource_ids = fields.Many2many(
        "odental.resource", "odental_appointment_resource_rel", "appointment_id", "resource_id",
        string="Recursos reservados"
    )
    participant_line_ids = fields.One2many(
        "odental.appointment.participant",
        "appointment_id",
        string="Personas asignadas al turno",
        copy=True,
    )
    available_participant_user_ids = fields.Many2many(
        "res.users",
        compute="_compute_available_participant_users",
        string="Usuarios disponibles",
    )
    start_datetime = fields.Datetime(string="Fecha y hora de inicio", required=True, index=True, tracking=True)
    duration_minutes = fields.Integer(string="Duración (minutos)", required=True, default=30, tracking=True)
    preparation_minutes = fields.Integer(string="Preparación previa (minutos)", default=0)
    cleaning_minutes = fields.Integer(string="Limpieza posterior (minutos)", default=0)
    end_datetime = fields.Datetime(string="Fecha y hora de finalización", compute="_compute_datetimes", store=True, index=True)
    blocking_start = fields.Datetime(string="Inicio del bloqueo", compute="_compute_datetimes", store=True, index=True)
    blocking_end = fields.Datetime(string="Fin del bloqueo", compute="_compute_datetimes", store=True, index=True)
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("scheduled", "Programada"),
            ("confirmed", "Confirmada"),
            ("in_progress", "En atención"),
            ("done", "Finalizada"),
            ("cancelled", "Cancelada"),
            ("no_show", "No asistió"),
        ],
        string="Estado", default="draft", required=True, index=True, tracking=True
    )
    notes = fields.Text(string="Notas")
    external_source = fields.Selection([("todoist", "Todoist")], copy=False, readonly=True)
    external_uid = fields.Char(copy=False, readonly=True, index=True)
    external_conflict = fields.Boolean(string="Conflicto clínico", copy=False, readonly=True)
    last_schedule_changed_by = fields.Many2one(
        "res.users", string="Último cambio de agenda por", readonly=True, copy=False
    )
    last_schedule_change_source = fields.Selection(
        [("odoo", "O Dental"), ("todoist", "Todoist")],
        string="Origen del último cambio", readonly=True, copy=False,
    )
    last_schedule_changed_at = fields.Datetime(
        string="Fecha del último cambio de agenda", readonly=True, copy=False
    )
    schedule_audit_ids = fields.One2many(
        "odental.appointment.audit", "appointment_id", string="Historial de agenda", readonly=True
    )

    _SCHEDULE_FIELDS = (
        "start_datetime", "duration_minutes", "professional_id", "site_id",
        "state", "entry_type", "patient_id", "service_id", "resource_ids",
        "preparation_minutes", "cleaning_minutes", "active",
    )

    _sql_constraints = [
        ("external_busy_unique", "unique(organization_id, professional_id, external_source, external_uid)",
         "Este bloqueo externo ya está registrado para el profesional."),
    ]

    @api.depends(
        "organization_id",
        "organization_id.user_ids",
        "organization_id.professional_ids.user_id",
    )
    def _compute_available_participant_users(self):
        for appointment in self:
            organization = appointment.organization_id
            appointment.available_participant_user_ids = (
                organization.user_ids
                | organization.owner_user_id
                | organization.professional_ids.mapped("user_id")
            ) if organization else False

    @api.depends("start_datetime", "duration_minutes", "preparation_minutes", "cleaning_minutes")
    def _compute_datetimes(self):
        for appointment in self:
            if not appointment.start_datetime:
                appointment.end_datetime = False
                appointment.blocking_start = False
                appointment.blocking_end = False
                continue
            appointment.end_datetime = appointment.start_datetime + timedelta(minutes=appointment.duration_minutes)
            appointment.blocking_start = appointment.start_datetime - timedelta(minutes=appointment.preparation_minutes)
            appointment.blocking_end = appointment.end_datetime + timedelta(minutes=appointment.cleaning_minutes)

    @api.onchange("service_id", "professional_id")
    def _onchange_service_professional(self):
        if self.service_id:
            self.duration_minutes = self.service_id.duration_for(self.professional_id) if self.professional_id else self.service_id.duration_minutes
            self.preparation_minutes = self.service_id.preparation_minutes
            self.cleaning_minutes = self.service_id.cleaning_minutes

    @api.onchange("resource_ids")
    def _onchange_fixed_room(self):
        fixed_rooms = self.resource_ids.filtered(
            lambda resource: resource.resource_type == "room"
            and resource.assignment_mode == "fixed"
            and resource.fixed_professional_id
        )
        fixed_professionals = fixed_rooms.mapped("fixed_professional_id")
        if len(fixed_professionals) == 1:
            self.professional_id = fixed_professionals
            if fixed_professionals.user_id and not self.participant_line_ids:
                self.participant_line_ids = [
                    (0, 0, {"role": "operator", "user_id": fixed_professionals.user_id.id})
                ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not self.env.is_superuser() and set(vals).intersection({
                "last_schedule_changed_by", "last_schedule_change_source",
                "last_schedule_changed_at", "schedule_audit_ids",
            }):
                raise AccessError("El historial de cambios de agenda se actualiza automáticamente.")
            if vals.get("entry_type") == "busy" and not self.env.is_superuser():
                raise AccessError("Los bloqueos externos solo se crean mediante la sincronización autorizada.")
            if vals.get("entry_type") == "busy":
                vals["name"] = "No disponible"
                vals["state"] = "scheduled"
            elif vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("odental.appointment") or "Nuevo"
            self._apply_fixed_room_professional(vals)
            self._apply_service_defaults(vals)
        appointments = super().create(vals_list)
        if not (self.env.is_superuser() and self.env.context.get("odental_skip_schedule_audit")):
            for appointment in appointments:
                appointment._record_schedule_change("created", {}, appointment._schedule_snapshot())
        return appointments

    def write(self, vals):
        if not self.env.is_superuser() and set(vals).intersection({
            "last_schedule_changed_by", "last_schedule_change_source",
            "last_schedule_changed_at", "schedule_audit_ids",
        }):
            raise AccessError("El historial de cambios de agenda se actualiza automáticamente.")
        if not self.env.is_superuser() and self.filtered(lambda item: item.entry_type == "busy"):
            raise AccessError("El bloqueo se actualiza desde el calendario personal del profesional.")
        if vals.get("entry_type") == "busy" and not self.env.is_superuser():
            raise AccessError("No puede convertir una cita clínica en un bloqueo externo.")
        if (self.env.is_superuser() and self.env.context.get("odental_skip_schedule_audit")) or not set(vals).intersection(self._SCHEDULE_FIELDS):
            return super().write(vals)
        previous = {appointment.id: appointment._schedule_snapshot() for appointment in self}
        result = super().write(vals)
        for appointment in self:
            current = appointment._schedule_snapshot()
            before = previous[appointment.id]
            changed = [key for key in self._SCHEDULE_FIELDS if before[key] != current[key]]
            if changed:
                event = "cancelled" if current["state"] == "cancelled" and before["state"] != "cancelled" else "changed"
                appointment._record_schedule_change(
                    event, {key: before[key] for key in changed},
                    {key: current[key] for key in changed},
                )
        return result

    def unlink(self):
        if not self.env.is_superuser() and self.filtered(lambda item: item.entry_type == "busy"):
            raise AccessError("Los bloqueos externos no se eliminan desde la agenda clínica.")
        for appointment in self:
            appointment._record_schedule_change("deleted", appointment._schedule_snapshot(), {})
        return super().unlink()

    def _schedule_snapshot(self):
        self.ensure_one()
        result = {}
        for key in self._SCHEDULE_FIELDS:
            value = self[key]
            if key == "resource_ids":
                value = sorted(value.ids)
            elif isinstance(value, models.BaseModel):
                value = value.id or False
            elif key == "start_datetime":
                value = fields.Datetime.to_string(value) if value else False
            result[key] = value
        return result

    def _record_schedule_change(self, event, before, after):
        self.ensure_one()
        source = "odoo"
        actor_id = self.env.user.id
        if self.env.is_superuser() and self.env.context.get("odental_audit_source") == "todoist":
            source = "todoist"
            # Only the user attached to this appointment's professional can
            # be attributed to an external edit. Otherwise show the source
            # without inventing a human actor.
            doctor = self.professional_id.user_id
            actor_id = doctor.id if doctor.id == self.env.context.get("odental_audit_actor_user_id") else False
        now = fields.Datetime.now()
        self.env["odental.appointment.audit"].sudo().create({
            "appointment_id": self.id,
            "appointment_reference": self.name,
            "organization_id": self.organization_id.id,
            "company_id": self.company_id.id,
            "professional_id": self.professional_id.id,
            "actor_user_id": actor_id,
            "source": source,
            "event": event,
            "changed_at": now,
            "old_values": before,
            "new_values": after,
        })
        if event != "deleted":
            self.with_context(odental_skip_schedule_audit=True).sudo().write({
                "last_schedule_changed_by": actor_id,
                "last_schedule_change_source": source,
                "last_schedule_changed_at": now,
            })

    @api.model
    def _apply_fixed_room_professional(self, vals):
        if vals.get("professional_id") or not vals.get("resource_ids"):
            return
        resource_ids = set()
        for command in vals["resource_ids"]:
            if command[0] == 6:
                resource_ids.update(command[2])
            elif command[0] == 4:
                resource_ids.add(command[1])
        rooms = self.env["odental.resource"].browse(resource_ids).filtered(
            lambda resource: resource.resource_type == "room"
            and resource.assignment_mode == "fixed"
            and resource.fixed_professional_id
        )
        professionals = rooms.mapped("fixed_professional_id")
        if len(professionals) == 1:
            vals["professional_id"] = professionals.id
            if professionals.user_id and not vals.get("participant_line_ids"):
                vals["participant_line_ids"] = [
                    (0, 0, {"role": "operator", "user_id": professionals.user_id.id})
                ]

    @api.model
    def _apply_service_defaults(self, vals):
        if not vals.get("service_id"):
            return
        service = self.env["odental.service"].browse(vals["service_id"])
        professional = self.env["odental.professional"].browse(vals.get("professional_id"))
        vals.setdefault("duration_minutes", service.duration_for(professional) if professional else service.duration_minutes)
        vals.setdefault("preparation_minutes", service.preparation_minutes)
        vals.setdefault("cleaning_minutes", service.cleaning_minutes)

    @api.constrains(
        "organization_id", "patient_id", "professional_id", "service_id", "site_id",
        "resource_ids", "start_datetime", "duration_minutes", "preparation_minutes",
        "cleaning_minutes", "state", "entry_type"
    )
    def _check_appointment(self):
        blocking_states = ("scheduled", "confirmed", "in_progress")
        for appointment in self:
            if appointment.duration_minutes <= 0 or appointment.preparation_minutes < 0 or appointment.cleaning_minutes < 0:
                raise ValidationError("Las duraciones de la cita no son válidas.")
            if appointment.entry_type == "busy":
                if appointment.patient_id or appointment.service_id or appointment.site_id or appointment.resource_ids:
                    raise ValidationError("Un bloqueo privado no puede contener datos clínicos o recursos.")
                if appointment.professional_id not in appointment.organization_id.professional_ids:
                    raise ValidationError("El profesional no pertenece a la organización del bloqueo.")
                continue
            if not appointment.patient_id or not appointment.service_id or not appointment.site_id:
                raise ValidationError("La cita clínica requiere paciente, servicio y sede.")
            if appointment.patient_id.organization_id != appointment.organization_id:
                raise ValidationError("El paciente no pertenece a la organización de la cita.")
            if appointment.service_id.organization_id != appointment.organization_id:
                raise ValidationError("El servicio no pertenece a la organización de la cita.")
            if not appointment.site_id.is_available_to(appointment.organization_id):
                raise ValidationError("La sede no está disponible para la organización de la cita.")
            if appointment.professional_id not in appointment.organization_id.mapped("professional_ids"):
                raise ValidationError("El profesional no está autorizado en esta organización.")
            if any(not resource.is_available_to(appointment.organization_id) for resource in appointment.resource_ids):
                raise ValidationError("Uno o más recursos no están disponibles para la organización de la cita.")
            if any(resource.site_id != appointment.site_id for resource in appointment.resource_ids):
                raise ValidationError("Todos los recursos deben pertenecer a la sede seleccionada.")
            if appointment.state not in blocking_states or not appointment.blocking_start or not appointment.blocking_end:
                continue
            appointment._check_required_resources()
            if self.sudo().search_count([
                ("id", "!=", appointment.id),
                ("entry_type", "=", "busy"),
                ("state", "in", blocking_states),
                ("professional_id", "=", appointment.professional_id.id),
                ("blocking_start", "<", appointment.blocking_end),
                ("blocking_end", ">", appointment.blocking_start),
            ]):
                raise ValidationError("El profesional no está disponible durante este horario.")
            base_domain = [
                ("id", "!=", appointment.id),
                ("entry_type", "=", "clinical"),
                ("state", "in", blocking_states),
                ("blocking_start", "<", appointment.blocking_end),
                ("blocking_end", ">", appointment.blocking_start),
            ]
            # Availability spans clinics sharing staff or resources. Read only
            # for conflict detection; never return the other clinic's records.
            same_professional = self.sudo().search(
                base_domain + [("professional_id", "=", appointment.professional_id.id)]
            )
            if same_professional and any(
                not (
                    appointment._responsible_is_supervisor()
                    and other._responsible_is_supervisor()
                )
                for other in same_professional
            ):
                raise ValidationError("El profesional ya tiene otra cita durante este horario.")
            if appointment.resource_ids and self.sudo().search_count(base_domain + [("resource_ids", "in", appointment.resource_ids.ids)]):
                raise ValidationError("Uno o más recursos ya están reservados durante este horario.")
            appointment._check_participant_conflicts()

    def _responsible_is_supervisor(self):
        self.ensure_one()
        user = self.professional_id.user_id
        return bool(
            user
            and self.participant_line_ids.filtered(
                lambda line: line.user_id == user and line.role == "supervisor"
            )
        )

    def _check_participant_conflicts(self):
        self.ensure_one()
        exclusive_roles = {"operator", "assistant"}
        exclusive_users = self.participant_line_ids.filtered(
            lambda line: line.role in exclusive_roles
        ).mapped("user_id")
        if not exclusive_users:
            return
        # Return a generic availability error, without exposing other patients.
        conflict = self.env["odental.appointment.participant"].sudo().search_count(
            [
                ("appointment_id", "!=", self.id),
                ("appointment_id.state", "in", ("scheduled", "confirmed", "in_progress")),
                ("appointment_id.blocking_start", "<", self.blocking_end),
                ("appointment_id.blocking_end", ">", self.blocking_start),
                ("role", "in", tuple(exclusive_roles)),
                ("user_id", "in", exclusive_users.ids),
            ]
        )
        if conflict:
            raise ValidationError(
                "Un operador o asistente ya está asignado a otra atención durante este horario."
            )

    def _check_required_resources(self):
        self.ensure_one()
        present_types = set(self.resource_ids.mapped("resource_type"))
        if any(
            resource.resource_type == "room" and resource.includes_chair
            for resource in self.resource_ids
        ):
            present_types.add("chair")
        if self.participant_line_ids.filtered(lambda line: line.role == "assistant"):
            present_types.add("assistant")
        requirements = {
            "room": self.service_id.require_room,
            "chair": self.service_id.require_chair,
            "assistant": self.service_id.require_assistant,
            "equipment": self.service_id.require_equipment,
        }
        missing = [resource_type for resource_type, required in requirements.items() if required and resource_type not in present_types]
        if missing:
            labels = dict(self.env["odental.resource"]._fields["resource_type"].selection)
            missing_labels = ", ".join(labels[item] for item in missing)
            raise ValidationError(
                "El servicio «%s» requiere los siguientes recursos: %s. "
                "Revise la configuración del servicio o asígnelos a la cita."
                % (self.service_id.display_name, missing_labels)
            )

    def action_schedule(self):
        self.write({"state": "scheduled"})

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_start(self):
        self.write({"state": "in_progress"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancelled"})


class ODentalAppointmentParticipant(models.Model):
    _name = "odental.appointment.participant"
    _description = "Participante de turno O Dental"
    _order = "role, id"

    appointment_id = fields.Many2one(
        "odental.appointment", required=True, ondelete="cascade", index=True
    )
    organization_id = fields.Many2one(
        related="appointment_id.organization_id", store=True, index=True
    )
    user_id = fields.Many2one(
        "res.users", string="Usuario", required=True, ondelete="restrict", index=True
    )
    role = fields.Selection(
        [
            ("operator", "Operador principal"),
            ("assistant", "Asistente"),
            ("supervisor", "Supervisor"),
            ("observer", "Observador"),
        ],
        string="Función",
        required=True,
        default="operator",
        index=True,
    )
    notes = fields.Char(string="Observaciones")

    _sql_constraints = [
        (
            "appointment_user_unique",
            "unique(appointment_id, user_id)",
            "El usuario ya está asignado a esta cita.",
        )
    ]

    @api.constrains("appointment_id", "user_id", "role")
    def _check_user_organization(self):
        for participant in self:
            organization = participant.appointment_id.organization_id
            if (
                participant.user_id != organization.owner_user_id
                and participant.user_id not in organization.user_ids
            ):
                raise ValidationError("El usuario no está autorizado en la organización de la cita.")
            if participant.appointment_id.state in {"scheduled", "confirmed", "in_progress"}:
                participant.appointment_id._check_participant_conflicts()


class ODentalOrganizationProfessional(models.Model):
    _inherit = "odental.organization"

    professional_ids = fields.Many2many(
        "odental.professional", "odental_professional_organization_rel",
        "organization_id", "professional_id", string="Profesionales"
    )
