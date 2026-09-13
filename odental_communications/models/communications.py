from datetime import timedelta
from string import Formatter
from uuid import uuid4

import pytz

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


MESSAGE_TYPES = [
    ("confirmation", "Solicitud de confirmación"),
    ("reminder", "Recordatorio"),
    ("confirmed", "Confirmación recibida"),
    ("rescheduled", "Reprogramación"),
    ("cancellation", "Cancelación"),
    ("waitlist_offer", "Oferta de espacio disponible"),
    ("waitlist_booked", "Espacio reservado"),
    ("reactivation", "Reactivación"),
]

CHANNELS = [
    ("whatsapp", "WhatsApp"),
    ("email", "Correo electrónico"),
    ("phone", "Llamada telefónica"),
    ("none", "Sin comunicaciones"),
]

DEFAULT_BODIES = {
    "confirmation": (
        "Hola {patient_name}. Por favor confirme su cita de {service_name} con "
        "{professional_name} para el {appointment_datetime}."
    ),
    "reminder": (
        "Recordatorio O Dental: {patient_name}, su cita de {service_name} es el "
        "{appointment_datetime} con {professional_name}."
    ),
    "confirmed": (
        "Su cita de {service_name} para el {appointment_datetime} quedó confirmada."
    ),
    "rescheduled": (
        "Su cita de {service_name} fue reprogramada para el {appointment_datetime}. "
        "Por favor confirme nuevamente su asistencia."
    ),
    "cancellation": (
        "La cita de {service_name} programada para el {appointment_datetime} fue cancelada."
    ),
    "waitlist_offer": (
        "Se liberó un espacio para {service_name} el {appointment_datetime}. "
        "La oferta vence el {offer_expires_at}."
    ),
    "waitlist_booked": (
        "El espacio para {service_name} del {appointment_datetime} quedó reservado a su nombre."
    ),
    "reactivation": (
        "Hola {patient_name}. O Dental le recuerda que puede programar su próxima atención."
    ),
}

ALLOWED_PLACEHOLDERS = {
    "patient_name", "service_name", "professional_name", "organization_name",
    "appointment_datetime", "offer_expires_at",
}

TIMEZONES = [(timezone, timezone) for timezone in pytz.all_timezones]


class ODentalOrganization(models.Model):
    _inherit = "odental.organization"

    reminder_hours_before = fields.Integer(
        string="Horas antes del recordatorio", default=24
    )
    waitlist_offer_minutes = fields.Integer(
        string="Vigencia de oferta de lista de espera", default=30
    )
    automatic_appointment_messages = fields.Boolean(
        string="Preparar mensajes automáticamente", default=True,
        help="Crea mensajes en la bandeja de salida. No los envía sin un conector autorizado.",
    )
    communication_timezone = fields.Selection(
        TIMEZONES, string="Zona horaria de comunicaciones",
        required=True, default=lambda self: self.env.user.tz or "UTC",
    )

    @api.constrains("reminder_hours_before", "waitlist_offer_minutes")
    def _check_communication_times(self):
        for organization in self:
            if organization.reminder_hours_before < 1:
                raise ValidationError("El recordatorio debe prepararse al menos una hora antes.")
            if organization.waitlist_offer_minutes < 5:
                raise ValidationError("La oferta de lista de espera debe durar al menos cinco minutos.")


class ODentalPatient(models.Model):
    _inherit = "odental.patient"

    preferred_appointment_channel = fields.Selection(
        CHANNELS, string="Canal para citas", default="whatsapp", tracking=True
    )
    appointment_messages_consent = fields.Boolean(
        string="Autoriza mensajes de citas", tracking=True
    )
    appointment_messages_consent_at = fields.Datetime(
        string="Consentimiento registrado", readonly=True, copy=False
    )
    appointment_messages_consent_source = fields.Char(
        string="Origen del consentimiento", copy=False,
        help="Ejemplo: formulario de ingreso, portal del paciente o autorización presencial.",
    )
    communication_consent_event_ids = fields.One2many(
        "odental.communication.consent.event", "patient_id",
        string="Historial de autorización", readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        consent_values = []
        for vals in vals_list:
            granted = bool(vals.get("appointment_messages_consent"))
            if granted:
                vals["appointment_messages_consent_at"] = fields.Datetime.now()
            consent_values.append(granted)
        patients = super().create(vals_list)
        for patient, granted in zip(patients, consent_values):
            if granted:
                patient._log_communication_consent("granted")
        return patients

    def write(self, vals):
        consent_change = "appointment_messages_consent" in vals
        channel_change = "preferred_appointment_channel" in vals
        previous_consent = {patient.id: patient.appointment_messages_consent for patient in self}
        previous_channel = {patient.id: patient.preferred_appointment_channel for patient in self}
        values = dict(vals)
        if channel_change and not consent_change and any(previous_consent.values()):
            values["appointment_messages_consent"] = False
            consent_change = True
        if consent_change:
            values["appointment_messages_consent_at"] = (
                fields.Datetime.now() if values.get("appointment_messages_consent") else False
            )
        result = super().write(values)
        if (consent_change or channel_change) and not self.env.context.get("odental_consent_event"):
            for patient in self:
                new_value = patient.appointment_messages_consent
                old_value = previous_consent[patient.id]
                old_channel = previous_channel[patient.id]
                if old_value and (not new_value or old_channel != patient.preferred_appointment_channel):
                    patient._log_communication_consent("revoked", channel=old_channel)
                if new_value and (not old_value or old_channel != patient.preferred_appointment_channel):
                    patient._log_communication_consent("granted")
        return result

    def _log_communication_consent(self, event_type, channel=False):
        for patient in self:
            self.env["odental.communication.consent.event"].sudo().with_context(
                odental_consent_event=True
            ).create({
                "patient_id": patient.id,
                "event_type": event_type,
                "channel": channel or patient.preferred_appointment_channel,
                "source": patient.appointment_messages_consent_source or "Registro interno",
                "user_id": self.env.user.id,
            })

    def _communication_recipient(self):
        self.ensure_one()
        if self.preferred_appointment_channel == "whatsapp":
            return self.mobile
        if self.preferred_appointment_channel == "email":
            return self.email
        if self.preferred_appointment_channel == "phone":
            return self.mobile
        return False


class ODentalCommunicationConsentEvent(models.Model):
    _name = "odental.communication.consent.event"
    _description = "Evento de consentimiento de comunicaciones O Dental"
    _order = "occurred_at desc, id desc"

    patient_id = fields.Many2one("odental.patient", required=True, ondelete="cascade", index=True)
    organization_id = fields.Many2one(related="patient_id.organization_id", store=True, index=True)
    event_type = fields.Selection(
        [("granted", "Otorgado"), ("revoked", "Revocado")], required=True, readonly=True
    )
    channel = fields.Selection(CHANNELS, required=True, readonly=True)
    source = fields.Char(required=True, readonly=True)
    occurred_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    user_id = fields.Many2one("res.users", required=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("odental_consent_event"):
            raise AccessError("El historial de autorizaciones solo se genera desde el paciente.")
        return super().create(vals_list)

    def write(self, vals):
        raise UserError("El historial de autorizaciones es inmutable.")

    def unlink(self):
        raise UserError("El historial de autorizaciones es inmutable.")


class ODentalCommunicationTemplate(models.Model):
    _name = "odental.communication.template"
    _description = "Plantilla de comunicación O Dental"
    _order = "organization_id, message_type, channel"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    organization_id = fields.Many2one("odental.organization", required=True, ondelete="cascade", index=True)
    message_type = fields.Selection(MESSAGE_TYPES, required=True, index=True)
    channel = fields.Selection(CHANNELS, required=True, default="whatsapp")
    body = fields.Text(required=True)

    _sql_constraints = [
        (
            "organization_type_channel_unique", "unique(organization_id, message_type, channel)",
            "Ya existe una plantilla para este tipo y canal en la organización.",
        )
    ]

    @api.constrains("body")
    def _check_placeholders(self):
        for template in self:
            try:
                placeholders = {
                    field_name for _, field_name, _, _ in Formatter().parse(template.body)
                    if field_name
                }
            except ValueError as exc:
                raise ValidationError("La plantilla contiene llaves sin cerrar.") from exc
            unknown = placeholders - ALLOWED_PLACEHOLDERS
            if unknown:
                raise ValidationError(
                    "Variables no permitidas: %s" % ", ".join(sorted(unknown))
                )


class ODentalCommunicationMessage(models.Model):
    _name = "odental.communication.message"
    _description = "Mensaje O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scheduled_at desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="restrict", index=True, readonly=True
    )
    patient_id = fields.Many2one(
        "odental.patient", required=True, ondelete="restrict", index=True, readonly=True
    )
    appointment_id = fields.Many2one(
        "odental.appointment", ondelete="cascade", index=True, readonly=True
    )
    slot_offer_id = fields.Many2one(
        "odental.slot.offer", ondelete="cascade", index=True, readonly=True
    )
    message_type = fields.Selection(MESSAGE_TYPES, required=True, index=True, readonly=True)
    channel = fields.Selection(CHANNELS, required=True, readonly=True)
    recipient = fields.Char(readonly=True)
    body = fields.Text(required=True, readonly=True)
    scheduled_at = fields.Datetime(
        required=True, default=fields.Datetime.now, index=True, readonly=True
    )
    sent_at = fields.Datetime(readonly=True, copy=False)
    delivered_at = fields.Datetime(readonly=True, copy=False)
    state = fields.Selection(
        [("queued", "En cola"), ("blocked", "Bloqueado"), ("sent", "Enviado"),
         ("delivered", "Entregado"), ("failed", "Fallido"), ("cancelled", "Cancelado")],
        required=True, default="queued", tracking=True, index=True
    )
    blocking_reason = fields.Char(readonly=True)
    external_reference = fields.Char(readonly=True, copy=False, index=True)
    attempt_count = fields.Integer(readonly=True, copy=False)
    last_error = fields.Text(readonly=True, copy=False)
    deduplication_key = fields.Char(required=True, readonly=True, copy=False, index=True)

    _sql_constraints = [
        (
            "deduplication_key_unique", "unique(deduplication_key)",
            "Este mensaje ya fue preparado.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("odental_message_create"):
            raise AccessError("Los mensajes solo se generan desde los flujos de O Dental.")
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.communication.message"
                ) or "Nuevo"
        return super().create(vals_list)

    def write(self, vals):
        protected = {
            "organization_id", "patient_id", "appointment_id", "slot_offer_id",
            "message_type", "channel", "recipient", "body", "scheduled_at",
            "deduplication_key",
            "state", "sent_at", "delivered_at", "external_reference",
            "attempt_count", "last_error", "blocking_reason",
        }
        if protected.intersection(vals) and not self.env.context.get("odental_message_transition"):
            raise UserError("Utilice las acciones del mensaje para actualizar su entrega.")
        return super().write(vals)

    def action_mark_sent(self):
        for message in self:
            if message.state not in {"queued", "failed"}:
                raise UserError("Solo un mensaje pendiente o fallido puede marcarse como enviado.")
            message.with_context(odental_message_transition=True).write({
                "state": "sent", "sent_at": fields.Datetime.now(),
                "attempt_count": message.attempt_count + 1, "last_error": False,
            })

    def action_requeue(self):
        for message in self:
            if message.state not in {"blocked", "failed"}:
                raise UserError("Solo un mensaje bloqueado o fallido puede volver a la cola.")
            patient = message.patient_id
            recipient = patient._communication_recipient()
            if not patient.appointment_messages_consent:
                raise ValidationError("El paciente todavía no ha autorizado mensajes de citas.")
            if patient.preferred_appointment_channel == "none" or not recipient:
                raise ValidationError("Configure un canal y un destino válidos en el paciente.")
            message.with_context(odental_message_transition=True).write({
                "state": "queued", "channel": patient.preferred_appointment_channel,
                "recipient": recipient, "blocking_reason": False, "last_error": False,
            })

    def action_mark_delivered(self):
        for message in self:
            if message.state != "sent":
                raise UserError("El mensaje debe estar enviado antes de registrar su entrega.")
            message.with_context(odental_message_transition=True).write({
                "state": "delivered", "delivered_at": fields.Datetime.now(),
            })

    def action_mark_failed(self):
        for message in self:
            if message.state not in {"queued", "sent"}:
                raise UserError("Este mensaje no admite un fallo de entrega.")
            message.with_context(odental_message_transition=True).write({
                "state": "failed", "attempt_count": message.attempt_count + 1,
                "last_error": message.last_error or "Fallo informado por el conector",
            })

    def action_cancel(self):
        self.filtered(lambda message: message.state in {"queued", "blocked", "failed"}).with_context(
            odental_message_transition=True
        ).write({"state": "cancelled"})


class ODentalWaitlistEntry(models.Model):
    _name = "odental.waitlist.entry"
    _description = "Lista de espera O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, requested_at, id"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    organization_id = fields.Many2one("odental.organization", required=True, ondelete="restrict", index=True)
    patient_id = fields.Many2one("odental.patient", required=True, ondelete="restrict", index=True, tracking=True)
    service_id = fields.Many2one("odental.service", required=True, ondelete="restrict", tracking=True)
    professional_id = fields.Many2one("odental.professional", ondelete="restrict")
    site_id = fields.Many2one("odental.site", ondelete="restrict")
    requested_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    desired_start_date = fields.Date(required=True, default=fields.Date.context_today)
    desired_end_date = fields.Date(required=True)
    priority = fields.Selection(
        [("normal", "Normal"), ("urgent", "Urgente")], required=True, default="normal", tracking=True
    )
    notes = fields.Text()
    state = fields.Selection(
        [("waiting", "En espera"), ("offered", "Oferta enviada"),
         ("booked", "Reservado"), ("cancelled", "Cancelado")],
        required=True, default="waiting", tracking=True, index=True
    )
    booked_appointment_id = fields.Many2one("odental.appointment", readonly=True, copy=False)
    offer_ids = fields.One2many("odental.slot.offer", "waitlist_entry_id", string="Ofertas", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("state", "waiting") != "waiting" or vals.get("booked_appointment_id"):
                raise AccessError("Una solicitud nueva debe iniciar en lista de espera.")
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("odental.waitlist.entry") or "Nuevo"
        return super().create(vals_list)

    @api.constrains(
        "organization_id", "patient_id", "service_id", "professional_id",
        "site_id", "desired_start_date", "desired_end_date"
    )
    def _check_waitlist_entry(self):
        for entry in self:
            if entry.desired_end_date < entry.desired_start_date:
                raise ValidationError("La fecha final no puede ser anterior a la inicial.")
            if entry.patient_id.organization_id != entry.organization_id:
                raise ValidationError("El paciente pertenece a otra organización.")
            if entry.service_id.organization_id != entry.organization_id:
                raise ValidationError("El servicio pertenece a otra organización.")
            if entry.professional_id and entry.organization_id not in entry.professional_id.organization_ids:
                raise ValidationError("El profesional no está autorizado en la organización.")
            if entry.site_id and not entry.site_id.is_available_to(entry.organization_id):
                raise ValidationError("La sede no está disponible para la organización.")

    def write(self, vals):
        protected = {"state", "booked_appointment_id"}
        if protected.intersection(vals) and not self.env.context.get("odental_waitlist_transition"):
            raise UserError("Utilice las acciones de la lista de espera.")
        criteria = {
            "organization_id", "patient_id", "service_id", "professional_id",
            "site_id", "desired_start_date", "desired_end_date", "priority",
        }
        if criteria.intersection(vals) and any(entry.state != "waiting" for entry in self):
            raise UserError("No puede cambiar los criterios mientras exista una oferta activa o reserva.")
        return super().write(vals)

    def action_cancel(self):
        for entry in self:
            if entry.state == "booked":
                raise UserError("Una solicitud ya reservada no puede cancelarse desde la lista.")
            entry.offer_ids.filtered(lambda offer: offer.state == "offered").action_cancel()
            entry.with_context(odental_waitlist_transition=True).write({"state": "cancelled"})


class ODentalSlotOffer(models.Model):
    _name = "odental.slot.offer"
    _description = "Oferta de espacio O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "offered_at desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    organization_id = fields.Many2one(related="waitlist_entry_id.organization_id", store=True, index=True)
    waitlist_entry_id = fields.Many2one(
        "odental.waitlist.entry", required=True, ondelete="restrict", index=True, readonly=True
    )
    patient_id = fields.Many2one(related="waitlist_entry_id.patient_id", store=True, index=True)
    cancelled_appointment_id = fields.Many2one(
        "odental.appointment", required=True, ondelete="restrict", index=True, readonly=True
    )
    offered_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    expires_at = fields.Datetime(required=True, readonly=True, index=True)
    responded_at = fields.Datetime(readonly=True, copy=False)
    replacement_appointment_id = fields.Many2one("odental.appointment", readonly=True, copy=False)
    state = fields.Selection(
        [("offered", "Ofrecido"), ("accepted", "Aceptado"), ("declined", "Rechazado"),
         ("expired", "Vencido"), ("cancelled", "Cancelado")],
        required=True, default="offered", tracking=True, index=True
    )
    message_ids = fields.One2many("odental.communication.message", "slot_offer_id", string="Mensajes", readonly=True)

    _sql_constraints = [
        (
            "entry_cancelled_appointment_unique",
            "unique(waitlist_entry_id, cancelled_appointment_id)",
            "Este espacio ya fue ofrecido a este paciente.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("odental_offer_create"):
            raise AccessError("Las ofertas solo se generan desde una cita cancelada.")
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("odental.slot.offer") or "Nuevo"
        offers = super().create(vals_list)
        for offer in offers:
            offer._validate_relationships()
        return offers

    @api.constrains("waitlist_entry_id", "cancelled_appointment_id")
    def _validate_relationships(self):
        for offer in self:
            appointment = offer.cancelled_appointment_id
            entry = offer.waitlist_entry_id
            if entry.state != "waiting":
                raise ValidationError("La solicitud ya no está disponible para una nueva oferta.")
            if appointment.organization_id != entry.organization_id:
                raise ValidationError("La cita liberada pertenece a otra organización.")
            if appointment.service_id != entry.service_id:
                raise ValidationError("La cita liberada no corresponde al servicio solicitado.")
            if appointment.state != "cancelled":
                raise ValidationError("Solo puede ofrecerse una cita que ya fue cancelada.")
            slot_date = appointment._local_appointment_datetime().date()
            if not (entry.desired_start_date <= slot_date <= entry.desired_end_date):
                raise ValidationError("El espacio no está dentro de las fechas solicitadas.")
            if entry.professional_id and entry.professional_id != appointment.professional_id:
                raise ValidationError("El profesional no coincide con la solicitud de espera.")
            if entry.site_id and entry.site_id != appointment.site_id:
                raise ValidationError("La sede no coincide con la solicitud de espera.")

    def write(self, vals):
        protected = {
            "waitlist_entry_id", "cancelled_appointment_id", "expires_at",
            "state", "responded_at", "replacement_appointment_id",
        }
        if protected.intersection(vals) and not self.env.context.get("odental_offer_transition"):
            raise UserError("Utilice las acciones de la oferta.")
        return super().write(vals)

    def _check_open(self):
        self.ensure_one()
        if self.state != "offered":
            raise UserError("La oferta ya no está disponible.")
        if self.expires_at <= fields.Datetime.now():
            raise UserError("La oferta venció y ya no puede aceptarse.")
        if self.cancelled_appointment_id.state != "cancelled":
            raise UserError("El espacio original ya no está disponible.")
        if self.waitlist_entry_id.state != "offered":
            raise UserError("La solicitud ya no se encuentra en estado ofrecido.")

    def action_accept(self):
        self.ensure_one()
        self._check_open()
        original = self.cancelled_appointment_id
        entry = self.waitlist_entry_id
        appointment = self.env["odental.appointment"].with_context(
            odental_waitlist_booking=True
        ).create({
            "organization_id": entry.organization_id.id,
            "patient_id": entry.patient_id.id,
            "professional_id": original.professional_id.id,
            "service_id": original.service_id.id,
            "site_id": original.site_id.id,
            "resource_ids": [(6, 0, original.resource_ids.ids)],
            "start_datetime": original.start_datetime,
            "duration_minutes": original.duration_minutes,
            "preparation_minutes": original.preparation_minutes,
            "cleaning_minutes": original.cleaning_minutes,
            "notes": f"Espacio recuperado desde {original.name}; lista {entry.name}.",
            "replaced_appointment_id": original.id,
        })
        appointment.with_context(odental_skip_automatic_messages=True).action_schedule()
        now = fields.Datetime.now()
        self.with_context(odental_offer_transition=True).write({
            "state": "accepted", "responded_at": now,
            "replacement_appointment_id": appointment.id,
        })
        self.message_ids.filtered(
            lambda message: message.state in {"queued", "blocked", "failed"}
        ).action_cancel()
        entry.with_context(odental_waitlist_transition=True).write({
            "state": "booked", "booked_appointment_id": appointment.id,
        })
        original.with_context(odental_communication_transition=True).write({
            "replacement_appointment_id": appointment.id,
        })
        entry.offer_ids.filtered(lambda offer: offer != self and offer.state == "offered").action_cancel()
        appointment._queue_communication("waitlist_booked", slot_offer=self)
        return {
            "type": "ir.actions.act_window", "res_model": "odental.appointment",
            "res_id": appointment.id, "view_mode": "form", "target": "current",
        }

    def action_decline(self):
        for offer in self:
            offer._check_open()
            offer.with_context(odental_offer_transition=True).write({
                "state": "declined", "responded_at": fields.Datetime.now(),
            })
            offer.message_ids.filtered(
                lambda message: message.state in {"queued", "blocked", "failed"}
            ).action_cancel()
            offer.waitlist_entry_id.with_context(odental_waitlist_transition=True).write({"state": "waiting"})
            offer.cancelled_appointment_id._offer_cancelled_slot()

    def action_expire(self):
        for offer in self.filtered(lambda item: item.state == "offered"):
            offer.with_context(odental_offer_transition=True).write({
                "state": "expired", "responded_at": fields.Datetime.now(),
            })
            offer.message_ids.action_cancel()
            offer.waitlist_entry_id.with_context(odental_waitlist_transition=True).write({"state": "waiting"})
            offer.cancelled_appointment_id._offer_cancelled_slot()

    def action_cancel(self):
        for offer in self.filtered(lambda item: item.state == "offered"):
            offer.with_context(odental_offer_transition=True).write({
                "state": "cancelled", "responded_at": fields.Datetime.now(),
            })
            offer.message_ids.action_cancel()

    @api.model
    def _cron_expire_offers(self):
        self.search([
            ("state", "=", "offered"), ("expires_at", "<=", fields.Datetime.now())
        ]).action_expire()


class ODentalAppointment(models.Model):
    _inherit = "odental.appointment"

    patient_response = fields.Selection(
        [("pending", "Pendiente"), ("confirmed", "Confirmó"), ("declined", "Canceló")],
        default="pending", tracking=True, copy=False, readonly=True
    )
    patient_response_at = fields.Datetime(readonly=True, copy=False)
    reminder_due_at = fields.Datetime(compute="_compute_reminder_due_at", store=True, index=True)
    communication_message_ids = fields.One2many(
        "odental.communication.message", "appointment_id", string="Comunicaciones", readonly=True
    )
    communication_message_count = fields.Integer(compute="_compute_communication_message_count")
    slot_offer_ids = fields.One2many(
        "odental.slot.offer", "cancelled_appointment_id", string="Ofertas de sustitución", readonly=True
    )
    replacement_appointment_id = fields.Many2one(
        "odental.appointment", string="Cita sustituta", readonly=True, copy=False
    )
    replaced_appointment_id = fields.Many2one(
        "odental.appointment", string="Cita liberada", readonly=True, copy=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("odental_waitlist_booking") and any(
            vals.get("replaced_appointment_id") for vals in vals_list
        ):
            raise AccessError("La relación de sustitución solo se genera desde una oferta aceptada.")
        return super().create(vals_list)

    @api.depends("start_datetime", "organization_id.reminder_hours_before")
    def _compute_reminder_due_at(self):
        for appointment in self:
            appointment.reminder_due_at = (
                appointment.start_datetime - timedelta(
                    hours=appointment.organization_id.reminder_hours_before
                ) if appointment.start_datetime else False
            )

    @api.depends("communication_message_ids")
    def _compute_communication_message_count(self):
        for appointment in self:
            appointment.communication_message_count = len(appointment.communication_message_ids)

    def write(self, vals):
        protected = {"patient_response", "patient_response_at", "replacement_appointment_id"}
        if protected.intersection(vals) and not self.env.context.get("odental_communication_transition"):
            raise UserError("Utilice las acciones de comunicación de la cita.")
        previous_states = {appointment.id: appointment.state for appointment in self}
        previous_starts = {appointment.id: appointment.start_datetime for appointment in self}
        values = dict(vals)
        result = super().write(values)
        if "state" in values and not self.env.context.get("odental_skip_automatic_messages"):
            for appointment in self:
                previous = previous_states[appointment.id]
                if appointment.state == previous:
                    continue
                if appointment.state == "scheduled":
                    appointment._queue_communication("confirmation")
                elif appointment.state == "confirmed":
                    appointment._cancel_pending_communications({"confirmation"})
                    if appointment.patient_response == "confirmed" and "start_datetime" not in values:
                        appointment._queue_communication("confirmed")
                elif appointment.state == "cancelled":
                    appointment._cancel_pending_communications({"confirmation", "reminder"})
                    appointment._queue_communication("cancellation")
                    appointment._offer_cancelled_slot()
                elif appointment.state in {"in_progress", "done", "no_show"}:
                    appointment._cancel_pending_communications({"confirmation", "reminder"})
        if "start_datetime" in values and not self.env.context.get("odental_skip_automatic_messages"):
            for appointment in self.filtered(lambda item: item.state in {"scheduled", "confirmed"}):
                if appointment.start_datetime != previous_starts[appointment.id]:
                    appointment.with_context(
                        odental_communication_transition=True,
                        odental_skip_automatic_messages=True,
                    ).write({"patient_response": "pending", "patient_response_at": False})
                    appointment._cancel_pending_communications({"confirmation", "reminder", "rescheduled"})
                    appointment._queue_communication("rescheduled")
        return result

    def _cancel_pending_communications(self, message_types):
        for appointment in self:
            appointment.communication_message_ids.filtered(
                lambda message: message.message_type in message_types
                and message.state in {"queued", "blocked", "failed"}
            ).action_cancel()

    def _message_values(self, slot_offer=False):
        self.ensure_one()
        patient = slot_offer.patient_id if slot_offer else self.patient_id
        localized_appointment = self._local_appointment_datetime()
        localized_expiration = fields.Datetime.context_timestamp(
            self.with_context(tz=self.organization_id.communication_timezone),
            slot_offer.expires_at if slot_offer else self.start_datetime,
        )
        return {
            "patient_name": patient.name,
            "service_name": self.service_id.name,
            "professional_name": self.professional_id.name,
            "organization_name": self.organization_id.name,
            "appointment_datetime": localized_appointment.strftime("%d/%m/%Y %I:%M %p"),
            "offer_expires_at": localized_expiration.strftime("%d/%m/%Y %I:%M %p"),
        }

    def _local_appointment_datetime(self):
        self.ensure_one()
        return fields.Datetime.context_timestamp(
            self.with_context(tz=self.organization_id.communication_timezone),
            self.start_datetime,
        )

    def _queue_communication(self, message_type, slot_offer=False, scheduled_at=False):
        self.ensure_one()
        organization = self.organization_id
        if not organization.automatic_appointment_messages:
            return self.env["odental.communication.message"].browse()
        patient = slot_offer.patient_id if slot_offer else self.patient_id
        channel = patient.preferred_appointment_channel or "none"
        recipient = patient._communication_recipient()
        template = self.env["odental.communication.template"].search([
            ("organization_id", "=", organization.id),
            ("message_type", "=", message_type), ("channel", "=", channel),
            ("active", "=", True),
        ], limit=1)
        body_template = template.body if template else DEFAULT_BODIES[message_type]
        try:
            body = body_template.format(**self._message_values(slot_offer=slot_offer))
        except (KeyError, ValueError) as exc:
            raise ValidationError("No se pudo completar la plantilla de comunicación.") from exc
        key = uuid4().hex
        blocked_reason = False
        if not patient.appointment_messages_consent:
            blocked_reason = "El paciente no ha autorizado mensajes de citas."
        elif channel == "none":
            blocked_reason = "El paciente no eligió un canal de contacto."
        elif not recipient:
            blocked_reason = "El paciente no tiene un destino válido para el canal elegido."
        return self.env["odental.communication.message"].with_context(
            odental_message_create=True
        ).create({
            "organization_id": organization.id,
            "patient_id": patient.id,
            "appointment_id": self.id,
            "slot_offer_id": slot_offer.id if slot_offer else False,
            "message_type": message_type,
            "channel": channel,
            "recipient": recipient or False,
            "body": body,
            "scheduled_at": scheduled_at or fields.Datetime.now(),
            "state": "blocked" if blocked_reason else "queued",
            "blocking_reason": blocked_reason,
            "deduplication_key": key,
        })

    def action_prepare_reminder(self):
        for appointment in self:
            if appointment.state not in {"scheduled", "confirmed"}:
                raise UserError("Solo puede recordarse una cita programada o confirmada.")
            existing = appointment.communication_message_ids.filtered(
                lambda message: message.message_type == "reminder" and message.state != "cancelled"
            )
            if not existing:
                appointment._queue_communication("reminder")

    def action_register_patient_confirmation(self):
        for appointment in self:
            if appointment.state not in {"scheduled", "confirmed"}:
                raise UserError("La cita no admite confirmación del paciente.")
            appointment.with_context(odental_communication_transition=True).write({
                "patient_response": "confirmed", "patient_response_at": fields.Datetime.now(),
                "state": "confirmed",
            })

    def action_register_patient_cancellation(self):
        for appointment in self:
            if appointment.state not in {"scheduled", "confirmed"}:
                raise UserError("La cita no admite cancelación del paciente.")
            appointment.with_context(odental_communication_transition=True).write({
                "patient_response": "declined", "patient_response_at": fields.Datetime.now(),
                "state": "cancelled",
            })

    def _offer_cancelled_slot(self):
        for appointment in self:
            if appointment.state != "cancelled" or appointment.replacement_appointment_id:
                continue
            if appointment.start_datetime <= fields.Datetime.now():
                continue
            if appointment.slot_offer_ids.filtered(lambda offer: offer.state == "offered"):
                continue
            slot_date = appointment._local_appointment_datetime().date()
            domain = [
                ("organization_id", "=", appointment.organization_id.id),
                ("patient_id", "!=", appointment.patient_id.id),
                ("service_id", "=", appointment.service_id.id),
                ("state", "=", "waiting"),
                ("desired_start_date", "<=", slot_date),
                ("desired_end_date", ">=", slot_date),
                "|", ("professional_id", "=", False),
                ("professional_id", "=", appointment.professional_id.id),
                "|", ("site_id", "=", False), ("site_id", "=", appointment.site_id.id),
            ]
            previously_offered = appointment.slot_offer_ids.mapped("waitlist_entry_id").ids
            if previously_offered:
                domain.append(("id", "not in", previously_offered))
            entry = self.env["odental.waitlist.entry"].search(domain, order="priority desc, requested_at, id", limit=1)
            if not entry:
                continue
            offer = self.env["odental.slot.offer"].with_context(
                odental_offer_create=True
            ).create({
                "waitlist_entry_id": entry.id,
                "cancelled_appointment_id": appointment.id,
                "expires_at": fields.Datetime.now() + timedelta(
                    minutes=appointment.organization_id.waitlist_offer_minutes
                ),
            })
            entry.with_context(odental_waitlist_transition=True).write({"state": "offered"})
            appointment._queue_communication("waitlist_offer", slot_offer=offer)

    def action_view_communications(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "odental.communication.message",
            "view_mode": "list,form", "target": "current",
            "domain": [("appointment_id", "=", self.id)],
            "context": {"default_appointment_id": self.id},
        }

    @api.model
    def _cron_prepare_appointment_reminders(self):
        now = fields.Datetime.now()
        appointments = self.search([
            ("state", "in", ("scheduled", "confirmed")),
            ("start_datetime", ">", now),
            ("reminder_due_at", "<=", now),
        ])
        for appointment in appointments:
            if not appointment.communication_message_ids.filtered(
                lambda message: message.message_type == "reminder" and message.state != "cancelled"
            ):
                appointment._queue_communication("reminder")
