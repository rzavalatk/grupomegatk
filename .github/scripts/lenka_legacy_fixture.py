"""TEST DATABASE ONLY: reproduce unrelated legacy rows, never production data."""
import json
from odoo import Command

assert env.cr.dbname == 'lenka_legacy_upgrade_test', 'Isolated test database required'
company = env['res.company'].create({'name': 'FICTITIOUS OTHER COMPANY - upgrade preservation'})
local = env(context=dict(env.context, allowed_company_ids=company.ids))
accounts = local['account.account'].create([
    {'name': name, 'code': code, 'account_type': 'asset_current',
     'company_ids': [Command.set(company.ids)]}
    for name, code in [('Legacy test debit', 'TESTLEG01'), ('Legacy test credit', 'TESTLEG02')]
])
journal = local['account.journal'].create({
    'name': 'Fictitious legacy journal', 'code': 'LEG', 'type': 'general',
    'company_id': company.id,
})
moves = local['account.move']
for state in ('posted', 'cancel'):
    move = local['account.move'].create({
        'journal_id': journal.id, 'date': '2024-01-10',
        'ref': 'FICTITIOUS legacy %s - do not copy real records' % state,
        'line_ids': [Command.create({'account_id': accounts[0].id, 'debit': 20}),
                     Command.create({'account_id': accounts[1].id, 'credit': 20})],
    })
    if state == 'posted':
        move.action_post()
    else:
        move.button_cancel()
    moves |= move
partner = local['res.partner'].create({'name': 'FICTITIOUS historical investor'})
investment = local['lenka.investment'].create({
    'partner_id': partner.id, 'company_id': company.id, 'investment_type': 'current',
    'principal_amount': 1000, 'passive_rate': 1, 'rate_period': 'monthly',
    'start_date': '2025-09-20', 'capitalization': 'monthly',
})
investment.action_activate()
interest = local['lenka.investment.interest'].create({
    'investment_id': investment.id, 'period_start_date': '2025-09-20',
    'period_date': '2025-10-20', 'calculation_days': 30, 'base_amount': 1000,
    'rate': 1, 'amount': 10, 'state': 'accrued',
})
env.flush_all()
# Reproduce a constraint ALREADY ABSENT in the legacy fixture, before installing
# the new release. The installer is never allowed to drop or bypass constraints.
env.cr.execute('ALTER TABLE account_move_line DROP CONSTRAINT account_move_line_check_amount_currency_balance_sign')
env.cr.execute('UPDATE account_move_line SET amount_currency = -balance WHERE move_id IN %s', [tuple(moves.ids)])

tables = {'account_move': moves.ids, 'account_move_line': moves.line_ids.ids,
          'res_company': company.ids, 'account_journal': journal.ids,
          'account_account': accounts.ids, 'lenka_investment': investment.ids,
          'lenka_investment_interest': interest.ids}
snapshot = {'tables': {}, 'constraints': None}
for table, ids in tables.items():
    env.cr.execute('SELECT id, to_jsonb(t) FROM %s t WHERE id IN %%s ORDER BY id' % table, [tuple(ids)])
    snapshot['tables'][table] = env.cr.fetchall()
env.cr.execute("""SELECT conname, pg_get_constraintdef(oid), convalidated
                  FROM pg_constraint WHERE conrelid = 'account_move_line'::regclass
                  ORDER BY conname""")
snapshot['constraints'] = env.cr.fetchall()
env['ir.config_parameter'].sudo().set_param('lenka_test_legacy_snapshot', json.dumps(snapshot, default=str))
env.cr.commit()
print('FICTITIOUS LEGACY FIXTURE READY: one posted and one cancelled entry in another company')
