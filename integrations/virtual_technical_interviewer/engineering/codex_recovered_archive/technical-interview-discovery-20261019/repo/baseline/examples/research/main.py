import argparse
p=argparse.ArgumentParser(description='Deterministic demo margin calculation')
p.add_argument('--revenue',required=True,type=float)
p.add_argument('--cost',required=True,type=float)
a=p.parse_args()
if a.revenue<=0 or a.cost<0: p.error('revenue must be > 0 and cost must be >= 0')
print(f'profit: {a.revenue-a.cost:.2f}')
print(f'margin: {(a.revenue-a.cost)/a.revenue*100:.2f}%')
