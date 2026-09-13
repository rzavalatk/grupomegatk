from datetime import timedelta
from uuid import UUID

from odoo import fields, http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.tools import file_open


class ODentalContingencyController(http.Controller):
    SECURE_HEADERS = {
        "Cache-Control": "private, no-store, max-age=0",
        "Pragma": "no-cache",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-Robots-Tag": "noindex, nofollow, noarchive",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Content-Security-Policy": (
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; connect-src 'self'; worker-src 'self'; frame-ancestors 'none'; "
            "base-uri 'self'; form-action 'self'"
        ),
    }

    @staticmethod
    def _require_professional():
        user = request.env.user
        if not user.has_group("odental_core.group_odental_professional"):
            raise AccessError("Solo un profesional autorizado puede usar el modo contingencia.")
        return user

    @staticmethod
    def _uuid(value, label):
        try:
            parsed = UUID(str(value))
        except (TypeError, ValueError, AttributeError) as error:
            raise ValidationError(f"{label} no es válido.") from error
        return str(parsed)

    @classmethod
    def _json_error(cls, error):
        return {"ok": False, "error": str(error)}

    @http.route(
        "/odental/contingency",
        type="http",
        auth="user",
        website=True,
        methods=["GET"],
        sitemap=False,
    )
    def contingency(self, **kwargs):
        self._require_professional()
        response = request.render("odental_offline.contingency_page", {})
        for key, value in self.SECURE_HEADERS.items():
            response.headers[key] = value
        return response

    @http.route(
        "/odental/contingency/app.js",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        sitemap=False,
    )
    def contingency_javascript(self, **kwargs):
        with file_open("odental_offline/static/src/js/contingency_app.js", "rb") as stream:
            content = stream.read()
        return request.make_response(
            content,
            headers=[
                ("Content-Type", "text/javascript; charset=utf-8"),
                ("Cache-Control", "public, max-age=300"),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )

    @http.route(
        "/odental/contingency/sw.js",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        sitemap=False,
    )
    def contingency_service_worker(self, **kwargs):
        with file_open(
            "odental_offline/static/src/js/contingency_service_worker.js", "rb"
        ) as stream:
            content = stream.read()
        return request.make_response(
            content,
            headers=[
                ("Content-Type", "text/javascript; charset=utf-8"),
                ("Cache-Control", "no-cache"),
                ("Service-Worker-Allowed", "/odental/"),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )

    @http.route(
        "/odental/contingency/bootstrap",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def contingency_bootstrap(self, **kwargs):
        try:
            user = self._require_professional()
            now = fields.Datetime.now()
            date_from = now - timedelta(hours=12)
            date_to = now + timedelta(hours=48)
            domain = [
                ("state", "in", ["scheduled", "confirmed", "in_progress"]),
                ("start_datetime", ">=", date_from),
                ("start_datetime", "<=", date_to),
            ]
            if not user.has_group("odental_core.group_odental_manager"):
                professional_ids = request.env["odental.professional"].search(
                    [("user_id", "=", user.id)]
                ).ids
                domain.append(("professional_id", "in", professional_ids or [0]))
            appointments = request.env["odental.appointment"].search(
                domain, order="start_datetime, id", limit=500
            )
            return {
                "ok": True,
                "user_id": user.id,
                "user_name": user.display_name,
                "generated_at": fields.Datetime.to_string(now),
                "expires_at": fields.Datetime.to_string(date_to),
                "appointments": [
                    {
                        "id": item.id,
                        "reference": item.name,
                        "organization_id": item.organization_id.id,
                        "organization_name": item.organization_id.name,
                        "patient_id": item.patient_id.id,
                        "patient_reference": item.patient_id.reference,
                        "patient_name": item.patient_id.name,
                        "professional_name": item.professional_id.name,
                        "service_name": item.service_id.name,
                        "site_name": item.site_id.name,
                        "start": fields.Datetime.to_string(item.start_datetime),
                        "end": fields.Datetime.to_string(item.end_datetime),
                        "state": item.state,
                    }
                    for item in appointments
                ],
            }
        except (AccessError, UserError, ValidationError) as error:
            return self._json_error(error)

    @http.route(
        "/odental/contingency/sync",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def contingency_sync(self, device_id=None, batch_uuid=None, entries=None, **kwargs):
        try:
            user = self._require_professional()
            device_id = self._uuid(device_id, "El identificador del dispositivo")
            batch_uuid = self._uuid(batch_uuid, "El identificador del lote")
            if not isinstance(entries, list) or not entries or len(entries) > 100:
                raise ValidationError("Envíe entre 1 y 100 entradas por lote.")

            normalized = []
            organization_ids = set()
            for raw in entries:
                if not isinstance(raw, dict):
                    raise ValidationError("Una entrada del lote no es válida.")
                client_uuid = self._uuid(raw.get("client_uuid"), "El identificador de entrada")
                try:
                    appointment_id = int(raw.get("appointment_id"))
                except (TypeError, ValueError) as error:
                    raise ValidationError("La cita indicada no es válida.") from error
                appointment = request.env["odental.appointment"].browse(appointment_id).exists()
                if not appointment:
                    raise ValidationError("La cita indicada no existe o no está autorizada.")
                organization_ids.add(appointment.organization_id.id)
                try:
                    client_created_at = fields.Datetime.to_datetime(
                        raw.get("client_created_at")
                    )
                except (TypeError, ValueError) as error:
                    raise ValidationError("La fecha de captura no es válida.") from error
                now = fields.Datetime.now()
                if not client_created_at or client_created_at > now + timedelta(minutes=5):
                    raise ValidationError("La fecha de captura está fuera del intervalo permitido.")
                if client_created_at < now - timedelta(days=7):
                    raise ValidationError("La anotación tiene más de siete días y requiere registro manual.")
                normalized.append(
                    {
                        "client_uuid": client_uuid,
                        "appointment_id": appointment.id,
                        "entry_type": (raw.get("entry_type") or "").strip(),
                        "content": (raw.get("content") or "").strip(),
                        "tooth_code": (raw.get("tooth_code") or "").strip(),
                        "surface": (raw.get("surface") or "").strip(),
                        "condition": (raw.get("condition") or "").strip(),
                        "finding_status": (raw.get("finding_status") or "").strip(),
                        "client_created_at": client_created_at,
                    }
                )
            if len(organization_ids) != 1:
                raise ValidationError("Cada lote debe corresponder a una sola organización.")
            organization = request.env["odental.organization"].browse(organization_ids.pop())
            req = request.httprequest
            batch = request.env["odental.contingency.batch"]._ingest(
                organization,
                user,
                device_id,
                batch_uuid,
                normalized,
                metadata={
                    "ip": req.remote_addr or "",
                    "user_agent": req.user_agent.string or "",
                },
            )
            return {
                "ok": True,
                "batch_id": batch.id,
                "batch_name": batch.name,
                "batch_uuid": batch.client_batch_uuid,
                "accepted_entry_uuids": batch.entry_ids.mapped("client_uuid"),
                "state": batch.state,
            }
        except (AccessError, UserError, ValidationError) as error:
            return self._json_error(error)

