"""python3 -m hal_core.cli [inspect|preflight|run] ..."""
import argparse,json,sys
from .contracts import inspect,ContractError
from .ports import feature_status
from .engine import run

def main():
    p=argparse.ArgumentParser(description='HAL offline curated runtime v0.0.1 — NO model API, NO secrets')
    sub=p.add_subparsers(dest='action',required=True)
    i=sub.add_parser('inspect');i.add_argument('--package',required=True)
    f=sub.add_parser('preflight');f.add_argument('--package',required=True);f.add_argument('--feature',required=True);f.add_argument('--provider',default=None)
    x=sub.add_parser('run');x.add_argument('--package',required=True);x.add_argument('--feature',required=True);x.add_argument('--payload',required=True,help='JSON object (no credentials)')
    a=p.parse_args()
    try:
        if a.action=='inspect':out=inspect(a.package).public()
        elif a.action=='preflight':out=feature_status(inspect(a.package),a.feature,a.provider)
        else:out=run(a.package,a.feature,json.loads(a.payload))
    except (ContractError,ValueError) as e:out={'status':'ERROR','reason':str(e)}
    print(json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True))
    return 0 if out.get('status') not in ('BLOCKED','ERROR') else 2

if __name__=='__main__':sys.exit(main())
