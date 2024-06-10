from odoo import models, fields

class Cuota(models.Model):
    _name = 'cuota'
    _description = 'Modelo de Cuota'

    prestamo_id = fields.Many2one('prestamo', string='Préstamo', required=True, ondelete='cascade')
    amount = fields.Float(string='Monto de la Cuota', required=True)
    date_due = fields.Date(string='Fecha de Vencimiento', required=True)
    pagado = fields.Boolean(string='Pagado', default=False)

    def generar_factura(self):
        for cuota in self:
            factura = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': cuota.prestamo_id.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'name': 'Cuota de Préstamo',
                    'quantity': 1,
                    'price_unit': cuota.monto,
                })]
            })
            cuota.write({'pagado': True})
