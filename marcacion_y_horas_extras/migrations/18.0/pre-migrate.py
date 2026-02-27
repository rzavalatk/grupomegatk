from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


MODULE = 'marcacion_y_horas_extras'


def _disable_module_records(env, module_name: str):
	"""Desactiva registros de UI del módulo para que el crawler no los recorra.

	Esto NO elimina datos; solo pone inactive=False donde aplica.
	"""
	imd = env['ir.model.data'].sudo()

	def _deactivate(model_name: str, domain_extra=None):
		domain_extra = domain_extra or []
		recs = env[model_name].sudo().search([('id', 'in', imd.search([
			('module', '=', module_name),
			('model', '=', model_name),
		]).mapped('res_id'))] + domain_extra)
		if not recs:
			return 0
		# Solo modelos con campo active
		if 'active' in recs._fields:
			recs.write({'active': False})
			return len(recs)
		return 0

	counts = {
		'ir.ui.menu': _deactivate('ir.ui.menu'),
		'ir.actions.act_window': _deactivate('ir.actions.act_window'),
		'ir.actions.server': _deactivate('ir.actions.server'),
		'ir.ui.view': _deactivate('ir.ui.view'),
		'ir.rule': _deactivate('ir.rule'),
		'ir.cron': _deactivate('ir.cron'),
		'ir.actions.report': _deactivate('ir.actions.report'),
	}
	_logger.info("%s: desactivados registros UI: %s", module_name, counts)


def migrate(cr, installed_version):
	env = api.Environment(cr, SUPERUSER_ID, {})

	mod = env['ir.module.module'].sudo().search([('name', '=', MODULE)], limit=1)
	if not mod:
		_logger.info("%s: módulo no encontrado, nada que hacer", MODULE)
		return

	if mod.state not in ('installed', 'to upgrade', 'to remove'):
		_logger.info("%s: estado=%s, no se modifica", MODULE, mod.state)
		return

	_logger.warning("%s: marcando para ignorar en upgrade (estado actual=%s)", MODULE, mod.state)

	# 1) Intentar desinstalar el módulo.
	# En upgrades Odoo.sh esto suele funcionar, pero si hay dependencias puede fallar.
	try:
		if mod.state == 'installed':
			mod.button_uninstall()
		else:
			# Si ya está para upgrade/remove, lo dejamos como "to remove".
			mod.write({'state': 'to remove'})
		_logger.warning("%s: desinstalación solicitada (state=%s)", MODULE, mod.state)
		return
	except Exception as exc:
		_logger.warning("%s: no se pudo desinstalar (%s). Se desactivarán menús/acciones/vistas.", MODULE, exc)

	# 2) Fallback: desactivar elementos de UI creados por este módulo.
	_disable_module_records(env, MODULE)

