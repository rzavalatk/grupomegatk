"""TEST DATABASE ONLY: assert that installation preserves other-company rows."""
import json
assert env.cr.dbname == 'lenka_legacy_upgrade_test', 'Isolated test database required'
snapshot = json.loads(env['ir.config_parameter'].sudo().get_param('lenka_test_legacy_snapshot'))
for table, rows in snapshot['tables'].items():
    ids = tuple(row[0] for row in rows)
    env.cr.execute('SELECT id, to_jsonb(t) FROM %s t WHERE id IN %%s ORDER BY id' % table, [ids])
    actual = json.loads(json.dumps(env.cr.fetchall(), default=str))
    assert actual == rows, 'Installer changed historical records in %s' % table
env.cr.execute("""SELECT conname, pg_get_constraintdef(oid), convalidated
                  FROM pg_constraint WHERE conrelid = 'account_move_line'::regclass
                  ORDER BY conname""")
assert json.loads(json.dumps(env.cr.fetchall())) == snapshot['constraints'], 'Installer changed shared accounting constraints'
modules = env['ir.module.module'].search([('name', 'in', ['lenka_financiero', 'lenka_banks'])])
assert all(m.state == 'installed' for m in modules) and len(modules) == 2
assert {m.name: m.installed_version for m in modules} == {
    'lenka_financiero': '18.0.1.0.13', 'lenka_banks': '18.0.1.0.1'}
from odoo.addons.lenka_financiero.models.accounting_guard import _has_guard
for method in ('create', 'write', 'unlink'):
    assert _has_guard(getattr(type(env['account.move.line']), method)), 'Missing runtime protection: %s' % method
print('PASS: both modules installed; every historical row and accounting constraint unchanged; guards active after restart')
env.cr.rollback()
