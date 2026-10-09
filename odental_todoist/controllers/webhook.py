"""Signed Todoist notifications. The polling job remains the recovery path."""

import base64
import hashlib
import hmac
import json
import logging

from odoo import http
from odoo.http import request
from werkzeug.wrappers import Response


_logger = logging.getLogger(__name__)
_EVENTS = {
    "item:added", "item:updated", "item:deleted",
    "item:completed", "item:uncompleted",
}


def valid_signature(secret, body, signature):
    if not secret or not signature:
        return False
    expected = base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(expected, signature)


class ODentalTodoistWebhook(http.Controller):
    @http.route("/odental/todoist/webhook", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    def todoist_webhook(self, **_kwargs):
        body = request.httprequest.get_data()
        if len(body) > 262144:
            return Response(status=413)
        secret = request.env["ir.config_parameter"].sudo().get_param(
            "odental_todoist.webhook_client_secret"
        )
        if not secret:
            return Response(status=404)
        signature = request.httprequest.headers.get("X-Todoist-Hmac-SHA256", "")
        if not valid_signature(secret, body, signature):
            return Response(status=403)
        try:
            data = json.loads(body)
        except (ValueError, UnicodeError):
            return Response(status=400)
        if not isinstance(data, dict) or data.get("event_name") not in _EVENTS:
            return Response(status=200)
        user_id = str(data.get("user_id") or "")
        if not user_id or not user_id.isdigit():
            return Response(status=400)

        connections = request.env["odental.todoist.connection"].sudo().search([
            ("active", "=", True), ("todoist_user_id", "=", user_id),
        ])
        for connection in connections:
            try:
                with request.env.cr.savepoint():
                    # Prevent a duplicate delivery from racing another webhook
                    # for the same doctor. The periodic job still reconciles.
                    request.env.cr.execute(
                        "SELECT pg_try_advisory_xact_lock(%s, %s)",
                        (768802, connection.id),
                    )
                    if not request.env.cr.fetchone()[0]:
                        continue
                    connection._sync_one()
            except Exception:
                _logger.exception("Todoist webhook reconciliation failed for connection %s", connection.id)
                return Response(status=503)
        return Response(status=200)
