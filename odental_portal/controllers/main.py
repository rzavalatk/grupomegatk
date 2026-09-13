import hmac
from uuid import uuid4

from odoo import fields, http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class ODentalCustomerPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "odental_patient_count" in counters:
            values["odental_patient_count"] = request.env[
                "odental.patient"
            ].sudo().search_count(
                [("partner_id", "=", request.env.user.partner_id.id)]
            )
        return values


class ODentalPatientPortal(http.Controller):
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
    def _session_key(invitation):
        return f"odental_patient_registration_{invitation.id}"

    @classmethod
    def _render(cls, template, values, status=200):
        response = request.render(template, values, headers=cls.SECURE_HEADERS)
        response.status_code = status
        return response

    @classmethod
    def _invalid(cls, message, status=404):
        return cls._render("odental_portal.portal_invalid", {"message": message}, status)

    def _verified_invitation(self, token):
        invitation = request.env["odental.patient.portal.invitation"]._find_by_token(token)
        if not invitation:
            return invitation
        verified_hash = request.session.get(self._session_key(invitation))
        if not verified_hash or not hmac.compare_digest(
            verified_hash, invitation.token_hash or ""
        ):
            return request.env["odental.patient.portal.invitation"].browse()
        return invitation

    @staticmethod
    def _metadata():
        req = request.httprequest
        return (req.remote_addr or "")[:64], (req.user_agent.string or "")[:512]

    @staticmethod
    def _clean(value, limit):
        return (value or "").strip()[:limit]

    @http.route(
        "/odental/register/<string:token>",
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=False,
    )
    def registration(self, token, **kwargs):
        invitation = request.env["odental.patient.portal.invitation"]._find_by_token(token)
        if not invitation:
            return self._invalid("Esta invitación no existe, venció o ya fue utilizada.")
        if not self._verified_invitation(token):
            return self._render(
                "odental_portal.portal_registration_verify",
                {"invitation": invitation, "token": token, "error": kwargs.get("error")},
            )
        return self._render(
            "odental_portal.portal_registration_form",
            {
                "invitation": invitation,
                "patient": invitation.patient_id,
                "token": token,
                "error": kwargs.get("error"),
                "form_values": kwargs,
            },
        )

    @http.route(
        "/odental/register/<string:token>/verify",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
        sitemap=False,
    )
    def registration_verify(self, token, code=None, **kwargs):
        invitation = request.env["odental.patient.portal.invitation"]._find_by_token(token)
        if not invitation:
            return self._invalid("Esta invitación no existe, venció o ya fue utilizada.")
        success, error = invitation._verify_otp(code)
        if not success:
            return self._render(
                "odental_portal.portal_registration_verify",
                {"invitation": invitation, "token": token, "error": error},
                400,
            )
        request.session[self._session_key(invitation)] = invitation.token_hash
        return request.redirect(f"/odental/register/{token}")

    @http.route(
        "/odental/register/<string:token>/submit",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
        sitemap=False,
    )
    def registration_submit(self, token, **values):
        invitation = self._verified_invitation(token)
        if not invitation:
            return self._invalid("Debe validar nuevamente su identidad.", 403)
        patient = invitation.patient_id
        name = self._clean(values.get("name"), 200)
        mobile = self._clean(values.get("mobile"), 40)
        email = self._clean(values.get("email"), 254)
        if not name or not (mobile or email):
            return self._render(
                "odental_portal.portal_registration_form",
                {
                    "invitation": invitation,
                    "patient": patient,
                    "token": token,
                    "error": "Ingrese su nombre y al menos un teléfono o correo.",
                    "form_values": values,
                },
                400,
            )
        try:
            birthdate = fields.Date.to_date(values.get("birthdate")) if values.get("birthdate") else False
        except (TypeError, ValueError):
            birthdate = False
        if values.get("birthdate") and not birthdate:
            return self._render(
                "odental_portal.portal_registration_form",
                {
                    "invitation": invitation,
                    "patient": patient,
                    "token": token,
                    "error": "La fecha de nacimiento no es válida.",
                    "form_values": values,
                },
                400,
            )
        if values.get("truth_confirmed") != "yes":
            return self._render(
                "odental_portal.portal_registration_form",
                {
                    "invitation": invitation,
                    "patient": patient,
                    "token": token,
                    "error": "Confirme que la información suministrada es verdadera.",
                    "form_values": values,
                },
                400,
            )
        clinical_record = request.env["odental.clinical.record"].sudo().search(
            [("patient_id", "=", patient.id), ("state", "=", "active")], limit=1
        )
        if not clinical_record:
            return self._invalid(
                "La clínica debe habilitar su expediente antes de recibir el formulario.", 409
            )
        ip_address, user_agent = self._metadata()
        try:
            with request.env.cr.savepoint():
                update = request.env["odental.patient.update.request"].with_context(
                    odental_portal_submission=True
                ).sudo().create(
                    {
                        "patient_id": patient.id,
                        "invitation_id": invitation.id,
                        "requested_name": name,
                        "requested_identification": self._clean(
                            values.get("identification"), 80
                        ),
                        "requested_birthdate": birthdate,
                        "requested_mobile": mobile,
                        "requested_email": email,
                        "submitted_ip_address": ip_address,
                        "submitted_user_agent": user_agent,
                    }
                )
                intake = request.env["odental.patient.intake"].with_context(
                    odental_portal_submission=True
                ).sudo().create(
                    {
                        "patient_id": patient.id,
                        "clinical_record_id": clinical_record.id,
                        "invitation_id": invitation.id,
                        "allergies": self._clean(values.get("allergies"), 3000),
                        "medications": self._clean(values.get("medications"), 3000),
                        "medical_conditions": self._clean(
                            values.get("medical_conditions"), 3000
                        ),
                        "surgeries": self._clean(values.get("surgeries"), 3000),
                        "anesthesia_reactions": self._clean(
                            values.get("anesthesia_reactions"), 3000
                        ),
                        "pregnancy": values.get("pregnancy") == "yes",
                        "pregnancy_details": self._clean(
                            values.get("pregnancy_details"), 300
                        ),
                        "other_information": self._clean(
                            values.get("other_information"), 3000
                        ),
                        "truth_confirmed": True,
                        "submitted_ip_address": ip_address,
                        "submitted_user_agent": user_agent,
                    }
                )
                invitation._mark_used(ip_address)
        except (UserError, ValidationError) as error:
            return self._render(
                "odental_portal.portal_registration_form",
                {
                    "invitation": invitation,
                    "patient": patient,
                    "token": token,
                    "error": str(error),
                    "form_values": values,
                },
                400,
            )
        request.session.pop(self._session_key(invitation), None)
        return self._render(
            "odental_portal.portal_registration_received",
            {"patient": patient, "update": update, "intake": intake},
        )

    @staticmethod
    def _portal_patient():
        partner = request.env.user.partner_id
        if not partner:
            return request.env["odental.patient"].browse()
        return request.env["odental.patient"].sudo().search(
            [("partner_id", "=", partner.id)], limit=1
        )

    @http.route(
        ["/my/odental"], type="http", auth="user", website=True, sitemap=False
    )
    def patient_home(self, **kwargs):
        patient = self._portal_patient()
        if not patient:
            return self._invalid("Su usuario todavía no está vinculado a un paciente.", 403)
        now = fields.Datetime.now()
        appointments = request.env["odental.appointment"].sudo().search(
            [
                ("patient_id", "=", patient.id),
                ("start_datetime", ">=", now),
                ("state", "in", ("scheduled", "confirmed")),
            ],
            order="start_datetime asc",
        )
        record = request.env["odental.clinical.record"].sudo().search(
            [("patient_id", "=", patient.id)], limit=1
        )
        plans = request.env["odental.treatment.plan"].sudo().search(
            [
                ("clinical_record_id", "=", record.id),
                ("state", "in", ("offered", "approved", "in_progress", "completed")),
            ],
            order="create_date desc",
        ) if record else request.env["odental.treatment.plan"].browse()
        invoices = request.env["account.move"].sudo().search(
            [
                ("odental_patient_id", "=", patient.id),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
            ],
            order="invoice_date desc, id desc",
        )
        agreements = request.env["odental.payment.agreement"].sudo().search(
            [("patient_id", "=", patient.id), ("state", "!=", "cancelled")],
            order="create_date desc",
        )
        consents = request.env["odental.patient.consent"].sudo().search(
            [("patient_id", "=", patient.id), ("state", "=", "pending")],
            order="create_date desc",
        )
        return self._render(
            "odental_portal.portal_patient_home",
            {
                "patient": patient,
                "appointments": appointments,
                "plans": plans,
                "invoices": invoices,
                "agreements": agreements,
                "consents": consents,
            },
        )

    @http.route(
        "/my/odental/consent/<int:consent_id>",
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
        csrf=True,
        sitemap=False,
    )
    def patient_consent(self, consent_id, **values):
        patient = self._portal_patient()
        consent = request.env["odental.patient.consent"].sudo().search(
            [("id", "=", consent_id), ("patient_id", "=", patient.id), ("state", "=", "pending")],
            limit=1,
        ) if patient else request.env["odental.patient.consent"].browse()
        if not consent:
            return self._invalid("El consentimiento no está disponible.", 404)
        if request.httprequest.method == "POST":
            if values.get("accepted") != "yes":
                return self._render(
                    "odental_portal.portal_patient_consent",
                    {"patient": patient, "consent": consent, "error": "Debe confirmar la aceptación."},
                    400,
                )
            signer_name = self._clean(values.get("signer_name"), 200)
            signer_identification = self._clean(
                values.get("signer_identification"), 80
            )
            if not signer_name or not signer_identification:
                return self._render(
                    "odental_portal.portal_patient_consent",
                    {"patient": patient, "consent": consent, "error": "Complete los datos del firmante."},
                    400,
                )
            consent.write(
                {
                    "signer_type": (
                        values.get("signer_type")
                        if values.get("signer_type") in {"patient", "representative"}
                        else "patient"
                    ),
                    "signer_name": signer_name,
                    "signer_identification": signer_identification,
                    "verification_method": "secure_portal",
                    "verification_reference": f"portal-session-{uuid4().hex}",
                }
            )
            consent.action_sign()
            return self._render(
                "odental_portal.portal_patient_consent_signed",
                {"patient": patient, "consent": consent},
            )
        return self._render(
            "odental_portal.portal_patient_consent",
            {"patient": patient, "consent": consent, "error": False},
        )
