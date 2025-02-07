from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

class ReportVisita(models.AbstractModel):
    _name = 'control_visitas.report_pdf'
    _description = 'Reporte de Visitas' 

    @api.model
    def _get_report_values(self, docids, data=None):
        _logger.warning(f"docids recibido: {docids}")

        docs = self.env['control.visitas'].browse(docids)
        _logger.warning(f"Registros obtenidos: {docs}")

        return {
            'docs': docs,
        }
