from odoo import fields, models


class ODentalClinicalAudit(models.Model):
    _inherit = "odental.clinical.audit"

    event_type = fields.Selection(
        selection_add=[
            ("offline_received", "Contingencia recibida"),
            ("offline_applied", "Contingencia aplicada"),
        ],
        ondelete={"offline_received": "cascade", "offline_applied": "cascade"},
    )
