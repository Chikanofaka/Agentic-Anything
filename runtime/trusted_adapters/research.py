"""Explicitly curated deterministic specialist adapter; no network or file access."""
import math

def run(x):
    if set(x) != {'revenue','cost'}: raise ValueError('INVALID_FIELDS: revenue,cost required')
    if any(isinstance(x[k],bool) or not isinstance(x[k],(int,float)) or not math.isfinite(x[k]) for k in x):
        raise ValueError('NON_FINITE_OR_NON_NUMERIC_AMOUNT')
    revenue=float(x['revenue']);cost=float(x['cost'])
    if revenue<=0 or cost<0:raise ValueError('INVALID_AMOUNT_RANGE')
    return {'profit':round(revenue-cost,2),'margin_pct':round((revenue-cost)/revenue*100,2),'unit':'user_supplied_units','rule':'margin-v1'}
