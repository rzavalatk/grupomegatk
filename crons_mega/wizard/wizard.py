# -*- coding: utf-8 -*-
from odoo import fields, models


class ModelMail(models.TransientModel):
    _name = "account.cierre.mail"

    mail = fields.Char("Destinatarios")
    cc = fields.Char("CC")
    
    
    def obtener_mail(self):
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        cierre_id = self.env[active_model].browse(active_id)
        cierre_id.send_email(self.mail,self.cc)