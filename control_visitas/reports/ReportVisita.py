from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

class ReportVisita(models.AbstractModel):
    _name = 'report.control_visitas.report_visita'

    @api.model
    def _get_report_values(self, docids, data=None):
        _logger.info(f"docids recibido: {docids}")
        
        docs = self.env['control.visitas'].browse(docids)
        _logger.info(f"Registros obtenidos: {docs}")
        
        return {
            'docs': docs,
        }
