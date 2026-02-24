from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Pre-migrate account_invoice_line_report: protegiendo producto 5410")

    product_id = 5410
    Imd = env['ir.model.data'].sudo()

    # Buscar cualquier xmlid que apunte a ese producto (product.product o product.template)
    imd_records = Imd.search([
        ('model', 'in', ['product.product', 'product.template']),
        ('res_id', '=', product_id),
    ])

    if imd_records:
        count = len(imd_records)
        imd_records.unlink()
        _logger.info(
            "Eliminados %s registros ir.model.data para el producto id %s; "
            "se evita su borrado automático en la migración.",
            count, product_id
        )
    else:
        _logger.info("No se encontraron registros ir.model.data para el producto id %s", product_id)

    # Proteger las reglas salariales con ids 8 y 9 para evitar su borrado
    for salary_rule_id in (8, 9, 7, 6, 5, 4, 3, 2, 1):
        _logger.info(
            "Pre-migrate account_invoice_line_report: protegiendo hr.salary.rule %s",
            salary_rule_id,
        )

        imd_salary_rule = Imd.search([
            ('model', '=', 'hr.salary.rule'),
            ('res_id', '=', salary_rule_id),
        ])

        if imd_salary_rule:
            count = len(imd_salary_rule)
            imd_salary_rule.unlink()
            _logger.info(
                "Eliminados %s registros ir.model.data para hr.salary.rule id %s; "
                "se evita su borrado automático en la migració n.",
                count, salary_rule_id
            )
        else:
            _logger.info(
                "No se encontraron registros ir.model.data para hr.salary.rule id %s",
                salary_rule_id,
            )

    # Ignorar módulos que ya no se van a usar
    modules_to_ignore = [
        'gps_visitas',
        'hr_payroll_account_community',
        'ohrms_core',
        'planilla_y_metas',
        'prestamos_financieros',
        'whatsapp_mail_messaging',
    ]

    Module = env['ir.module.module'].sudo()
    modules = Module.search([('name', 'in', modules_to_ignore)])
    if modules:
        _logger.info(
            "Marcando módulos como desinstalados/ignorados en migración: %s",
            modules.mapped('name'),
        )
        modules.write({'state': 'uninstalled'})
    else:
        _logger.info("No se encontraron módulos para ignorar: %s", modules_to_ignore)


