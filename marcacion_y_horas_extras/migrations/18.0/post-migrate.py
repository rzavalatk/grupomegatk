from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # 1) Asegurar que el usuario Administrador tenga todas las empresas asignadas.
    #    (En upgrades en Odoo.sh el crawler se ejecuta como Administrator id=2)
    admin_user = env.ref('base.user_admin', raise_if_not_found=False)
    if admin_user:
        companies = env['res.company'].search([])
        if companies:
            admin_user.write({'company_ids': [(6, 0, companies.ids)]})
            _logger.info("Admin asignado a %s empresas", len(companies))

    # 2) Corregir inconsistencias multi-compañía en pagos:
    #    Si un payment apunta a un journal de otra compañía, el crawler puede leer el payment
    #    pero fallar al computar campos que acceden al journal por reglas multi-compañía.
    #    Fix: alinear company_id del payment con la company_id del journal.
    #    Esto hace que el payment quede en su compañía real y sea filtrado correctamente.
    try:
        cr.execute(
            """
            UPDATE account_payment p
               SET company_id = j.company_id
              FROM account_journal j
             WHERE p.journal_id = j.id
               AND j.company_id IS NOT NULL
               AND (p.company_id IS NULL OR p.company_id <> j.company_id)
            """
        )
        _logger.info("Actualizados %s pagos con company_id inconsistente", cr.rowcount)
    except Exception as exc:
        _logger.warning("No se pudo normalizar company_id en account_payment: %s", exc)
