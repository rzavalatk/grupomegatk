import base64
import binascii
import hmac

from werkzeug.utils import secure_filename

from odoo import http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request


class ODentalReferralPortal(http.Controller):
    INLINE_MIMETYPES = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/pdf",
    }
    SECURE_HEADERS = {
        "Cache-Control": "private, no-store, max-age=0",
        "Pragma": "no-cache",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-Robots-Tag": "noindex, nofollow, noarchive",
        "Content-Security-Policy": (
            "default-src 'self'; img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
            "font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
            "base-uri 'self'; form-action 'self'"
        ),
    }

    @staticmethod
    def _session_key(referral):
        return f"odental_referral_verified_{referral.id}"

    @staticmethod
    def _consent_session_key(referral):
        return f"odental_referral_consent_verified_{referral.id}"

    def _verified_referral(self, token):
        referral = request.env["odental.referral"]._find_by_token(token)
        if not referral:
            return referral
        session_hash = request.session.get(self._session_key(referral))
        if not session_hash or not hmac.compare_digest(
            session_hash, referral.access_token_hash or ""
        ):
            return request.env["odental.referral"].browse()
        return referral

    def _verified_consent_referral(self, token):
        referral = request.env["odental.referral"]._find_by_consent_token(token)
        if not referral:
            return referral
        session_hash = request.session.get(self._consent_session_key(referral))
        if not session_hash or not hmac.compare_digest(
            session_hash, referral.consent_access_token_hash or ""
        ):
            return request.env["odental.referral"].browse()
        return referral

    @staticmethod
    def _request_metadata():
        http_request = request.httprequest
        return http_request.remote_addr, http_request.user_agent.string

    @staticmethod
    def _secure_render(template, values, status=200):
        response = request.render(
            template,
            values,
            headers=ODentalReferralPortal.SECURE_HEADERS,
        )
        response.status_code = status
        return response

    @classmethod
    def _invalid_response(cls, message, status=404):
        return cls._secure_render(
            "odental_referral.portal_referral_invalid",
            {"message": message},
            status,
        )

    @http.route(
        "/odental/referral/consent/<string:token>",
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=False,
    )
    def referral_consent(self, token, **kwargs):
        referral = request.env["odental.referral"]._find_by_consent_token(token)
        if not referral:
            return self._invalid_response(
                "Este consentimiento no existe, venció o ya fue utilizado."
            )
        verified = self._verified_consent_referral(token)
        if not verified:
            return self._secure_render(
                "odental_referral.portal_consent_verify",
                {"referral": referral, "token": token, "error": kwargs.get("error")},
            )
        return self._secure_render(
            "odental_referral.portal_consent_document",
            {"referral": referral, "token": token, "error": kwargs.get("error")},
        )

    @http.route(
        "/odental/referral/consent/<string:token>/verify",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
        sitemap=False,
    )
    def referral_consent_verify(self, token, code=None, **kwargs):
        referral = request.env["odental.referral"]._find_by_consent_token(token)
        if not referral:
            return self._invalid_response(
                "Este consentimiento no existe, venció o ya fue utilizado."
            )
        ip_address, user_agent = self._request_metadata()
        success, error = referral._verify_consent_otp(
            token, code, ip_address, user_agent
        )
        if not success:
            return self._secure_render(
                "odental_referral.portal_consent_verify",
                {"referral": referral, "token": token, "error": error},
            )
        request.session[self._consent_session_key(referral)] = (
            referral.consent_access_token_hash
        )
        return request.redirect(f"/odental/referral/consent/{token}")

    @http.route(
        "/odental/referral/consent/<string:token>/sign",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
        sitemap=False,
    )
    def referral_consent_sign(
        self,
        token,
        signer_name=None,
        signer_identification=None,
        signer_type="patient",
        accepted=None,
        **kwargs,
    ):
        referral = self._verified_consent_referral(token)
        if not referral:
            return self._invalid_response("Debe validar nuevamente su identidad.", 403)
        if not accepted:
            return self._secure_render(
                "odental_referral.portal_consent_document",
                {
                    "referral": referral,
                    "token": token,
                    "error": "Debe confirmar que leyó y acepta el consentimiento.",
                },
                400,
            )
        try:
            ip_address, user_agent = self._request_metadata()
            consent = referral._portal_sign_consent(
                signer_name,
                signer_identification,
                signer_type,
                ip_address,
                user_agent,
            )
        except (UserError, ValidationError) as error:
            return self._secure_render(
                "odental_referral.portal_consent_document",
                {"referral": referral, "token": token, "error": str(error)},
                400,
            )
        request.session.pop(self._consent_session_key(referral), None)
        return self._secure_render(
            "odental_referral.portal_consent_signed",
            {"referral": referral, "consent": consent},
        )

    @http.route(
        "/odental/referral/<string:token>",
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=False,
    )
    def referral_access(self, token, **kwargs):
        referral = request.env["odental.referral"]._find_by_token(token)
        if not referral:
            return self._invalid_response("Este acceso no existe, venció o fue revocado.")
        verified = self._verified_referral(token)
        if not verified:
            return self._secure_render(
                "odental_referral.portal_referral_verify",
                {"referral": referral, "token": token, "error": kwargs.get("error")},
            )
        ip_address, user_agent = self._request_metadata()
        if not referral._register_view(ip_address, user_agent):
            return self._invalid_response("Este acceso ya no está disponible.", 403)
        return self._secure_render(
            "odental_referral.portal_referral_detail",
            {
                "referral": referral,
                "token": token,
                "submitted": kwargs.get("submitted"),
            },
        )

    @http.route(
        "/odental/referral/<string:token>/verify",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
        sitemap=False,
    )
    def referral_verify(self, token, code=None, **kwargs):
        referral = request.env["odental.referral"]._find_by_token(token)
        if not referral:
            return self._invalid_response("Este acceso no existe, venció o fue revocado.")
        ip_address, user_agent = self._request_metadata()
        success, error = referral._verify_otp(
            token, code, ip_address, user_agent
        )
        if not success:
            return self._secure_render(
                "odental_referral.portal_referral_verify",
                {"referral": referral, "token": token, "error": error},
            )
        request.session[self._session_key(referral)] = referral.access_token_hash
        return request.redirect(f"/odental/referral/{token}")

    @http.route(
        "/odental/referral/<string:token>/image/<int:image_id>",
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=False,
    )
    def referral_image(self, token, image_id, download=False, **kwargs):
        referral = self._verified_referral(token)
        if not referral:
            return self._invalid_response("Debe validar nuevamente su acceso.", 403)
        image = referral.image_ids.filtered(lambda item: item.id == image_id)
        if not image:
            return self._invalid_response("El archivo no forma parte de esta referencia.", 404)
        if download and not referral.allow_file_download:
            return self._invalid_response("La descarga de archivos no fue autorizada.", 403)
        mimetype = image.mimetype or "application/octet-stream"
        if not download and mimetype not in self.INLINE_MIMETYPES:
            return self._invalid_response(
                "Este tipo de archivo no admite visualización segura en línea.", 403
            )
        try:
            raw_file = base64.b64decode(image.file_data or b"", validate=True)
        except (binascii.Error, ValueError, TypeError):
            return self._invalid_response("El archivo clínico no está disponible.", 404)
        disposition = "attachment" if download and referral.allow_file_download else "inline"
        response_mimetype = (
            mimetype if disposition == "inline" else "application/octet-stream"
        )
        filename = secure_filename(image.filename or "clinical-file")
        ip_address, user_agent = self._request_metadata()
        referral._log_access(
            "file_download" if disposition == "attachment" else "file_view",
            True,
            f"Archivo consultado: {image.name}",
            ip_address,
            user_agent,
        )
        return request.make_response(
            raw_file,
            headers=[
                ("Content-Type", response_mimetype),
                ("Content-Disposition", f'{disposition}; filename="{filename}"'),
                ("Cache-Control", "private, no-store, max-age=0"),
                ("Content-Security-Policy", "sandbox; default-src 'none'"),
                ("Referrer-Policy", "no-referrer"),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )

    @http.route(
        "/odental/referral/<string:token>/report",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
        sitemap=False,
    )
    def referral_report(self, token, summary=None, **kwargs):
        referral = self._verified_referral(token)
        if not referral:
            return self._invalid_response("Debe validar nuevamente su acceso.", 403)
        if referral.access_level != "read_report":
            return self._invalid_response("Esta referencia no permite entregar informes.", 403)
        if referral.report_ids:
            return self._invalid_response("El informe de esta referencia ya fue recibido.", 409)
        if not (summary or "").strip():
            return self._invalid_response("El informe debe incluir hallazgos o recomendaciones.", 400)
        upload = request.httprequest.files.get("report_file")
        file_data = filename = False
        if upload and upload.filename:
            raw_file = upload.read(10 * 1024 * 1024 + 1)
            if len(raw_file) > 10 * 1024 * 1024:
                return self._invalid_response("El archivo no puede superar 10 MB.", 400)
            file_data = base64.b64encode(raw_file)
            filename = secure_filename(upload.filename)
        report = request.env["odental.referral.report"].sudo().create(
            {
                "referral_id": referral.id,
                "author_name": referral.recipient_name,
                "summary": summary.strip(),
                "file_data": file_data,
                "filename": filename,
            }
        )
        request.session.pop(self._session_key(referral), None)
        return self._secure_render(
            "odental_referral.portal_referral_report_received",
            {"referral": referral, "report": report},
        )
