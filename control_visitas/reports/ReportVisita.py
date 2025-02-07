from odoo import api, models

class ReportVisita(models.AbstractModel):
    _name = 'report.control_visitas.report_visita'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['control.visitas'].browse(docids)
        return {
            'docs': docs,
        }
