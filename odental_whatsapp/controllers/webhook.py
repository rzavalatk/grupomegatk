import json
import logging

from odoo import http
from odoo.http import Response, request


_logger = logging.getLogger(__name__)


class ODentalWhatsAppWebhook(http.Controller):

    @http.route(
        "/odental/whatsapp/webhook/<string:webhook_key>",
        type="http", auth="public", csrf=False, methods=["GET"], sitemap=False,
    )
    def verify_webhook(self, webhook_key, **params):
        account = request.env["odental.whatsapp.account"].sudo().search([
            ("webhook_key", "=", webhook_key), ("active", "=", True),
        ], limit=1)
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")
        if account and mode == "subscribe" and challenge and account._verify_challenge_token(token):
            return Response(challenge, status=200, content_type="text/plain; charset=utf-8")
        return Response("Forbidden", status=403, content_type="text/plain; charset=utf-8")

    @http.route(
        "/odental/whatsapp/webhook/<string:webhook_key>",
        type="http", auth="public", csrf=False, methods=["POST"], sitemap=False,
    )
    def receive_webhook(self, webhook_key, **params):
        account = request.env["odental.whatsapp.account"].sudo().search([
            ("webhook_key", "=", webhook_key), ("active", "=", True),
        ], limit=1)
        if not account:
            return Response("Not found", status=404, content_type="text/plain; charset=utf-8")
        raw_body = request.httprequest.get_data(cache=True)
        signature = request.httprequest.headers.get("X-Hub-Signature-256", "")
        if not account._verify_signature(raw_body, signature):
            return Response("Forbidden", status=403, content_type="text/plain; charset=utf-8")
        try:
            payload = json.loads(raw_body.decode("utf-8"))
            if payload.get("object") != "whatsapp_business_account":
                return Response("Ignored", status=200, content_type="text/plain; charset=utf-8")
            request.env["odental.whatsapp.event"].sudo().with_context(
                odental_whatsapp_webhook=True
            ).ingest_payload(account, payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return Response("Bad request", status=400, content_type="text/plain; charset=utf-8")
        except Exception:
            _logger.exception("No se pudo procesar un webhook WhatsApp verificado")
            return Response("Processing error", status=500, content_type="text/plain; charset=utf-8")
        return Response("EVENT_RECEIVED", status=200, content_type="text/plain; charset=utf-8")

