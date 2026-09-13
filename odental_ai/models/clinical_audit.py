from odoo import fields, models


class ODentalClinicalAudit(models.Model):
    _inherit = "odental.clinical.audit"

    event_type = fields.Selection(
        selection_add=[
            ("ai_session_executed", "Sesión de IA ejecutada"),
            ("ai_session_undone", "Sesión de IA deshecha"),
        ],
        ondelete={
            "ai_session_executed": "cascade",
            "ai_session_undone": "cascade",
        },
    )
