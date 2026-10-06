from odoo import fields, models


class ODentalClinicalRecord(models.Model):
    _inherit = "odental.clinical.record"

    odontogram_ids = fields.One2many(
        "odental.odontogram", "clinical_record_id", string="Odontogramas"
    )
    clinical_image_ids = fields.One2many(
        "odental.clinical.image", "clinical_record_id", string="Imágenes clínicas"
    )

