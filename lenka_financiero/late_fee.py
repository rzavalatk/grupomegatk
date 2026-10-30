"""Simple monthly arrears on principal, prorated daily on a 30-day basis.

Charge the outstanding balance once per day, assigned to the oldest unpaid
installment. Payment events take effect after that day's accrual. Replaying
the posted history makes refreshes idempotent and preserves earlier accrual.
"""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal


def balance_late_fees(principal, monthly_percent, grace_days, lines, payments, as_of):
    # lines: (id, due_date, capital, interest); payments:
    # (date, capital_including_extra, [(line_id, capital, interest), ...]).
    ordered = sorted(lines, key=lambda line: (line[1], line[0]))
    totals = {line[0]: Decimal('0') for line in ordered}
    if not ordered or not monthly_percent:
        return totals
    dec = lambda value: Decimal(str(value))
    daily_rate = dec(monthly_percent) / Decimal('100') / Decimal('30')
    events = defaultdict(list)
    for date, capital, allocations in payments:
        events[date].append((capital, allocations))
    start = ordered[0][1] + timedelta(days=grace_days + 1)
    balance = dec(principal)
    paid = defaultdict(lambda: Decimal('0'))

    def apply(events_for_day):
        nonlocal balance
        for capital, allocations in events_for_day:
            balance = max(balance - dec(capital), Decimal('0'))
            for line_id, cap, interest in allocations:
                paid[line_id] += dec(cap) + dec(interest)

    for date in sorted(events):
        if date < start:
            apply(events[date])
    day = start
    while day <= as_of:
        if balance > 0:
            for line_id, due, capital, interest in ordered:
                if due + timedelta(days=grace_days) >= day:
                    break
                if dec(capital) + dec(interest) - paid[line_id] > Decimal('0.01'):
                    totals[line_id] += balance * daily_rate
                    break
        apply(events.get(day, []))
        day += timedelta(days=1)
    return totals
