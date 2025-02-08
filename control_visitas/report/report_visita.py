from odoo import api, models
from odoo.tools import email_split
import logging

_logger = logging.getLogger(__name__)

class Report_Visita(models.AbstractModel):
    _name = 'control_visitas.report_pdf'
    _description = 'Reporte de Visitas'

    @api.model
    def _get_report_values(self, docids, data=None):
        _logger.warning(f"docids recibido: {docids}")

        docs = self.env['control.visitas'].browse(docids)
        _logger.warning(f"Registros obtenidos: {docs}")

        # Llamar a la función para enviar el correo
        self.enviar_correo_con_reporte(docs)

        return {
            'docs': docs,
        }

    def enviar_correo_con_reporte(self, docs):
        """
        Envía un correo electrónico con el reporte adjunto.
        """
        # Obtener el template de correo
        template = self.env.ref('control_visitas.email_template_reporte_visitas', raise_if_not_found=False)
        if not template:
            _logger.error("Plantilla de correo no encontrada.")
            return

        # Obtener el reporte PDF
        report = self.env['ir.actions.report']._get_report_from_name('control_visitas.report_pdf')
        pdf_content, _ = report._render_qweb_pdf(docs.ids)

        # Adjuntar el PDF al correo
        attachment = self.env['ir.attachment'].create({
            'name': f"Reporte_Visitas_{docs[0].name}.pdf",
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'control.visitas',
            'res_id': docs[0].id,
            'mimetype': 'application/pdf',
        })

        # Enviar el correo
        for doc in docs:
            if doc.user_id.email:
                template.send_mail(doc.id, force_send=True, email_values={
                    'attachment_ids': [attachment.id],
                    'email_to': doc.user_id.email,
                })
                _logger.warning(f"Correo enviado a {doc.user_id.email}")
            else:
                _logger.warning(f"No se encontró un correo para el usuario {doc.user_id.name}")