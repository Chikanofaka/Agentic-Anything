import argparse
p=argparse.ArgumentParser(description='Deterministic demo returns triage')
p.add_argument('--condition',required=True,choices=['sealed','opened','damaged'])
p.add_argument('--proof',required=True,choices=['yes','no'])
p.add_argument('--days',required=True,type=int)
a=p.parse_args()
if not 0<=a.days<=365: p.error('days must be between 0 and 365')
result=('MANUAL_REVIEW' if a.proof=='no' else 'INSPECT' if a.condition!='sealed' else 'STANDARD_RETURN' if a.days<=30 else 'OUT_OF_WINDOW')
print(result)
