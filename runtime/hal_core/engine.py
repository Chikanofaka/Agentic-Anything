"""Curated local typed dispatch: no arbitrary package code or external network APIs."""
from __future__ import annotations
import importlib, json, time, uuid
from .contracts import inspect, ContractError
from .ports import feature_status
from .registry import TRUSTED

DENIED_INPUT_KEYS = {'api_key','apikey','key','token','password','secret','credential','authorization'}

def run(package_path, feature, payload, *, max_tool_calls=1):
    started=time.monotonic()
    receipt={'run_id':str(uuid.uuid4()),'kind':'DETERMINISTIC_OFFLINE', 'feature':feature,
             'status':'BLOCKED', 'events':[], 'live_model_used':False,'external_writes':False}
    def evt(code): receipt['events'].append({'code':code})
    try:
        p=inspect(package_path);receipt['domain_id']=p.manifest['id'];receipt['package_digest']=p.digest
        evt('PACKAGE_INSPECTED')
        if max_tool_calls<1 or max_tool_calls>1:raise ContractError('TOOL_BUDGET_INVALID')
        if not isinstance(payload,dict) or any(str(x).lower() in DENIED_INPUT_KEYS for x in payload):
            raise ContractError('SECRET_LIKE_OR_INVALID_PAYLOAD')
        registry=TRUSTED.get((p.manifest['id'],feature))
        if registry is None:raise ContractError('NOT_IN_TRUSTED_REGISTRY')
        status=feature_status(p,feature)
        if status['status']!='AVAILABLE_CURATED_LOCAL':
            raise ContractError('FEATURE_PORT_NOT_AVAILABLE')
        declared=next(x for x in p.manifest['features'] if x['id']==feature)
        if declared['required_ports'] != [registry[0]]:raise ContractError('REQUIRED_PORTS_MISMATCH')
        evt('FEATURE_RESOLVED')
        # Import is hardcoded from this source tree, never from package path/manifest.
        tool=getattr(importlib.import_module(registry[1]),registry[2]);result=tool(payload)
        evt('TRUSTED_TOOL_EXECUTED')
        receipt['result']=result;receipt['status']='SUCCESS'
    except (ContractError,ValueError,KeyError,TypeError) as e:
        receipt['status']='BLOCKED';receipt['reason']=str(e);evt('EXECUTION_BLOCKED')
    receipt['elapsed_ms']=round((time.monotonic()-started)*1000,2)
    return receipt
