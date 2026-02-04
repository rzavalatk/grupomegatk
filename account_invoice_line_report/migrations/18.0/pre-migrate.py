from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def _ensure_admin_group_has_model_access(env, model_name, perms=('read',)):
    """Garantiza que el grupo de administradores tenga ciertos permisos sobre un modelo."""
    try:
        group_admin = env.ref('base.group_system', raise_if_not_found=False)
        if not group_admin:
            _logger.warning(f"No se encontró el grupo base.group_system")
            return

        model = env['ir.model'].search([('model', '=', model_name)], limit=1)
        if not model:
            _logger.warning(f"No se encontró el modelo {model_name}")
            return

        access_obj = env['ir.model.access']
        access = access_obj.search([
            ('model_id', '=', model.id),
            ('group_id', '=', group_admin.id),
        ], limit=1)

        vals = {
            'name': f'access_{model_name.replace(".", "_")}_admin_upgrade',
            'model_id': model.id,
            'group_id': group_admin.id,
            'perm_read': 'read' in perms,
            'perm_write': 'write' in perms,
            'perm_create': 'create' in perms,
            'perm_unlink': 'unlink' in perms,
        }

        if access:
            # Fusionar permisos (no quitar nada que ya exista)
            for p in ('perm_read', 'perm_write', 'perm_create', 'perm_unlink'):
                vals[p] = getattr(access, p) or vals[p]
            access.write(vals)
            _logger.info(f"Actualizado acceso para {model_name}: {vals['name']}")
        else:
            access_obj.create(vals)
            _logger.info(f"Creado acceso para {model_name}: {vals['name']}")
    except Exception as e:
        _logger.error(f"Error al crear permisos para {model_name}: {e}")


def _disable_multicompany_rules(env, model_name):
    """Desactiva temporalmente las reglas de registro multiempresa para un modelo."""
    try:
        model = env['ir.model'].search([('model', '=', model_name)], limit=1)
        if not model:
            return
        
        # Buscar reglas multiempresa activas para este modelo
        rules = env['ir.rule'].search([
            ('model_id', '=', model.id),
            ('active', '=', True),
            '|', ('domain_force', 'ilike', 'company_id'),
                 ('domain_force', 'ilike', 'company_ids')
        ])
        
        if rules:
            rules.write({'active': False})
            _logger.info(f"Desactivadas {len(rules)} reglas multiempresa para {model_name}")
            return rules.ids
        return []
    except Exception as e:
        _logger.error(f"Error al desactivar reglas para {model_name}: {e}")
        return []


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    _logger.info("="*80)
    _logger.info("Iniciando pre-migración a Odoo 18.0")
    _logger.info("="*80)

    # 1) Desinstalar módulos problemáticos
    modules_to_deactivate = ['web_notify', 'payment_term_custom', 'marcacion_y_horas_extras']
    module_obj = env['ir.module.module']
    modules = module_obj.search([('name', 'in', modules_to_deactivate)])
    if modules:
        modules.write({'state': 'uninstalled'})
        _logger.info(f"Desactivados módulos: {modules_to_deactivate}")

    # 2) Lista de modelos problemáticos
    problematic_models = [
        'account.journal',
        'account.payment.method.line',
        'hr.employee.markings',
        'hr.employee',
    ]
    
    # 3) Desactivar reglas multiempresa temporalmente
    _logger.info("Desactivando reglas multiempresa...")
    disabled_rules = {}
    for model_name in problematic_models:
        rule_ids = _disable_multicompany_rules(env, model_name)
        if rule_ids:
            disabled_rules[model_name] = rule_ids
    
    # 4) Crear permisos completos para el grupo de administradores
    _logger.info("Creando permisos de acceso completos...")
    for model_name in problematic_models:
        _ensure_admin_group_has_model_access(
            env, 
            model_name, 
            perms=('read', 'write', 'create', 'unlink')
        )
    
    # 5) Asegurar que el usuario admin tenga acceso a todas las empresas
    try:
        admin_user = env.ref('base.user_admin')
        all_companies = env['res.company'].search([])
        if all_companies:
            admin_user.write({'company_ids': [(6, 0, all_companies.ids)]})
            _logger.info(f"Usuario admin asignado a {len(all_companies)} empresas")
    except Exception as e:
        _logger.error(f"Error al asignar empresas al admin: {e}")
    
    _logger.info("="*80)
    _logger.info("Pre-migración completada")
    _logger.info("="*80)