import logging

from odoo import _, api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        """ Find the transaction based on the feedback data.

        For an acquirer to handle transaction post-processing, it must overwrite this method and
        return the transaction matching the data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The feedback data sent by the acquirer
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        """
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'pixel':
            return tx
        reference = data.get('reference')
        tx = self.search([('reference', '=', reference), ('provider', '=', 'pixel')])
        if not tx:
            raise ValidationError(
                "Test: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_feedback_data(self, data):
        """ Override of payment to process the transaction based on Authorize data.

        Note: self.ensure_one()

        :param dict data: The feedback data sent by the provider
        :return: None
        """
        super()._process_feedback_data(data)
        if self.provider != 'pixel':
            return

        response_content = data.get('payment_transaction')

        self.acquirer_reference = response_content.get('transaction_id')
        status_code = data.get('success')
        if status_code:  # Approved
            self._set_done()
            self.token_id = data.get('token_id')
            self.state_message = data.get('message')
        else:
            error = data.get('errors')
            if error:
                error_code = response_content.get('x_response_reason_text')
                _logger.info(
                    "received data with invalid status code %s and error code %s",
                    status_code, error_code
                )
                self._set_error(
                    "Authorize.Net: " + _(
                        "Received data with status code \"%(status)s\" and error code \"%(error)s\"",
                        status=status_code, error=error_code
                    )
                )
            else:
                self._set_canceled()
                self.token_id = data.get('token_id')
                self.state_message = data.get('message')

    # def _set_pending(self, state_message=None):
    #     """ Update the transactions' state to 'pending'.
    #
    #     :param str state_message: The reason for which the transaction is set in 'pending' state
    #     :return: None
    #     """
    #     allowed_states = ('draft',)
    #     target_state = 'pending'
    #     txs_to_process = self._update_state(allowed_states, target_state, state_message)
    #     txs_to_process._log_received_message()