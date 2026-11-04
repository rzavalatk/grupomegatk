"""Isolated CI only: simultaneous RPC-like transactions must not duplicate money."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier

from psycopg2.errors import SerializationFailure
from odoo import api, SUPERUSER_ID

assert env.cr.dbname == 'lenka_refinance_test', 'Isolated test database required'
company = env['res.company'].create({'name': 'FICTITIOUS concurrent Lenka account'})
local = env(context=dict(env.context, allowed_company_ids=company.ids))
partner = local['res.partner'].create({'name': 'FICTITIOUS concurrent investor'})
bank, liability = local['account.account'].create([
    {'name': 'FICTITIOUS ' + name, 'code': code, 'account_type': kind,
     'company_ids': [(6, 0, company.ids)]}
    for name, code, kind in [('bank', 'LCON01', 'asset_cash'), ('obligation', 'LCON02', 'liability_current')]
])
journal = local['account.journal'].create({
    'name': 'FICTITIOUS concurrency bank', 'code': 'LCON', 'type': 'bank',
    'company_id': company.id, 'default_account_id': bank.id,
})
company.lenka_investor_liability_account_id = liability
investment = local['lenka.investment'].create({
    'partner_id': partner.id, 'company_id': company.id, 'investment_type': 'current',
    'principal_amount': 100000, 'passive_rate': 1.5, 'rate_period': 'monthly',
    'start_date': '2025-09-20', 'capitalization': 'monthly',
})
investment.action_activate()
env.cr.commit()  # Only the explicitly guarded fictitious CI database.
registry = env.registry
company_id, investment_id = company.id, investment.id


def run_twice(model_name, record_id, operation):
    barrier = Barrier(2)

    def worker():
        for attempt in range(4):
            try:
                with registry.cursor() as cr:
                    cr.execute("SET LOCAL lock_timeout = '15s'")
                    worker_env = api.Environment(cr, SUPERUSER_ID, {'allowed_company_ids': [company_id]})
                    record = worker_env[model_name].browse(record_id)
                    record.read(['state'])  # Both transactions acquire a snapshot first.
                    if not attempt:
                        barrier.wait(timeout=20)
                    operation(record)
                    cr.commit()
                return attempt
            except SerializationFailure:
                if attempt == 3:
                    raise

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: worker(), range(2)))
    assert sum(results) >= 1, 'Expected an RPC serialization retry for the competing snapshot'


run_twice('lenka.investment', investment_id,
          lambda rec: rec._generate_interest_until(date(2025, 10, 31), 1.5))
env.cr.rollback()  # Refresh the reader snapshot after the independent commits.
env.invalidate_all()
investment = local['lenka.investment'].browse(investment_id)
assert len(investment.interest_line_ids) == 2
assert investment.interest_line_ids.sorted('period_date').mapped('amount') == [550, 1508.25]
deposit = local['lenka.investment.deposit'].create({
    'investment_id': investment_id, 'date': '2025-11-01', 'amount': 1000,
    'journal_id': journal.id, 'reference': 'FICTITIOUS-CONCURRENT-ONE-RECEIPT',
})
deposit_id = deposit.id
env.cr.commit()
run_twice('lenka.investment.deposit', deposit_id, lambda rec: rec.action_post())
env.cr.rollback()
env.invalidate_all()
deposit = local['lenka.investment.deposit'].browse(deposit_id)
assert deposit.state == 'posted' and deposit.move_id.state == 'draft'
assert len(deposit.move_id.line_ids) == 2
assert local['account.move'].search_count([('ref', '=', deposit.move_id.ref)]) == 1
assert investment.outstanding_principal == 101000
print('PASS: concurrent month-end generation creates two periods once; concurrent deposit confirmation creates one receipt; serialization retries preserve balances')
env.cr.rollback()
