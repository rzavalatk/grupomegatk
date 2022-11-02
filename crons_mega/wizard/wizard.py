# -*- coding: utf-8 -*-
from odoo import fields, models


class ModelMail(models.TransientModel):
    _name = "account.cierre.mail"

    mail = fields.Char("Destinatario")
    
    
    def obtener_mail(self):
        active_id = self._context.get('active_id')
        cierre_id = self.env['account.cierre'].browse(active_id)
        cierre_id.send_email(self.mail)