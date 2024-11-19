#MODELO PARA CAMBIAR LOS ESTADOS DE LAS CUOTAS CUANDO SE CANCELA LA FACTURA O SE MANDA A ESTADO BORRADOR
#CAMBIO DE ESTADO DE LA CUOTA DESDE LA FACTURA RELACIONADA A LA MISMA

from odoo import models


class AccountMove(models.Model):
    """Alterar el estado de la línea de reembolso del préstamo al pulsar el botón de borrador y cancelación"""
    _inherit = 'account.move'

    def button_draft(self):
        """Cambiar el estado del registro de reembolso a «facturado»
        mientras se restablece para redactar la factura"""
        res = super().button_draft()
        loan_line_ids = self.env['repayment.line'].search([
            ('name', 'ilike', self.payment_reference)])
        if loan_line_ids:
            loan_line_ids.update({
                'state': 'invoiced',
                'invoice': True
            })
        return res

    def button_cancel(self):
        """Cambiar el estado del registro de reembolso a «impagado».
        al anular la factura"""
        res = super().button_cancel()
        for record in self:
            loan_line_ids = self.env['repayment.line'].search([
                ('name', 'ilike', record.payment_reference)])
            if loan_line_ids:
                loan_line_ids.update({
                    'state': 'unpaid',
                    'invoice': False
                })
        return res
