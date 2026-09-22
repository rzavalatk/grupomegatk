def _split_name(value):
    parts = (value or "").strip().split()
    if not parts:
        return (None, None, None, None)
    if len(parts) == 1:
        return (parts[0], None, None, None)
    if len(parts) == 2:
        return (parts[0], None, parts[1], None)
    if len(parts) == 3:
        return (parts[0], None, parts[1], parts[2])
    return (parts[0], " ".join(parts[1:-2]), parts[-2], parts[-1])


def migrate(cr, version):
    """Conserva los profesionales existentes al separar nombres y apellidos."""
    cr.execute(
        """
        SELECT id, name
          FROM odental_professional
         WHERE first_name IS NULL
            OR first_surname IS NULL
        """
    )
    for professional_id, name in cr.fetchall():
        first_name, middle_name, first_surname, second_surname = _split_name(name)
        cr.execute(
            """
            UPDATE odental_professional
               SET first_name = COALESCE(first_name, %s),
                   middle_name = COALESCE(middle_name, %s),
                   first_surname = COALESCE(first_surname, %s),
                   second_surname = COALESCE(second_surname, %s),
                   professional_code = COALESCE(
                       professional_code,
                       'PRO-' || LPAD(id::text, 6, '0')
                   )
             WHERE id = %s
            """,
            (
                first_name,
                middle_name,
                first_surname,
                second_surname,
                professional_id,
            ),
        )
