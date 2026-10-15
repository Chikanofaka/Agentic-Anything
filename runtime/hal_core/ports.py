"""Port resolution is capability evidence, never a fabricated live model healthcheck."""
from __future__ import annotations
from .contracts import Inspection
from .registry import TRUSTED
LOCAL_PORTS={'LOCAL_CALCULATE','LOCAL_TRIAGE'}
DIRECT_MODELS={'openai','anthropic','deepseek','qwen'}
MANAGED_AGENTS={'manus','workbuddy'}

def feature_status(pkg: Inspection, feature_id: str, provider: str|None=None):
    f=next((x for x in pkg.manifest['features'] if x['id']==feature_id),None)
    if f is None:return {'status':'BLOCKED','reason':'UNKNOWN_FEATURE', 'missing_ports':[]}
    missing=[]; checks=[]
    for port in f['required_ports']:
        if port in LOCAL_PORTS:
            r=TRUSTED.get((pkg.manifest['id'],feature_id))
            if r is None or r[0]!=port or f['required_ports'] != [port]:
                missing.append(port+':NO_CURATED_BINDING')
            else:
                checks.append({'port':port,'state':'AVAILABLE_CURATED_LOCAL'})
        elif port=='LLM_DIRECT':
            if not provider: missing.append(port+':NO_PROVIDER')
            elif provider in MANAGED_AGENTS:missing.append('MANAGED_AGENT_PORT_MISMATCH')
            elif provider in DIRECT_MODELS:missing.append('LLM_DIRECT:UNVERIFIED_LIVE_CREDENTIALS_AND_CAPABILITIES')
            else: missing.append(port+':UNSUPPORTED_PROVIDER')
        else: missing.append(port+':NO_REGISTERED_ADAPTER')
    return {'status': 'AVAILABLE_CURATED_LOCAL' if not missing else 'BLOCKED',
            'missing_ports':missing,'checks':checks,'provider':provider,
            'live_model_verified':False}
