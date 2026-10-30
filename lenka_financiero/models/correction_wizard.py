from odoo import fields, models


class LenkaCorrectionWizard(models.TransientModel):
    _name = 'lenka.correction.wizard'
    _description = 'Motivo de devolución a revisión'

    operation_id = fields.Many2one('lenka.financial.operation', required=True, readonly=True)
    reason = fields.Text(string='Motivo de la devolución', required=True)

    def action_confirm(self):
        self.ensure_one()
        self.operation_id._return_for_correction(self.reason)
        return {'type': 'ir.actions.act_window_close'}
