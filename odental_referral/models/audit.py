from odoo import fields, models


class ODentalClinicalAudit(models.Model):
    _inherit = "odental.clinical.audit"

    event_type = fields.Selection(
        selection_add=[
            ("referral_created", "Referencia creada"),
            ("referral_consent_requested", "Consentimiento de referencia solicitado"),
            ("referral_activated", "Acceso de referencia activado"),
            ("referral_accessed", "Referencia consultada"),
            ("referral_revoked", "Acceso de referencia revocado"),
            ("referral_rejected", "Referencia rechazada"),
            ("referral_closed", "Referencia cerrada"),
            ("referral_expired", "Acceso de referencia vencido"),
            ("referral_invalidated", "Referencia invalidada por cambio de alcance"),
            ("referral_report_submitted", "Informe externo recibido"),
            ("referral_report_reviewed", "Informe externo revisado"),
        ],
        ondelete={
            "referral_created": "cascade",
            "referral_consent_requested": "cascade",
            "referral_activated": "cascade",
            "referral_accessed": "cascade",
            "referral_revoked": "cascade",
            "referral_rejected": "cascade",
            "referral_closed": "cascade",
            "referral_expired": "cascade",
            "referral_invalidated": "cascade",
            "referral_report_submitted": "cascade",
            "referral_report_reviewed": "cascade",
        },
    )
