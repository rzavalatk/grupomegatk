from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bac_registered_only_payment = fields.Boolean(
        string='Requerir usuario registrado para pagar',
        config_parameter='bac_payment_control.registered_only_payment',
        default=True,
        help='Cuando esta activo, los pedidos con productos BAC solo pueden pagar si el cliente inicio sesion.',
    )
    bac_auto_prepare_checkout = fields.Boolean(
        string='Preparar controles BAC al entrar a pago',
        config_parameter='bac_payment_control.auto_prepare_checkout',
        default=True,
        help='Genera o actualiza los controles BAC automaticamente cuando el cliente entra a la pantalla de pago. La validacion del pago sigue siendo manual por un empleado autorizado.',
    )