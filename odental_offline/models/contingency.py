import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


ENTRY_TYPES = [
    ("clinical_note", "Nota clínica"),
    ("prescription", "Indicación o receta"),
    ("odontogram_finding", "Hallazgo de odontograma"),
]

_BATCH_CREATE_TOKEN = object()
_BATCH_TRANSITION_TOKEN = object()
_ENTRY_CREATE_TOKEN = object()
_ENTRY_TRANSITION_TOKEN = object()


def _digest(payload):
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ODentalContingencyBatch(models.Model):
    _name = "odental.contingency.batch"
    _description = "Lote de contingencia O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "received_at desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="restrict", index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    user_id = fields.Many2one("res.users", required=True, ondelete="restrict", index=True)
    device_hash = fields.Char(required=True, readonly=True, copy=False, index=True)
    client_batch_uuid = fields.Char(required=True, readonly=True, copy=False, index=True)
    content_hash = fields.Char(required=True, readonly=True, copy=False, index=True)
    received_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    received_ip = fields.Char(readonly=True, copy=False)
    user_agent = fields.Char(readonly=True, copy=False)
    entry_ids = fields.One2many(
        "odental.contingency.entry", "batch_id", string="Entradas", readonly=True
    )
    entry_count = fields.Integer(compute="_compute_entry_count")
    state = fields.Selection(
        [
            ("received", "Recibido"),
            ("reviewed", "Revisado"),
            ("applied", "Aplicado"),
            ("partially_applied", "Aplicado parcialmente"),
            ("rejected", "Rechazado"),
        ],
        required=True,
        default="received",
        readonly=True,
        tracking=True,
        index=True,
    )
    reviewed_at = fields.Datetime(readonly=True, copy=False)
    reviewed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    review_notes = fields.Text(string="Observaciones de revisión")

    _sql_constraints = [
        (
            "contingency_batch_user_uuid_unique",
            "unique(user_id, client_batch_uuid)",
            "Este lote de contingencia ya fue recibido.",
        )
    ]

    @api.depends("entry_ids")
    def _compute_entry_count(self):
        for batch in self:
            batch.entry_count = len(batch.entry_ids)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("odental_offline_batch_create") is not _BATCH_CREATE_TOKEN:
            raise AccessError("Los lotes solo se crean mediante la sincronización segura.")
        for values in vals_list:
            if values.get("name", "Nuevo") == "Nuevo":
                values["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.contingency.batch"
                ) or "Nuevo"
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) <= {"review_notes"}:
            if any(batch.state in {"applied", "rejected"} for batch in self):
                raise UserError("Un lote finalizado no puede modificarse.")
            return super().write(vals)
        if self.env.context.get("odental_offline_batch_transition") is not _BATCH_TRANSITION_TOKEN:
            raise UserError("Los lotes de contingencia son inmutables.")
        return super().write(vals)

    def unlink(self):
        raise UserError("Los lotes se conservan como evidencia de auditoría.")

    def _transition(self, values):
        return self.sudo().with_context(
            odental_offline_batch_transition=_BATCH_TRANSITION_TOKEN
        ).write(values)

    @api.model
    def _ingest(self, organization, user, device_id, batch_uuid, entries, metadata=None):
        """Persist an already schema-validated offline batch, with defense-in-depth checks."""
        if not user.with_user(user).has_group("odental_core.group_odental_professional"):
            raise AccessError("Solo un profesional autorizado puede sincronizar datos clínicos.")
        if organization.owner_user_id != user and user not in organization.user_ids:
            raise AccessError("La organización no está autorizada para este usuario.")
        existing = self.sudo().search(
            [("user_id", "=", user.id), ("client_batch_uuid", "=", batch_uuid)], limit=1
        )
        if existing:
            return existing
        if not entries or len(entries) > 100:
            raise ValidationError("El lote debe contener entre 1 y 100 entradas.")
        client_uuids = [entry.get("client_uuid") for entry in entries]
        if len(client_uuids) != len(set(client_uuids)):
            raise ValidationError("El lote contiene identificadores de entrada repetidos.")
        if self.env["odental.contingency.entry"].sudo().search_count(
            [("user_id", "=", user.id), ("client_uuid", "in", client_uuids)]
        ):
            raise ValidationError(
                "Una o más entradas ya pertenecen a otro lote de sincronización."
            )

        normalized = []
        for raw in entries:
            appointment = self.env["odental.appointment"].browse(raw["appointment_id"]).exists()
            if not appointment or appointment.organization_id != organization:
                raise ValidationError("Una entrada corresponde a una cita no autorizada.")
            is_manager = user.with_user(user).has_group("odental_core.group_odental_manager")
            if not is_manager and appointment.professional_id.user_id != user:
                raise AccessError("No puede sincronizar anotaciones de otro profesional.")
            values = dict(raw)
            values.update(
                {
                    "appointment_id": appointment.id,
                    "patient_id": appointment.patient_id.id,
                    "professional_id": appointment.professional_id.id,
                }
            )
            self.env["odental.contingency.entry"]._validate_payload(values)
            normalized.append(values)

        meta = metadata or {}
        batch_values = {
            "organization_id": organization.id,
            "user_id": user.id,
            "device_hash": hashlib.sha256(device_id.encode("utf-8")).hexdigest(),
            "client_batch_uuid": batch_uuid,
            "content_hash": _digest(normalized),
            "received_ip": (meta.get("ip") or "")[:128],
            "user_agent": (meta.get("user_agent") or "")[:512],
        }
        batch = self.sudo().with_context(
            odental_offline_batch_create=_BATCH_CREATE_TOKEN
        ).create(batch_values)
        self.env["odental.contingency.entry"]._create_from_sync(batch, normalized)
        for patient in batch.entry_ids.mapped("patient_id"):
            clinical_record = self.env["odental.clinical.record"].search(
                [("patient_id", "=", patient.id)], limit=1
            )
            if clinical_record:
                clinical_record._log_event(
                    "offline_received",
                    f"Contingencia recibida: {batch.name}",
                    batch.content_hash,
                    source_record=batch,
                )
        return batch

    def _check_reviewer(self):
        for batch in self:
            if self.env.user.has_group("odental_core.group_odental_manager"):
                continue
            if not self.env.user.has_group("odental_core.group_odental_professional"):
                raise AccessError("Solo un profesional puede revisar una contingencia.")
            unauthorized = batch.entry_ids.filtered(
                lambda entry: entry.professional_id.user_id != self.env.user
            )
            if unauthorized:
                raise AccessError("No puede revisar anotaciones de otro profesional.")

    def action_review(self):
        for batch in self:
            if batch.state != "received":
                raise UserError("Solo un lote recién recibido puede revisarse.")
            batch._check_reviewer()
            batch.entry_ids.filtered(lambda entry: entry.state == "pending")._transition(
                {
                    "state": "reviewed",
                    "reviewed_at": fields.Datetime.now(),
                    "reviewed_by_id": self.env.user.id,
                }
            )
            batch._transition(
                {
                    "state": "reviewed",
                    "reviewed_at": fields.Datetime.now(),
                    "reviewed_by_id": self.env.user.id,
                }
            )

    def action_reject(self):
        for batch in self:
            if batch.state not in {"received", "reviewed"}:
                raise UserError("Este lote ya fue finalizado.")
            batch._check_reviewer()
            if not (batch.review_notes or "").strip():
                raise ValidationError("Indique el motivo del rechazo en las observaciones.")
            batch.entry_ids.filtered(
                lambda entry: entry.state in {"pending", "reviewed"}
            )._transition(
                {
                    "state": "rejected",
                    "reviewed_at": fields.Datetime.now(),
                    "reviewed_by_id": self.env.user.id,
                    "review_notes": batch.review_notes,
                }
            )
            batch._transition(
                {
                    "state": "rejected",
                    "reviewed_at": fields.Datetime.now(),
                    "reviewed_by_id": self.env.user.id,
                }
            )

    def _refresh_state(self):
        for batch in self:
            states = set(batch.entry_ids.mapped("state"))
            if states == {"applied"}:
                state = "applied"
            elif states == {"rejected"}:
                state = "rejected"
            elif states <= {"reviewed"}:
                state = "reviewed"
            elif "applied" in states or "rejected" in states:
                state = "partially_applied"
            else:
                state = "received"
            batch._transition({"state": state})


class ODentalContingencyEntry(models.Model):
    _name = "odental.contingency.entry"
    _description = "Entrada de contingencia O Dental"
    _order = "client_created_at, id"

    batch_id = fields.Many2one(
        "odental.contingency.batch", required=True, ondelete="restrict", index=True
    )
    organization_id = fields.Many2one(related="batch_id.organization_id", store=True, index=True)
    user_id = fields.Many2one(related="batch_id.user_id", store=True, index=True)
    client_uuid = fields.Char(required=True, readonly=True, copy=False, index=True)
    appointment_id = fields.Many2one(
        "odental.appointment", required=True, ondelete="restrict", index=True
    )
    patient_id = fields.Many2one("odental.patient", required=True, ondelete="restrict", index=True)
    professional_id = fields.Many2one(
        "odental.professional", required=True, ondelete="restrict", index=True
    )
    entry_type = fields.Selection(ENTRY_TYPES, required=True, readonly=True, index=True)
    content = fields.Text(readonly=True)
    tooth_code = fields.Char(readonly=True)
    surface = fields.Char(readonly=True)
    condition = fields.Char(readonly=True)
    finding_status = fields.Char(readonly=True)
    client_created_at = fields.Datetime(required=True, readonly=True, index=True)
    received_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    content_hash = fields.Char(required=True, readonly=True, copy=False, index=True)
    state = fields.Selection(
        [
            ("pending", "Pendiente"),
            ("reviewed", "Revisada"),
            ("applied", "Aplicada"),
            ("rejected", "Rechazada"),
            ("conflict", "Conflicto"),
        ],
        required=True,
        default="pending",
        readonly=True,
        index=True,
    )
    review_notes = fields.Text(string="Observaciones de revisión")
    reviewed_at = fields.Datetime(readonly=True, copy=False)
    reviewed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    applied_at = fields.Datetime(readonly=True, copy=False)
    applied_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    target_model = fields.Char(readonly=True, copy=False)
    target_res_id = fields.Integer(readonly=True, copy=False)

    _sql_constraints = [
        (
            "contingency_entry_user_uuid_unique",
            "unique(user_id, client_uuid)",
            "Esta entrada de contingencia ya fue recibida.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("odental_offline_entry_create") is not _ENTRY_CREATE_TOKEN:
            raise AccessError("Las entradas solo se crean mediante la sincronización segura.")
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) <= {"review_notes"}:
            if any(entry.state in {"applied", "rejected"} for entry in self):
                raise UserError("Una entrada finalizada no puede modificarse.")
            return super().write(vals)
        if self.env.context.get("odental_offline_entry_transition") is not _ENTRY_TRANSITION_TOKEN:
            raise UserError("Las entradas sincronizadas son inmutables.")
        return super().write(vals)

    def unlink(self):
        raise UserError("Las entradas se conservan como evidencia de auditoría.")

    def _transition(self, values):
        return self.sudo().with_context(
            odental_offline_entry_transition=_ENTRY_TRANSITION_TOKEN
        ).write(values)

    @api.model
    def _validate_payload(self, values):
        entry_type = values.get("entry_type")
        if entry_type not in dict(ENTRY_TYPES):
            raise ValidationError("El tipo de entrada no está permitido.")
        content = (values.get("content") or "").strip()
        if len(content) > 5000:
            raise ValidationError("La anotación supera el límite de 5,000 caracteres.")
        if entry_type in {"clinical_note", "prescription"} and not content:
            raise ValidationError("La anotación clínica no puede estar vacía.")
        if entry_type == "odontogram_finding":
            for field_name in ("tooth_code", "surface", "condition", "finding_status"):
                if not values.get(field_name):
                    raise ValidationError("El hallazgo odontológico está incompleto.")
            if not self.env["odental.tooth"].search_count(
                [("code", "=", values["tooth_code"])], limit=1
            ):
                raise ValidationError("La pieza dental indicada no existe.")
            selections = {
                "surface": "surface",
                "condition": "condition",
                "finding_status": "status",
            }
            for incoming, model_field in selections.items():
                allowed = dict(self.env["odental.odontogram.finding"]._fields[model_field].selection)
                if values[incoming] not in allowed:
                    raise ValidationError(f"El valor de {incoming} no está permitido.")

    @api.model
    def _create_from_sync(self, batch, entries):
        values_list = []
        existing = set(
            self.sudo().search(
                [("user_id", "=", batch.user_id.id), ("client_uuid", "in", [x["client_uuid"] for x in entries])]
            ).mapped("client_uuid")
        )
        for raw in entries:
            if raw["client_uuid"] in existing:
                continue
            values = {
                "batch_id": batch.id,
                "client_uuid": raw["client_uuid"],
                "appointment_id": raw["appointment_id"],
                "patient_id": raw["patient_id"],
                "professional_id": raw["professional_id"],
                "entry_type": raw["entry_type"],
                "content": (raw.get("content") or "").strip(),
                "tooth_code": raw.get("tooth_code"),
                "surface": raw.get("surface"),
                "condition": raw.get("condition"),
                "finding_status": raw.get("finding_status"),
                "client_created_at": raw["client_created_at"],
                "content_hash": _digest(raw),
            }
            values_list.append(values)
        if values_list:
            return self.sudo().with_context(
                odental_offline_entry_create=_ENTRY_CREATE_TOKEN
            ).create(values_list)
        return self.browse()

    def _check_reviewer(self):
        for entry in self:
            if self.env.user.has_group("odental_core.group_odental_manager"):
                continue
            if (
                not self.env.user.has_group("odental_core.group_odental_professional")
                or entry.professional_id.user_id != self.env.user
            ):
                raise AccessError("No puede revisar esta anotación clínica.")

    def action_apply(self):
        for entry in self:
            if entry.state != "reviewed":
                raise UserError("La entrada debe revisarse antes de aplicarla.")
            entry._check_reviewer()
            clinical_record = self.env["odental.clinical.record"].search(
                [("patient_id", "=", entry.patient_id.id), ("state", "=", "active")],
                limit=1,
            )
            if not clinical_record:
                raise ValidationError("El paciente no tiene un expediente clínico activo.")

            if entry.entry_type in {"clinical_note", "prescription"}:
                values = {
                    "clinical_record_id": clinical_record.id,
                    "appointment_id": entry.appointment_id.id,
                    "professional_id": entry.professional_id.id,
                }
                values[
                    "clinical_findings" if entry.entry_type == "clinical_note" else "prescriptions"
                ] = entry.content
                target = self.env["odental.clinical.encounter"].create(values)
            else:
                odontogram = self.env["odental.odontogram"].search(
                    [
                        ("clinical_record_id", "=", clinical_record.id),
                        ("professional_id", "=", entry.professional_id.id),
                        ("state", "=", "draft"),
                    ],
                    order="chart_datetime desc, id desc",
                    limit=1,
                )
                if not odontogram:
                    odontogram = self.env["odental.odontogram"].create(
                        {
                            "clinical_record_id": clinical_record.id,
                            "professional_id": entry.professional_id.id,
                            "dentition": "mixed",
                            "summary": "Creado desde una contingencia revisada.",
                        }
                    )
                tooth = self.env["odental.tooth"].search(
                    [("code", "=", entry.tooth_code)], limit=1
                )
                target = self.env["odental.odontogram.finding"].create(
                    {
                        "odontogram_id": odontogram.id,
                        "tooth_id": tooth.id,
                        "surface": entry.surface,
                        "condition": entry.condition,
                        "status": entry.finding_status,
                        "notes": entry.content,
                    }
                )

            entry._transition(
                {
                    "state": "applied",
                    "applied_at": fields.Datetime.now(),
                    "applied_by_id": self.env.user.id,
                    "target_model": target._name,
                    "target_res_id": target.id,
                }
            )
            clinical_record._log_event(
                "offline_applied",
                f"Contingencia aplicada desde {entry.batch_id.name}",
                entry.content_hash,
                source_record=entry,
            )
            entry.batch_id._refresh_state()

    def action_reject(self):
        for entry in self:
            if entry.state not in {"pending", "reviewed", "conflict"}:
                raise UserError("Esta entrada ya fue finalizada.")
            entry._check_reviewer()
            if not (entry.review_notes or "").strip():
                raise ValidationError("Indique el motivo del rechazo.")
            entry._transition(
                {
                    "state": "rejected",
                    "reviewed_at": fields.Datetime.now(),
                    "reviewed_by_id": self.env.user.id,
                }
            )
            entry.batch_id._refresh_state()
