from odoo import api, models
from odoo.tools import email_split
import logging

_logger = logging.getLogger(__name__)

class Report_Visita(models.AbstractModel):
    _name = 'visitas.report'
    _description = 'Reporte de Visitas'

    def _get_report_values(self, docids, data=None):
        _logger.warning(f"docids recibido: {docids}")

        docs = self.env['control.visitas'].browse(docids)
        _logger.warning(f"Registros obtenidos: {docs}")

        return {
            'docs': {
                {
                'name': 'Visita Administración',
                'fecha': '2023-06-01',
                'region': 'Región 1',
                'user_id': 'John Doe',
                }
                },
        }