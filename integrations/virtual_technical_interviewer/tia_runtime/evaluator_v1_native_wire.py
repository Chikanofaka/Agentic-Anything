"""E4D-02C1B1A Native Swift loopback wire -> Host transaction adapter.

Additive developer-only module. Its wire payload contains NO candidate content,
credentials or provider endpoint. Swift's structural check does not grant any
Host authority: Host commit_mock re-checks the complete frozen source + model
proposal's 12 dimensions. No real HTTP outside localhost may be sent.
"""
from __future__ import annotations

import json
import re
from .evaluator_v1_native_transaction import (
    RECEIPT_SCHEMA, MOCK_TRANSPORT, OfflineEvaluatorTransactionHarness,
)
from .evaluator_v1_semantic_contract import strict_load

REQUEST_SCHEMA = "tia-e4d02c1b1a-mock-wire-request/v1"
RESPONSE_SCHEMA = "tia-e4d02c1b1a-mock-wire-response/v1"
WIRE_TRANSPORT = "LOCAL_LOOPBACK_MOCK_HTTP"
IDS = re.compile(r"[a-z0-9_]{1,80}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")

class WireError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code

def _reject(code):
    raise WireError(code)

def wire_request(ticket):
    if type(ticket) is not dict or set(ticket) != {
        'schema', 'role', 'transport', 'transaction_id', 'request_id',
        'generation', 'source_sha256', 'question_index', 'native_request_authorized',
        'paid_consent_granted', 'real_provider_calls', 'status',
    }:
        _reject('INVALID_PREPARED_TICKET')
    if (ticket['role'] != 'evaluator' or ticket['transport'] != MOCK_TRANSPORT
            or ticket['status'] != 'MOCK_PREPARED_NOT_DISPATCHED'
            or ticket['native_request_authorized'] is not False
            or ticket['paid_consent_granted'] is not False
            or type(ticket['real_provider_calls']) is not int or ticket['real_provider_calls'] != 0
            or type(ticket['question_index']) is not int or ticket['question_index'] not in (0,1,2)):
        _reject('NOT_OFFLINE_MOCK_PREPARED')
    for key in ('transaction_id','request_id','generation'):
        if type(ticket[key]) is not str or not IDS.fullmatch(ticket[key]):
            _reject('INVALID_TICKET_ID')
    if type(ticket['source_sha256']) is not str or not SHA.fullmatch(ticket['source_sha256']):
        _reject('INVALID_SOURCE_DIGEST')
    return { 'schema': REQUEST_SCHEMA, 'role': 'evaluator', 'transport': WIRE_TRANSPORT,
             **{key:ticket[key] for key in ('transaction_id','request_id','generation','source_sha256')} }

def mock_wire_response(ticket, proposal_json):
    """Server-side deterministic test fixture ONLY, never generated inside TIA App."""
    request = wire_request(ticket)
    if type(proposal_json) is not str or not 0 < len(proposal_json.encode('utf-8')) <= 32768:
        _reject('INVALID_PROPOSAL_BYTES')
    return {'schema': RESPONSE_SCHEMA, **{k:v for k,v in request.items() if k != 'schema'},
            'proposal_json': proposal_json}

def wire_to_host_envelope(ticket, response_json):
    """Strictly re-check Native output; remains untrusted until Host commit_mock."""
    if type(response_json) is not str or len(response_json.encode('utf-8')) > 65536:
        _reject('WIRE_REPLY_TOO_LARGE')
    try:
        response = strict_load(response_json)
    except (ValueError, TypeError) as exc:
        _reject('INVALID_WIRE_REPLY_JSON')
    if type(response) is not dict or set(response) != {
        'schema','role','transport','transaction_id','request_id','generation',
        'source_sha256','proposal_json'}:
        _reject('WIRE_REPLY_FIELDS_INVALID')
    request = wire_request(ticket)
    if response.pop('schema') != RESPONSE_SCHEMA:
        _reject('WIRE_SCHEMA_MISMATCH')
    for key, value in request.items():
        if key != 'schema' and response.get(key) != value:
            _reject('WIRE_TICKET_MISMATCH')
    raw = response['proposal_json']
    if type(raw) is not str or not 0 < len(raw.encode('utf-8')) <= 32768:
        _reject('WIRE_PROPOSAL_INVALID')
    # Strict JSON must be parsed again by trusted Host commit.
    return {'schema': RECEIPT_SCHEMA, 'role': 'evaluator', 'transport': MOCK_TRANSPORT,
            **{key: ticket[key] for key in ('transaction_id','request_id','generation','source_sha256')},
            'proposal_json': raw}

def commit_from_native_wire(harness, plan, journal, ticket, response_json):
    if not isinstance(harness, OfflineEvaluatorTransactionHarness):
        _reject('HOST_HARNESS_REQUIRED')
    return harness.commit_mock(plan, journal, wire_to_host_envelope(ticket, response_json))
