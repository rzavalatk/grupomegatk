from odoo import fields, models


class ODentalClinicalAudit(models.Model):
    _inherit = "odental.clinical.audit"

    event_type = fields.Selection(
        selection_add=[
            ("odontogram_created", "Odontograma creado"),
            ("odontogram_signed", "Odontograma firmado"),
            ("odontogram_amended", "Odontograma rectificado"),
            ("image_created", "Imagen clínica creada"),
            ("image_finalized", "Imagen clínica finalizada"),
            ("image_archived", "Imagen clínica archivada"),
        ],
        ondelete={
            "odontogram_created": "cascade",
            "odontogram_signed": "cascade",
            "odontogram_amended": "cascade",
            "image_created": "cascade",
            "image_finalized": "cascade",
            "image_archived": "cascade",
        },
    )

