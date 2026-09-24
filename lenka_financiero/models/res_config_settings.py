from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    lenka_card_fee_rate = fields.Float(
        string='Comision de tarjeta (%)',
        config_parameter='lenka_financiero.card_fee_rate',
        default=3.5,
        help='Porcentaje retenido por el banco/POS en pagos con tarjeta. El neto despues de esta comision es el monto que se aplica a la deuda del cliente.'
    )


    lenka_passive_interest_tax_rate = fields.Float(
        string='Impuesto / retencion sobre intereses pasivos (%)',
        config_parameter='lenka_financiero.passive_interest_tax_rate',
        default=0.0,
        help='Porcentaje retenido sobre los intereses pagados a inversionistas o depositantes. Se mantiene en 0% mientras no aplique.'
    )
