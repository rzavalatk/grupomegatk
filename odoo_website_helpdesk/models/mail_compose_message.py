# -*- coding: utf-8 -*-
from odoo import fields, models


class MailComposeMessage(models.TransientModel):
    """ Esta clase amplía la funcionalidad de 'mail.compose.message'
    modelo para incluir un comportamiento personalizado para el envío de correos electrónicos relacionados con tickets de ayuda.
   """
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, auto_commit=False):
        """Anulación del método base '_action_send_mail' para incluir información adicional
        lógica al enviar correos electrónicos relacionados con tickets de ayuda.

        Si el modelo asociado al correo es 'help.ticket', actualice el
        Campo 'replied_date' del ticket de ayuda asociado hasta la fecha actual.
        """
        if self.model == 'help.ticket':
            ticket_id = self.env['help.ticket'].browse(self.res_id)
            ticket_id.replied_date = fields.Date.today()
        return super(MailComposeMessage, self)._action_send_mail(
            auto_commit=auto_commit)
