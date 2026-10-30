def migrate(cr, version):
    """Restore only manual projections cancelled by the former automatic rule."""
    cr.execute(
        """
        UPDATE cashflow_promise AS promise
           SET state = 'active',
               write_date = NOW()
         WHERE promise.state = 'cancelled'
           AND promise.source_move_id IS NULL
           AND promise.source_move_line_id IS NULL
           AND EXISTS (
               SELECT 1
                 FROM mail_message AS message
                WHERE message.model = 'cashflow.promise'
                  AND message.res_id = promise.id
                  AND message.body ILIKE
                      '%%Odoo ya no muestra una deuda abierta para este contacto%%'
                  AND ABS(EXTRACT(EPOCH FROM (promise.write_date - message.date))) <= 300
           )
        """
    )
