from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    bac_payment_enabled = fields.Boolean(
        string='Usa link BAC',
        help='Activa el control BAC para este producto.',
    )
    bac_payment_link = fields.Char(
        string='Link de pago BAC',
        help='Enlace fijo entregado por BAC para este producto.',
    )
    bac_payment_amount = fields.Monetary(
        string='Monto BAC',
        currency_field='bac_payment_currency_id',
        help='Monto exacto con el que fue configurado el enlace BAC.',
    )
    bac_payment_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda BAC',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    bac_payment_notes = fields.Text(
        string='Notas BAC',
        help='Referencia interna o notas de uso del enlace BAC.',
    )

    @api.constrains('bac_payment_enabled', 'bac_payment_link', 'bac_payment_amount')
    def _check_bac_payment_configuration(self):
        for product in self:
            if not product.bac_payment_enabled:
                continue
            if not product.bac_payment_link:
                raise ValidationError(_('Debe definir el link de pago BAC.'))
            if product.bac_payment_amount <= 0:
                raise ValidationError(_('El monto BAC debe ser mayor que cero.'))