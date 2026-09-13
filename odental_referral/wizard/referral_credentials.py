from odoo import fields, models


class ODentalReferralCredentialsWizard(models.TransientModel):
    _name = "odental.referral.credentials.wizard"
    _description = "Credenciales temporales de referencia O Dental"

    referral_id = fields.Many2one("odental.referral", required=True, readonly=True)
    credential_purpose = fields.Selection(
        [("patient", "Consentimiento del paciente"), ("recipient", "Acceso del especialista")],
        required=True,
        readonly=True,
    )
    access_url = fields.Char(string="Enlace seguro", required=True, readonly=True)
    one_time_code = fields.Char(
        string="Código temporal", required=True, readonly=True
    )
    expires_at = fields.Datetime(string="Vence el", required=True, readonly=True)
