"""Private Todoist availability. Task titles and descriptions never enter Odoo."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


TODOIST_API = "https://api.todoist.com/api/v1"
MIRROR_DESCRIPTION = "Bloqueo automático O Dental. Referencia: "


class ODentalTodoistConnection(models.Model):
    _name = "odental.todoist.connection"
    _description = "Conexión privada de disponibilidad Todoist"
    _rec_name = "professional_id"

    professional_id = fields.Many2one("odental.professional", required=True, ondelete="cascade", index=True)
    organization_id = fields.Many2one("odental.organization", required=True, ondelete="cascade", index=True)
    pilot_patient_id = fields.Many2one(
        "odental.patient", string="Paciente de prueba", required=True, ondelete="restrict",
        help="Durante el piloto solo se publican en Todoist las citas de este paciente.",
    )
    export_all_patients = fields.Boolean(
        string="Publicar citas de todos los pacientes",
        default=False,
        groups="base.group_system",
        help="Solo para activación clínica autorizada. Envía nombre, servicio general y horario a Todoist.",
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    # The user enters this through the short-lived wizard. Only the superuser
    # running the sync can read the stored credential, never clinical staff.
    api_token = fields.Char(copy=False, groups="base.group_system")
    todoist_user_id = fields.Char(copy=False)
    label_name = fields.Char(string="Etiqueta que bloquea", default="reunión", required=True)
    default_duration_minutes = fields.Integer(
        string="Duración si Todoist no indica una", default=60, required=True,
    )
    source_timezone = fields.Char(string="Zona horaria", default="America/Tegucigalpa", required=True)
    active = fields.Boolean(default=True)
    last_synced_at = fields.Datetime(string="Última actualización", readonly=True)
    last_error = fields.Char(string="Estado de sincronización", readonly=True)

    _sql_constraints = [
        ("professional_organization_unique", "unique(professional_id, organization_id)",
         "Ya existe una conexión Todoist para este profesional y organización."),
    ]

    @api.constrains("professional_id", "organization_id", "pilot_patient_id", "source_timezone", "default_duration_minutes")
    def _check_scope(self):
        for connection in self:
            if connection.organization_id not in connection.professional_id.organization_ids:
                raise ValidationError("El profesional debe pertenecer a la organización.")
            if connection.professional_id.company_id != connection.organization_id.company_id:
                raise ValidationError("La conexión debe permanecer dentro de la compañía del profesional.")
            if connection.pilot_patient_id.organization_id != connection.organization_id:
                raise ValidationError("El paciente de prueba debe pertenecer a la organización.")
            if (not connection.professional_id.user_id or
                    connection.company_id not in connection.professional_id.user_id.company_ids):
                raise ValidationError("El usuario del profesional debe tener acceso a la compañía de la clínica.")
            if not 0 < connection.default_duration_minutes <= 1440:
                raise ValidationError("La duración predeterminada debe estar entre 1 y 1440 minutos.")
            try:
                ZoneInfo(connection.source_timezone)
            except ZoneInfoNotFoundError as exc:
                raise ValidationError("Indique una zona horaria válida.") from exc

    def _check_owner(self):
        for connection in self:
            if connection.professional_id.user_id != self.env.user:
                raise AccessError("Solo el profesional puede administrar su propia conexión Todoist.")
            if connection.company_id not in self.env.companies:
                raise AccessError("Cambie a la compañía autorizada del profesional.")
            if connection.company_id not in connection.professional_id.user_id.company_ids:
                raise AccessError("El usuario del profesional no tiene acceso a la compañía de la clínica.")

    @api.model
    def _get_json(self, token, endpoint, params=None):
        try:
            response = requests.get(
                f"{TODOIST_API}/{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
                params=params, timeout=15,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            # Never include server response bodies, task content, or token.
            raise UserError("No se pudo consultar Todoist. Revise la conexión o autorización.") from exc

    @api.model
    def _fetch_user_id(self, token):
        data = self._get_json(token, "user")
        if not isinstance(data, dict) or not data.get("id"):
            raise UserError("Todoist no devolvió la identidad de la cuenta.")
        return str(data["id"])

    @api.model
    def _fetch_tasks(self, token):
        tasks = []
        cursor = None
        seen_cursors = set()
        for _page in range(100):
            params = {"limit": 200}
            if cursor:
                params["cursor"] = cursor
            data = self._get_json(token, "tasks", params=params)
            if not isinstance(data, dict) or not isinstance(data.get("results"), list):
                raise UserError("Todoist devolvió una lista de tareas incompleta.")
            tasks.extend(data["results"])
            cursor = data.get("next_cursor")
            if not cursor:
                return tasks
            if cursor in seen_cursors:
                break
            seen_cursors.add(cursor)
        raise UserError("La consulta de Todoist quedó incompleta; no se liberó ningún bloqueo.")

    @api.model
    def _send_json(self, token, method, endpoint, payload=None):
        try:
            response = requests.request(
                method, f"{TODOIST_API}/{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
                json=payload, timeout=15,
            )
            if method == "DELETE" and response.status_code == 404:
                return None  # A task already removed by its owner is retired.
            response.raise_for_status()
            return response.json() if response.content else None
        except (requests.RequestException, ValueError) as exc:
            raise UserError("No se pudo actualizar Todoist. Revise la conexión o autorización.") from exc

    def _task_interval(self, task):
        self.ensure_one()
        if not isinstance(task, dict) or task.get("checked") or task.get("is_deleted"):
            return None
        labels = {str(label).lstrip("@").casefold() for label in (task.get("labels") or [])}
        if self.label_name.strip().lstrip("@").casefold() not in labels:
            return None
        responsible = task.get("responsible_uid")
        if responsible and str(responsible) != self.todoist_user_id:
            return None
        due = task.get("due") or {}
        if not isinstance(due, dict):
            return None
        date_value = due.get("datetime") or due.get("date") or ""
        duration = task.get("duration") or {}
        if not isinstance(date_value, str) or not isinstance(duration, dict):
            return None
        if "T" not in date_value:
            return None  # All-day tasks do not block.
        minutes = self.default_duration_minutes
        if duration:
            if duration.get("unit") != "minute":
                return None
            minutes = duration.get("amount")
        if not isinstance(minutes, int) or not 0 < minutes <= 1440:
            return None
        try:
            start = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            if start.tzinfo is None:
                start = start.replace(tzinfo=ZoneInfo(due.get("timezone") or self.source_timezone))
        except (ValueError, TypeError, ZoneInfoNotFoundError):
            return None
        start_utc = start.astimezone(timezone.utc).replace(tzinfo=None)
        return start_utc, minutes

    def _has_clinical_conflict(self, start, end):
        self.ensure_one()
        return bool(self.env["odental.appointment"].sudo().search_count([
            ("entry_type", "=", "clinical"),
            ("professional_id", "=", self.professional_id.id),
            ("state", "in", ("scheduled", "confirmed", "in_progress")),
            ("blocking_start", "<", end),
            ("blocking_end", ">", start),
        ]))

    def _reconcile_tasks(self, tasks):
        self.ensure_one()
        if not self.env.is_superuser():
            raise AccessError("La sincronización requiere el proceso autorizado de O Dental.")
        appointments = self.env["odental.appointment"].sudo().with_company(self.company_id).with_context(
            odental_audit_source="todoist",
            odental_audit_actor_user_id=self.professional_id.user_id.id,
        )
        domain = [
            ("entry_type", "=", "busy"),
            ("organization_id", "=", self.organization_id.id),
            ("professional_id", "=", self.professional_id.id),
            ("external_source", "=", "todoist"),
        ]
        existing = {item.external_uid: item for item in appointments.search(domain)}
        seen = set()
        for task in tasks:
            if isinstance(task, dict) and str(task.get("description") or "").startswith(MIRROR_DESCRIPTION):
                continue  # Clinical mirrors never become personal meeting blocks.
            interval = self._task_interval(task)
            task_id = str(task.get("id") or "") if isinstance(task, dict) else ""
            if not interval or not task_id or task_id.startswith("tmp-"):
                continue
            start, minutes = interval
            seen.add(task_id)
            values = {
                "start_datetime": start,
                "duration_minutes": minutes,
                "external_conflict": self._has_clinical_conflict(start, start + timedelta(minutes=minutes)),
                "state": "scheduled",
            }
            current = existing.get(task_id)
            if current:
                changed = {key: value for key, value in values.items() if current[key] != value}
                if changed:
                    current.with_context(odental_skip_automatic_messages=True).write(changed)
            else:
                appointments.create({
                    **values, "entry_type": "busy",
                    "organization_id": self.organization_id.id,
                    "professional_id": self.professional_id.id,
                    "external_source": "todoist", "external_uid": task_id,
                })
        for task_id, current in existing.items():
            if task_id not in seen and current.state != "cancelled":
                current.with_context(odental_skip_automatic_messages=True).write(
                    {"state": "cancelled", "external_conflict": False}
                )

    def _export_marker(self, appointment):
        self.ensure_one()
        identity = f"{self.env.cr.dbname}:{self.id}:{appointment.id}"
        return hashlib.sha256(identity.encode()).hexdigest()[:24]

    def _export_payload(self, appointment):
        self.ensure_one()
        local_tz = ZoneInfo(self.source_timezone)
        start = appointment.start_datetime.replace(tzinfo=timezone.utc)
        end = appointment.end_datetime.replace(tzinfo=timezone.utc)
        first, last = start.astimezone(local_tz), end.astimezone(local_tz)
        interval = f"{first:%d/%m %H:%M}–{last:%H:%M}"
        return {
            "content": f"Atender a {appointment.patient_id.name} · {appointment.service_id.name} · {interval}",
            "description": MIRROR_DESCRIPTION + self._export_marker(appointment),
            "labels": [self.label_name.strip().lstrip("@"), "odental"],
            # Duration is intentionally absent so free Todoist accounts work;
            # the end time is visible in the neutral task title.
            "due_datetime": start.isoformat().replace("+00:00", "Z"),
        }

    @api.model
    def _remote_matches(self, remote, payload):
        due = remote.get("due") or {}
        actual_due = due.get("datetime") or due.get("date") if isinstance(due, dict) else ""
        try:
            expected = datetime.fromisoformat(payload["due_datetime"].replace("Z", "+00:00"))
            actual = datetime.fromisoformat(actual_due.replace("Z", "+00:00"))
            same_time = expected == actual
        except (AttributeError, TypeError, ValueError):
            same_time = False
        return (remote.get("content") == payload["content"]
                and remote.get("description") == payload["description"]
                and set(payload["labels"]).issubset(set(remote.get("labels") or []))
                and same_time)

    def _mirror_interval(self, task, fallback_minutes):
        self.ensure_one()
        due = task.get("due") or {}
        if not isinstance(due, dict):
            return None
        value = due.get("datetime") or due.get("date") or ""
        if not isinstance(value, str) or "T" not in value:
            return None
        try:
            start = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if start.tzinfo is None:
                start = start.replace(tzinfo=ZoneInfo(due.get("timezone") or self.source_timezone))
            duration = task.get("duration") or {}
            minutes = duration.get("amount", fallback_minutes) if isinstance(duration, dict) else fallback_minutes
            if not isinstance(minutes, int) or not 0 < minutes <= 1440:
                return None
            return start.astimezone(timezone.utc).replace(tzinfo=None), minutes
        except (ValueError, TypeError, ZoneInfoNotFoundError):
            return None

    def _reconcile_exports(self, tasks):
        self.ensure_one()
        if not self.env.is_superuser():
            raise AccessError("La publicación de citas requiere el proceso autorizado de O Dental.")
        mirrors = self.env["odental.todoist.mirror"].sudo().with_company(self.company_id)
        existing = {item.appointment_id.id: item for item in mirrors.search([("connection_id", "=", self.id)])}
        appointments = self.env["odental.appointment"].sudo().with_company(self.company_id).with_context(
            odental_audit_source="todoist",
            odental_audit_actor_user_id=self.professional_id.user_id.id,
        )
        domain = [
            ("entry_type", "=", "clinical"),
            ("active", "=", True),
            ("organization_id", "=", self.organization_id.id),
            ("professional_id", "=", self.professional_id.id),
            ("state", "in", ("scheduled", "confirmed", "in_progress")),
            ("start_datetime", ">=", fields.Datetime.now() - timedelta(days=1)),
        ]
        if not self.export_all_patients:
            domain.append(("patient_id", "=", self.pilot_patient_id.id))
        active = appointments.search(domain)
        # A previously published visit can be moved from an old date in
        # Todoist; retain its mirror in the reconciliation until retired.
        active |= appointments.browse(list(existing)).filtered(lambda appointment:
            appointment.active and appointment.entry_type == "clinical"
            and appointment.organization_id == self.organization_id
            and appointment.professional_id == self.professional_id
            and (self.export_all_patients or appointment.patient_id == self.pilot_patient_id)
            and appointment.state in ("scheduled", "confirmed", "in_progress"))
        remote_by_id = {str(task.get("id")): task for task in tasks if isinstance(task, dict) and task.get("id")}
        remote_by_marker = {
            task.get("description"): task for task in tasks
            if isinstance(task, dict) and str(task.get("description") or "").startswith(MIRROR_DESCRIPTION)
        }
        conflicts = False
        for appointment in active:
            mirror = existing.pop(appointment.id, False)
            marker = MIRROR_DESCRIPTION + self._export_marker(appointment)
            remote = (remote_by_id.get(mirror.task_id) if mirror else None) or remote_by_marker.get(marker)
            if remote:
                task_id = str(remote["id"])
                interval = self._mirror_interval(remote, appointment.duration_minutes)
                if mirror and mirror.synced_start and interval and (
                    interval[0] != mirror.synced_start
                    or (remote.get("duration") and interval[1] != mirror.synced_duration)
                ):
                    # The doctor's Todoist time wins even if reception also
                    # moved this appointment since the last reconciliation.
                    try:
                        with self.env.cr.savepoint():
                            appointment.write({"start_datetime": interval[0], "duration_minutes": interval[1]})
                    except ValidationError:
                        appointment.write({"external_conflict": True})
                        conflicts = True
                        continue  # Keep the doctor's edit for manual conflict resolution.
                    appointment.write({"external_conflict": False})
                elif (appointment.external_conflict and mirror and mirror.synced_start
                      and interval and interval[0] == mirror.synced_start
                      and (not remote.get("duration") or interval[1] == mirror.synced_duration)):
                    # The doctor restored the last accepted time after a
                    # rejected move. The conflict is no longer outstanding.
                    appointment.write({"external_conflict": False})
                payload = self._export_payload(appointment)
                explicit_duration = remote.get("duration") or {}
                if isinstance(explicit_duration, dict) and explicit_duration.get("unit") == "minute":
                    payload.update({"duration": appointment.duration_minutes, "duration_unit": "minute"})
                if not self._remote_matches(remote, payload):
                    self._send_json(self.api_token, "POST", f"tasks/{task_id}", payload)
            else:
                payload = self._export_payload(appointment)
                created = self._send_json(self.api_token, "POST", "tasks", payload)
                if not isinstance(created, dict) or not created.get("id"):
                    raise UserError("Todoist no confirmó la creación del bloqueo clínico.")
                task_id = str(created["id"])
            fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            values = {"task_id": task_id, "fingerprint": fingerprint,
                      "synced_start": appointment.start_datetime,
                      "synced_duration": appointment.duration_minutes}
            if mirror:
                mirror.write(values)
            else:
                mirrors.create({"connection_id": self.id, "appointment_id": appointment.id, **values})
        for mirror in existing.values():
            if mirror.task_id in remote_by_id:
                self._send_json(self.api_token, "DELETE", f"tasks/{mirror.task_id}")
            mirror.unlink()
        return conflicts

    def _retire_exports(self):
        self.ensure_one()
        if not self.env.is_superuser():
            raise AccessError("La desconexión requiere el proceso autorizado de O Dental.")
        mirrors = self.env["odental.todoist.mirror"].sudo().search([("connection_id", "=", self.id)])
        for mirror in mirrors:
            self._send_json(self.api_token, "DELETE", f"tasks/{mirror.task_id}")
        mirrors.unlink()

    def _sync_one(self):
        self.ensure_one()
        if not self.env.is_superuser():
            raise AccessError("La sincronización requiere el proceso autorizado de O Dental.")
        if not self.active or not self.api_token:
            return
        if self.company_id not in self.professional_id.user_id.company_ids:
            raise ValidationError("El usuario del profesional debe tener acceso a la compañía de la clínica.")
        tasks = self._fetch_tasks(self.api_token)
        # Reconcile only after every page succeeded: a partial response must
        # never cancel legitimate blocks.
        self._reconcile_tasks(tasks)
        conflicts = self._reconcile_exports(tasks)
        self.sudo().write({"last_synced_at": fields.Datetime.now(),
                           "last_error": "Revise citas clínicas con conflicto de horario." if conflicts else False})

    def action_sync_now(self):
        self._check_owner()
        for connection in self:
            connection.sudo()._sync_one()
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_disconnect(self):
        self._check_owner()
        for connection in self:
            connection.sudo()._retire_exports()
            connection.sudo().write({"active": False, "api_token": False})
            blocks = self.env["odental.appointment"].sudo().search([
                ("entry_type", "=", "busy"),
                ("organization_id", "=", connection.organization_id.id),
                ("professional_id", "=", connection.professional_id.id),
                ("external_source", "=", "todoist"),
                ("state", "!=", "cancelled"),
            ])
            blocks.with_context(odental_skip_automatic_messages=True).write({"state": "cancelled"})
        return {"type": "ir.actions.client", "tag": "reload"}

    @api.model
    def _cron_sync(self):
        if not self.env.is_superuser():
            raise AccessError("La tarea de sincronización requiere el usuario del sistema.")
        for connection in self.sudo().search([("active", "=", True)]):
            try:
                with self.env.cr.savepoint():
                    self.env.cr.execute(
                        "SELECT pg_try_advisory_xact_lock(%s, %s)",
                        (768802, connection.id),
                    )
                    if not self.env.cr.fetchone()[0]:
                        continue
                    connection._sync_one()
            except Exception:  # One failed account must not block other clinics.
                connection.sudo().write({"last_error": "Todoist no se actualizó; revise la conexión."})


class ODentalTodoistMirror(models.Model):
    _name = "odental.todoist.mirror"
    _description = "Cita clínica publicada en Todoist"

    connection_id = fields.Many2one("odental.todoist.connection", required=True, ondelete="cascade", index=True)
    appointment_id = fields.Many2one("odental.appointment", required=True, ondelete="cascade", index=True)
    task_id = fields.Char(required=True, index=True)
    fingerprint = fields.Char(required=True)
    synced_start = fields.Datetime(string="Último inicio conciliado")
    synced_duration = fields.Integer(string="Última duración conciliada")

    _sql_constraints = [
        ("connection_appointment_unique", "unique(connection_id, appointment_id)",
         "La cita ya está publicada en esta conexión."),
        ("connection_task_unique", "unique(connection_id, task_id)",
         "La tarea ya está vinculada a una cita clínica."),
    ]
