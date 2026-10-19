"""Curated deterministic returns example. Not a regulatory or actual returns policy."""
def run(x):
    if set(x) != {'condition','proof','days'}:raise ValueError('INVALID_FIELDS: condition,proof,days required')
    if x['condition'] not in ('sealed','opened','damaged') or x['proof'] not in ('yes','no'):
        raise ValueError('INVALID_ENUM')
    if isinstance(x['days'],bool) or not isinstance(x['days'],int) or not 0<=x['days']<=365:
        raise ValueError('INVALID_DAYS')
    result=('MANUAL_REVIEW' if x['proof']=='no' else 'INSPECT' if x['condition']!='sealed' else 'STANDARD_RETURN' if x['days']<=30 else 'OUT_OF_WINDOW')
    return {'classification':result,'rule':'fictional-returns-v1','not_a_real_business_policy':True}
