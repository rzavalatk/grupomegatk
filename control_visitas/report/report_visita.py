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
