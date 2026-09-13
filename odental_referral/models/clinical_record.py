from odoo import fields, models


class ODentalClinicalRecord(models.Model):
    _inherit = "odental.clinical.record"

    referral_ids = fields.One2many(
        "odental.referral", "clinical_record_id", string="Referencias profesionales"
    )

