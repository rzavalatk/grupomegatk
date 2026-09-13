import hashlib

from odoo import fields, models
from odoo.exceptions import AccessError, ValidationError


class ODentalWhatsAppCredentialsWizard(models.TransientModel):
    _name = "odental.whatsapp.credentials.wizard"
    _description = "Configurar credenciales WhatsApp O Dental"

    account_id = fields.Many2one("odental.whatsapp.account", required=True, readonly=True)
    access_token = fields.Char(string="Token de acceso")
    app_secret = fields.Char(string="Secreto de la aplicación")
    verify_token = fields.Char(
        string="Token de verificación",
        help="Cadena privada elegida por la clínica y registrada también en Meta.",
    )

    def action_save(self):
        self.ensure_one()
        if not self.env.user.has_group("odental_core.group_odental_admin"):
            raise AccessError("Solo el administrador O Dental puede configurar credenciales.")
        if not any((self.access_token, self.app_secret, self.verify_token)):
            raise ValidationError("Ingrese al menos una credencial para actualizar.")
        if self.access_token:
            self.account_id._set_secret("access_token", self.access_token.strip())
        if self.app_secret:
            self.account_id._set_secret("app_secret", self.app_secret.strip())
        if self.verify_token:
            digest = hashlib.sha256(self.verify_token.strip().encode()).hexdigest()
            self.account_id._set_secret("verify_token_hash", digest)
        self.account_id.invalidate_recordset(["credentials_configured"])
        return {"type": "ir.actions.act_window_close"}
