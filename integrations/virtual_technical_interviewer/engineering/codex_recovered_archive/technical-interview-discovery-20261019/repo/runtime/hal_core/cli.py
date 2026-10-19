"""python3 -m hal_core.cli [inspect|preflight|run] ..."""
import argparse,json,sys
from .contracts import inspect,ContractError,parse_json
from .ports import feature_status
from .engine import run

def main():
    p=argparse.ArgumentParser(description='HAL offline curated runtime Sprint 1 — NO model API, NO secrets')
    sub=p.add_subparsers(dest='action',required=True)
    i=sub.add_parser('inspect');i.add_argument('--package',required=True)
    i.add_argument('--normalized',action='store_true',help='Emit hal-domain/v1 manifest only; does not modify package files')
    f=sub.add_parser('preflight');f.add_argument('--package',required=True);f.add_argument('--feature',required=True);f.add_argument('--provider',default=None)
    x=sub.add_parser('run');x.add_argument('--package',required=True);x.add_argument('--feature',required=True);x.add_argument('--payload',required=True,help='JSON object (no credentials)')
    a=p.parse_args()
    try:
        if a.action=='inspect':
            package=inspect(a.package)
            out=package.contract if a.normalized else package.public()
        elif a.action=='preflight':out=feature_status(inspect(a.package),a.feature,a.provider)
        else:out=run(a.package,a.feature,parse_json(a.payload))
    except ContractError as e:out={'status':'ERROR','reason':str(e)}
    print(json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False))
    return 0 if out.get('status') not in ('BLOCKED','ERROR') else 2

if __name__=='__main__':sys.exit(main())
