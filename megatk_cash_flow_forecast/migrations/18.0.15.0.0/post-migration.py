def migrate(cr, version):
    """Preserve the document scope of management notes created before v15."""
    cr.execute(
        """
        UPDATE cashflow_management_note
           SET scope = CASE
               WHEN move_id IS NOT NULL THEN 'document'
               ELSE 'general'
           END
        """
    )
