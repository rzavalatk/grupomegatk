
from odoo import models, fields, api
from odoo.http import request
import qrcode
import base64
from io import BytesIO

def generate_qr_code(value):
    qr = qrcode.QRCode(
             version=1,
             error_correction=qrcode.constants.ERROR_CORRECT_L,
             box_size=30,
             border=4)
    qr.add_data(value)
    qr.make(fit=True)
    img = qr.make_image()
    stream = BytesIO()
    img.save(stream, format="PNG")
    qr_img = base64.b64encode(stream.getvalue())
    return qr_img



class AccountMove(models.Model):
    _inherit = 'account.move'

    qr_image = fields.Binary("QR Code", compute='_generate_qr_code')
    qr_in_report = fields.Boolean('¿Añadir QR a la factura?')

    def _generate_qr_code(self):
        for order in self:
            if self.env.company.id == 8:
                base_url = 'megatk.net'
            elif self.env.company.id == 9:
                base_url = 'meditekhn.net'
            else:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                
            # Construye el enlace que quieres que aparezca en el código QR
            invoice_url = "{}/web/login?redirect=/my/invoices/{}".format(base_url, order.id)
            # Genera el código QR con el enlace
            qr_img = generate_qr_code(invoice_url)

            order.qr_image = qr_img
            print(self.qr_image, "qr_imageqr_image--------------------")
