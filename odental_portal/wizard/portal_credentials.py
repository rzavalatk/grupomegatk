from html import escape
from urllib.parse import quote

from odoo import api, fields, models


class ODentalPatientPortalCredentials(models.TransientModel):
    _name = "odental.patient.portal.credentials"
    _description = "Credenciales temporales del portal O Dental"
    _transient_max_hours = 0.25

    invitation_id = fields.Many2one(
        "odental.patient.portal.invitation", required=True, readonly=True
    )
    access_url = fields.Char(string="Enlace de registro", required=True, readonly=True)
    otp = fields.Char(string="Código temporal", required=True, readonly=True)
    qr_preview = fields.Html(compute="_compute_qr_preview", sanitize=False)
    warning = fields.Text(
        readonly=True,
        default=(
            "El enlace y el código se muestran una sola vez. Envíelos por canales separados "
            "cuando sea posible; no copie el código dentro del expediente."
        ),
    )

    @api.depends("access_url")
    def _compute_qr_preview(self):
        for wizard in self:
            encoded = quote(wizard.access_url or "", safe="")
            src = f"/report/barcode/QR/{encoded}?width=260&height=260"
            wizard.qr_preview = (
                f'<div class="text-center"><img src="{escape(src)}" '
                'alt="Código QR de registro" style="max-width:260px"/></div>'
            )
