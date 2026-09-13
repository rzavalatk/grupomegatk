import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


ACTION_TYPES = [
    ("create_encounter_draft", "Crear evolución en borrador"),
    ("odontogram_finding", "Agregar hallazgo al odontograma"),
    ("create_appointment_draft", "Crear cita en borrador"),
    ("reschedule_appointment", "Reprogramar cita"),
    ("cancel_appointment", "Cancelar cita"),
]

_ACTION_CREATE_TOKEN = object()
_ACTION_TRANSITION_TOKEN = object()


class ODentalAIAction(models.Model):
    _name = "odental.ai.action"
    _description = "Acción propuesta por el asistente IA O Dental"
    _order = "session_id, sequence, id"

    session_id = fields.Many2one(
        "odental.ai.session", required=True, ondelete="restrict", index=True
    )
    organization_id = fields.Many2one(
        related="session_id.organization_id", store=True, index=True
    )
    patient_id = fields.Many2one(related="session_id.patient_id", store=True, index=True)
    sequence = fields.Integer(required=True, default=10)
    action_type = fields.Selection(ACTION_TYPES, required=True, index=True)
    payload_json = fields.Text(required=True, readonly=True)
    preview = fields.Char(required=True, readonly=True)
    detail_text = fields.Text(string="Contenido propuesto", required=True, readonly=True)
    undo_supported = fields.Boolean(readonly=True)
    status = fields.Selection(
        [("proposed", "Propuesta"), ("executed", "Ejecutada"), ("undone", "Deshecha")],
        required=True,
        default="proposed",
        readonly=True,
        index=True,
    )
    target_model = fields.Char(readonly=True, copy=False)
    target_res_id = fields.Integer(readonly=True, copy=False)
    before_json = fields.Text(readonly=True, copy=False)
    after_json = fields.Text(readonly=True, copy=False)
    result_hash = fields.Char(readonly=True, copy=False, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("odental_ai_action_create") is not _ACTION_CREATE_TOKEN:
            raise AccessError("Las acciones de IA solo se crean desde el analizador controlado.")
        prepared = []
        for original in vals_list:
            vals = dict(original)
            payload = vals.pop("payload", {})
            vals["payload_json"] = json.dumps(
                payload, ensure_ascii=False, sort_keys=True
            )
            vals["undo_supported"] = vals.get("action_type") in {
                "create_encounter_draft",
                "odontogram_finding",
                "create_appointment_draft",
            }
            vals["preview"] = self._preview_for(vals.get("action_type"), payload)
            vals["detail_text"] = self._detail_for(vals.get("action_type"), payload)
            prepared.append(vals)
        return super().create(prepared)

    @api.model
    def _create_from_analysis(self, vals_list):
        return self.sudo().with_context(
            odental_ai_action_create=_ACTION_CREATE_TOKEN
        ).create(vals_list)

    def write(self, vals):
        if self.env.context.get("odental_ai_action_transition") is not _ACTION_TRANSITION_TOKEN:
            raise UserError("Las acciones propuestas son inmutables.")
        return super().write(vals)

    def _transition(self, values):
        return self.sudo().with_context(
            odental_ai_action_transition=_ACTION_TRANSITION_TOKEN
        ).write(values)

    def unlink(self):
        raise UserError("Las acciones de IA se conservan como evidencia de auditoría.")

    @staticmethod
    def _preview_for(action_type, payload):
        if action_type == "create_encounter_draft":
            labels = {
                "chief_complaint": "motivo",
                "clinical_findings": "hallazgos",
                "diagnosis_summary": "diagnóstico",
                "treatment_plan": "plan",
                "procedures_performed": "procedimientos",
                "prescriptions": "indicaciones",
                "private_notes": "nota restringida",
            }
            content = ", ".join(labels[key] for key in payload if key in labels)
            return f"Crear una evolución clínica en borrador con: {content}."
        if action_type == "odontogram_finding":
            return (
                f"Agregar {payload.get('condition')} en pieza {payload.get('tooth_code')}, "
                f"superficie {payload.get('surface')}, estado {payload.get('status')}."
            )
        if action_type == "create_appointment_draft":
            return f"Crear una cita en borrador para {payload.get('start')}."
        if action_type == "reschedule_appointment":
            return f"Reprogramar la cita seleccionada para {payload.get('new_start')}."
        if action_type == "cancel_appointment":
            return "Cancelar la cita seleccionada; esta acción no admite deshacer automático."
        raise ValidationError("El tipo de acción de IA no está permitido.")

    @staticmethod
    def _detail_for(action_type, payload):
        if action_type == "create_encounter_draft":
            labels = {
                "chief_complaint": "Motivo de consulta",
                "clinical_findings": "Hallazgos clínicos",
                "diagnosis_summary": "Diagnóstico",
                "treatment_plan": "Plan de tratamiento",
                "procedures_performed": "Procedimientos",
                "prescriptions": "Indicaciones",
                "private_notes": "Nota restringida",
            }
            return "\n".join(
                f"{labels[key]}: {value}" for key, value in payload.items() if key in labels
            )
        return ODentalAIAction._preview_for(action_type, payload)

    def _payload(self):
        self.ensure_one()
        try:
            payload = json.loads(self.payload_json or "{}")
        except json.JSONDecodeError as error:
            raise ValidationError("La propuesta estructurada está dañada.") from error
        if not isinstance(payload, dict):
            raise ValidationError("La propuesta estructurada no es válida.")
        return payload

    def _canonical_payload(self):
        self.ensure_one()
        return {
            "sequence": self.sequence,
            "action_type": self.action_type,
            "payload": self._payload(),
        }

    def _execution_payload(self):
        self.ensure_one()
        return {
            "action": self._canonical_payload(),
            "status": self.status,
            "target_model": self.target_model or "",
            "target_res_id": self.target_res_id,
            "result_hash": self.result_hash or "",
        }

    def _validate_ready(self):
        self.ensure_one()
        session = self.session_id
        payload = self._payload()
        if self.action_type in {"create_encounter_draft", "odontogram_finding"}:
            if not session.patient_id or not session.professional_id:
                raise ValidationError(
                    "Seleccione paciente y profesional para las acciones clínicas."
                )
            record = self.env["odental.clinical.record"].search(
                [("patient_id", "=", session.patient_id.id), ("state", "=", "active")],
                limit=1,
            )
            if not record:
                raise ValidationError("El paciente no tiene un expediente clínico activo.")
        if self.action_type == "create_encounter_draft":
            allowed = {
                "chief_complaint",
                "clinical_findings",
                "diagnosis_summary",
                "treatment_plan",
                "procedures_performed",
                "prescriptions",
                "private_notes",
            }
            if not payload or set(payload) - allowed:
                raise ValidationError("La evolución contiene campos no permitidos.")
        elif self.action_type == "odontogram_finding":
            required = {"tooth_code", "condition", "surface", "status", "notes"}
            if set(payload) != required:
                raise ValidationError("El hallazgo odontológico no tiene el formato permitido.")
            tooth = self.env["odental.tooth"].search(
                [("code", "=", payload["tooth_code"])], limit=1
            )
            if not tooth:
                raise ValidationError("La pieza dental indicada no existe.")
            self._validate_selection("odental.odontogram.finding", "condition", payload["condition"])
            self._validate_selection("odental.odontogram.finding", "surface", payload["surface"])
            self._validate_selection("odental.odontogram.finding", "status", payload["status"])
        elif self.action_type == "create_appointment_draft":
            if not all(
                [
                    session.patient_id,
                    session.professional_id,
                    session.service_id,
                    session.site_id,
                    payload.get("start"),
                ]
            ):
                raise ValidationError(
                    "Para agendar seleccione paciente, profesional, servicio y sede."
                )
            start = fields.Datetime.to_datetime(payload["start"])
            if not start or start <= fields.Datetime.now():
                raise ValidationError("La nueva cita debe programarse en el futuro.")
        elif self.action_type in {"reschedule_appointment", "cancel_appointment"}:
            if not session.appointment_id:
                raise ValidationError("Seleccione la cita que desea modificar.")
            if session.appointment_id.state not in {"draft", "scheduled", "confirmed"}:
                raise ValidationError("La cita ya no admite esta modificación.")
            if self.action_type == "reschedule_appointment":
                new_start = fields.Datetime.to_datetime(payload.get("new_start"))
                if not new_start or new_start <= fields.Datetime.now():
                    raise ValidationError("La reprogramación debe indicar una fecha futura.")
                if new_start == session.appointment_id.start_datetime:
                    raise ValidationError("La cita ya está programada en la fecha indicada.")

    def _validate_selection(self, model_name, field_name, value):
        selection = dict(self.env[model_name]._fields[field_name].selection)
        if value not in selection:
            raise ValidationError(f"El valor {value} no está permitido para {field_name}.")

    @staticmethod
    def _snapshot_encounter(record):
        fields_to_keep = [
            "clinical_record_id",
            "appointment_id",
            "professional_id",
            "encounter_datetime",
            "chief_complaint",
            "clinical_findings",
            "diagnosis_summary",
            "treatment_plan",
            "procedures_performed",
            "prescriptions",
            "private_notes",
            "state",
        ]
        result = {}
        for name in fields_to_keep:
            value = record[name]
            if hasattr(value, "id"):
                value = value.id
            elif name == "encounter_datetime":
                value = fields.Datetime.to_string(value)
            result[name] = value or False
        return result

    @staticmethod
    def _snapshot_finding(record):
        return {
            "odontogram_id": record.odontogram_id.id,
            "tooth_id": record.tooth_id.id,
            "surface": record.surface,
            "condition": record.condition,
            "status": record.status,
            "notes": record.notes or False,
        }

    @staticmethod
    def _snapshot_appointment(record):
        return {
            "organization_id": record.organization_id.id,
            "patient_id": record.patient_id.id,
            "professional_id": record.professional_id.id,
            "service_id": record.service_id.id,
            "site_id": record.site_id.id,
            "resource_ids": sorted(record.resource_ids.ids),
            "start_datetime": fields.Datetime.to_string(record.start_datetime),
            "duration_minutes": record.duration_minutes,
            "preparation_minutes": record.preparation_minutes,
            "cleaning_minutes": record.cleaning_minutes,
            "state": record.state,
            "notes": record.notes or False,
        }

    @staticmethod
    def _snapshot_odontogram(record):
        return {
            "clinical_record_id": record.clinical_record_id.id,
            "professional_id": record.professional_id.id,
            "encounter_id": record.encounter_id.id,
            "dentition": record.dentition,
            "summary": record.summary or False,
            "state": record.state,
            "finding_ids": sorted(record.finding_ids.ids),
        }

    @staticmethod
    def _hash(payload):
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _execute(self):
        self.ensure_one()
        if self.status != "proposed" or self.session_id.state != "confirmed":
            raise UserError("La acción no está disponible para ejecución.")
        self.session_id._check_confirming_user()
        self._validate_ready()
        session = self.session_id
        payload = self._payload()
        before = {}
        after = {}
        target = False

        if self.action_type == "create_encounter_draft":
            record = self.env["odental.clinical.record"].search(
                [("patient_id", "=", session.patient_id.id), ("state", "=", "active")],
                limit=1,
            )
            values = dict(payload)
            values.update(
                {
                    "clinical_record_id": record.id,
                    "professional_id": session.professional_id.id,
                    "appointment_id": session.appointment_id.id,
                }
            )
            target = self.env["odental.clinical.encounter"].create(values)
            after = {"record": self._snapshot_encounter(target)}
        elif self.action_type == "odontogram_finding":
            record = self.env["odental.clinical.record"].search(
                [("patient_id", "=", session.patient_id.id), ("state", "=", "active")],
                limit=1,
            )
            chart = session.odontogram_id
            chart_created = False
            if not chart:
                chart = self.env["odental.odontogram"].search(
                    [
                        ("clinical_record_id", "=", record.id),
                        ("professional_id", "=", session.professional_id.id),
                        ("state", "=", "draft"),
                    ],
                    order="chart_datetime desc, id desc",
                    limit=1,
                )
            if not chart:
                chart = self.env["odental.odontogram"].create(
                    {
                        "clinical_record_id": record.id,
                        "professional_id": session.professional_id.id,
                        "dentition": "mixed",
                        "summary": f"Borrador preparado desde {session.name}",
                    }
                )
                chart_created = True
            if chart.state != "draft":
                raise ValidationError("El odontograma dejó de estar disponible como borrador.")
            tooth = self.env["odental.tooth"].search(
                [("code", "=", payload["tooth_code"])], limit=1
            )
            target = self.env["odental.odontogram.finding"].create(
                {
                    "odontogram_id": chart.id,
                    "tooth_id": tooth.id,
                    "surface": payload["surface"],
                    "condition": payload["condition"],
                    "status": payload["status"],
                    "notes": payload["notes"],
                }
            )
            after = {
                "record": self._snapshot_finding(target),
                "created_chart_id": chart.id if chart_created else False,
                "created_chart": self._snapshot_odontogram(chart) if chart_created else False,
            }
        elif self.action_type == "create_appointment_draft":
            target = self.env["odental.appointment"].create(
                {
                    "organization_id": session.organization_id.id,
                    "patient_id": session.patient_id.id,
                    "professional_id": session.professional_id.id,
                    "service_id": session.service_id.id,
                    "site_id": session.site_id.id,
                    "resource_ids": [(6, 0, session.resource_ids.ids)],
                    "start_datetime": fields.Datetime.to_datetime(payload["start"]),
                    "state": "draft",
                    "notes": f"Borrador preparado por {session.name}",
                }
            )
            after = {"record": self._snapshot_appointment(target)}
        elif self.action_type == "reschedule_appointment":
            target = session.appointment_id
            before = {"start_datetime": fields.Datetime.to_string(target.start_datetime)}
            target.write(
                {"start_datetime": fields.Datetime.to_datetime(payload["new_start"])}
            )
            after = {"start_datetime": fields.Datetime.to_string(target.start_datetime)}
        elif self.action_type == "cancel_appointment":
            target = session.appointment_id
            before = {"state": target.state}
            target.action_cancel()
            after = {"state": target.state}
        else:
            raise ValidationError("La acción solicitada no está permitida.")

        result_hash = self._hash(
            {
                "type": self.action_type,
                "target_model": target._name,
                "target_res_id": target.id,
                "before": before,
                "after": after,
            }
        )
        self._transition(
            {
                "status": "executed",
                "target_model": target._name,
                "target_res_id": target.id,
                "before_json": json.dumps(before, ensure_ascii=False, sort_keys=True),
                "after_json": json.dumps(after, ensure_ascii=False, sort_keys=True),
                "result_hash": result_hash,
            }
        )

    def _undo(self):
        self.ensure_one()
        if (
            self.status != "executed"
            or self.session_id.state != "executed"
            or not self.undo_supported
        ):
            raise UserError("Esta acción no admite deshacer automático.")
        self.session_id._check_confirming_user()
        expected_models = {
            "create_encounter_draft": "odental.clinical.encounter",
            "odontogram_finding": "odental.odontogram.finding",
            "create_appointment_draft": "odental.appointment",
        }
        expected_model = expected_models.get(self.action_type)
        if not expected_model or self.target_model != expected_model:
            raise ValidationError("El destino de la acción no coincide con su tipo.")
        target = self.env[expected_model].sudo().browse(self.target_res_id).exists()
        if not target:
            raise ValidationError("El registro creado ya no existe.")
        after = json.loads(self.after_json or "{}")
        if self.action_type == "create_encounter_draft":
            if target.state != "draft" or self._snapshot_encounter(target) != after.get("record"):
                raise ValidationError("La evolución cambió y ya no puede eliminarse automáticamente.")
            target.unlink()
        elif self.action_type == "odontogram_finding":
            chart = target.odontogram_id
            if chart.state != "draft" or self._snapshot_finding(target) != after.get("record"):
                raise ValidationError("El odontograma cambió y ya no puede deshacerse automáticamente.")
            if after.get("created_chart_id") == chart.id:
                expected_chart = dict(after.get("created_chart") or {})
                expected_chart["finding_ids"] = [target.id]
                if self._snapshot_odontogram(chart) != expected_chart:
                    raise ValidationError(
                        "El odontograma creado por la IA fue modificado y no puede eliminarse automáticamente."
                    )
            target.unlink()
            if after.get("created_chart_id") == chart.id and not chart.finding_ids:
                chart.unlink()
        elif self.action_type == "create_appointment_draft":
            if target.state != "draft" or self._snapshot_appointment(target) != after.get("record"):
                raise ValidationError("La cita cambió y ya no puede eliminarse automáticamente.")
            target.unlink()
        else:
            raise UserError("Esta acción no admite deshacer automático.")
        self._transition({"status": "undone"})
