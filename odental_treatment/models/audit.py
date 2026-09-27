from odoo import fields, models


class ODentalClinicalAudit(models.Model):
    _inherit = "odental.clinical.audit"

    event_type = fields.Selection(
        selection_add=[
            ("treatment_created", "Plan de tratamiento creado"),
            ("treatment_offered", "Presupuesto presentado"),
            ("treatment_approved", "Presupuesto aprobado"),
            ("treatment_rejected", "Presupuesto rechazado"),
            ("treatment_revised", "Plan de tratamiento revisado"),
            ("treatment_started", "Tratamiento iniciado"),
            ("treatment_completed", "Tratamiento completado"),
            ("treatment_cancelled", "Tratamiento cancelado"),
            ("quotation_created", "Cotización creada"),
        ],
        ondelete={
            "treatment_created": "cascade",
            "treatment_offered": "cascade",
            "treatment_approved": "cascade",
            "treatment_rejected": "cascade",
            "treatment_revised": "cascade",
            "treatment_started": "cascade",
            "treatment_completed": "cascade",
            "treatment_cancelled": "cascade",
            "quotation_created": "cascade",
        },
    )
