# -*- coding: utf-8 -*-
from odoo import models


class AccountPaymentRegister(models.TransientModel):
    """Modificar el estado de la línea de reembolso del préstamo en función del estado de la factura"""
    _inherit = 'account.payment.register'

    def _post_payments(self, to_process, edit_mode=False):
        """Cambiar el estado del registro de reembolso a «pagado» al registrar el pago"""
        res = super()._post_payments(to_process, edit_mode=False)
        for record in self:
            loan_line_id = self.env['repayment.line'].search([
                ('name', 'ilike', record.communication)])
            loan_line_id.write({'state': 'paid'})
        return res
