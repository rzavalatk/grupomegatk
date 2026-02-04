from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def _reactivate_rules(env, model_name):
    """Reactiva las reglas de registro multiempresa para un modelo."""
    try:
        model = env['ir.model'].search([('model', '=', model_name)], limit=1)
        if not model:
            return
        
        # Buscar reglas desactivadas para este modelo
        rules = env['ir.rule'].search([
            ('model_id', '=', model.id),
            ('active', '=', False),
            '|', ('domain_force', 'ilike', 'company_id'),
                 ('domain_force', 'ilike', 'company_ids')
        ])
        
        if rules:
            rules.write({'active': True})
            _logger.info(f"Reactivadas {len(rules)} reglas multiempresa para {model_name}")
    except Exception as e:
        _logger.error(f"Error al reactivar reglas para {model_name}: {e}")


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    _logger.info("="*80)
    _logger.info("Iniciando post-migración a Odoo 18.0")
    _logger.info("="*80)

    # Lista de modelos que fueron modificados en pre-migrate
    problematic_models = [
        'account.journal',
        'account.payment.method.line',
        'hr.employee.markings',
        'hr.employee',
    ]
    
    # Reactivar reglas multiempresa
    _logger.info("Reactivando reglas multiempresa...")
    for model_name in problematic_models:
        _reactivate_rules(env, model_name)
    
    _logger.info("="*80)
    _logger.info("Post-migración completada")
    _logger.info("="*80)
