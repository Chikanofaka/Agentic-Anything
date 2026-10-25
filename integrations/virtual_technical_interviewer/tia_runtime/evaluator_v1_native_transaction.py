"""E4D-02C1B0: offline Native transaction *contract* harness, not a Native bridge.

Host-only class; no I/O, network, API keys, SQL, scoring or persisted state.
Actual native integration must separately implement/verify wire compatibility.
"""
from __future__ import annotations

import copy
import re
import secrets
from .evaluator_v1_host_source import (
    compile_host_source, verify_source_still_current,
    review_untrusted_proposal_json, HostSourceError,
)

TX_SCHEMA = 'tia-e4d02c1b0-host-txn/v1'
RECEIPT_SCHEMA = 'tia-e4d02c1b0-offline-receipt/v1'
ID_RE = re.compile(r'[a-z0-9_]{1,80}\Z')
MOCK_TRANSPORT = 'MOCK_HTTP_SIMULATED'


class TransactionError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _reject(code):
    raise TransactionError(code)


class OfflineEvaluatorTransactionHarness:
    """Models Host-owned prepare/commit/cancel/restart without native authority.

    A real provider can never be invoked through this object. Future code must
    implement a separate consent-gated Native protocol; this module cannot
    be switched into a paid mode by choosing other constructor arguments.
    """
    def __init__(self):
        self._pending = None
        self._committed_ids = set()
        self._expired_ids = set()
        self._mock_request_count = 0
        self._audit = []

    def snapshot(self):
        return {
            'schema': TX_SCHEMA,
            'pending': self._pending is not None,
            'mock_requests': self._mock_request_count,
            'actual_provider_requests': 0,
            'last_event': self._audit[-1] if self._audit else 'NONE',
            'native_transport_enabled': False,
            'real_grade': None,
        }

    def prepare_mock(self, plan, journal, question_index, *, consent,
                     scenario='UNKNOWN', transport=MOCK_TRANSPORT):
        if consent is not True:
            _reject('EXPLICIT_MOCK_CONSENT_REQUIRED')
        if transport != MOCK_TRANSPORT:
            _reject('LIVE_NATIVE_TRANSPORT_NOT_IMPLEMENTED')
        if self._pending is not None:
            _reject('EVALUATOR_TRANSACTION_ALREADY_PENDING')
        try:
            source = compile_host_source(plan, journal, question_index, scenario=scenario)
        except HostSourceError as exc:
            _reject('HOST_SOURCE_REJECTED_' + exc.code)
        transaction_id = 'tx_' + secrets.token_hex(12)
        request_id = 'req_' + secrets.token_hex(12)
        generation = 'gen_' + secrets.token_hex(12)
        self._pending = {
            'source': copy.deepcopy(source),
            'transaction_id': transaction_id,
            'request_id': request_id,
            'generation': generation,
        }
        self._audit.append('MOCK_PREPARED')
        return {
            'schema': TX_SCHEMA,
            'role': 'evaluator',
            'transport': MOCK_TRANSPORT,
            'transaction_id': transaction_id,
            'request_id': request_id,
            'generation': generation,
            'source_sha256': source['source_sha256'],
            'question_index': question_index,
            'native_request_authorized': False,
            'paid_consent_granted': False,
            'real_provider_calls': 0,
            'status': 'MOCK_PREPARED_NOT_DISPATCHED',
        }

    def _verify_envelope(self, envelope):
        if type(envelope) is not dict or set(envelope) != {
            'schema', 'role', 'transport', 'transaction_id', 'request_id',
            'generation', 'source_sha256', 'proposal_json'}:
            _reject('INVALID_MOCK_REPLY_ENVELOPE')
        if (envelope['schema'] != RECEIPT_SCHEMA or
                envelope['role'] != 'evaluator' or
                envelope['transport'] != MOCK_TRANSPORT or
                type(envelope['proposal_json']) is not str):
            _reject('INVALID_MOCK_REPLY_ROLE_OR_TRANSPORT')
        if self._pending is None:
            _reject('NO_PENDING_MOCK_TRANSACTION')
        pending = self._pending
        for field in ('transaction_id', 'request_id', 'generation'):
            if type(envelope[field]) is not str or not ID_RE.fullmatch(envelope[field]):
                _reject('INVALID_REPLY_ID')
            if envelope[field] != pending[field]:
                _reject('REPLY_TRANSACTION_MISMATCH')
        if envelope['source_sha256'] != pending['source']['source_sha256']:
            _reject('REPLY_SOURCE_DIGEST_MISMATCH')
        if envelope['transaction_id'] in self._committed_ids or envelope['transaction_id'] in self._expired_ids:
            _reject('REPLY_ALREADY_CONSUMED_OR_EXPIRED')

    def commit_mock(self, plan, journal, envelope):
        self._verify_envelope(envelope)
        pending = self._pending
        try:
            verify_source_still_current(plan, journal, pending['source'])
        except HostSourceError:
            _reject('STALE_HOST_EVIDENCE_AT_COMMIT')
        try:
            review = review_untrusted_proposal_json(plan, journal, pending['source'], envelope['proposal_json'])
        except HostSourceError as exc:
            _reject('INVALID_UNTRUSTED_MODEL_PROPOSAL_' + exc.code)
        self._committed_ids.add(pending['transaction_id'])
        self._pending = None
        self._mock_request_count += 1
        self._audit.append('MOCK_COMMITTED_TO_HUMAN_REVIEW')
        return {
            'schema': TX_SCHEMA,
            'status': 'HUMAN_REVIEW_REQUIRED',
            'review_packet': copy.deepcopy(review),
            'transaction_id': pending['transaction_id'],
            'source_sha256': pending['source']['source_sha256'],
            'transport': MOCK_TRANSPORT,
            'mock_requests': self._mock_request_count,
            'actual_provider_requests': 0,
            'verified_competency_score': None,
            'persisted_in_host_journal': False,
        }

    def cancel_mock(self):
        if self._pending is None:
            _reject('NO_PENDING_MOCK_TRANSACTION')
        self._expired_ids.add(self._pending['transaction_id'])
        self._pending = None
        self._audit.append('MOCK_CANCELLED')
        return {'status': 'CANCELLED', 'actual_provider_requests': 0}

    def simulate_recovery(self):
        """On hypothetical crash/restart never recreate pending or auto-retry."""
        if self._pending is not None:
            self._expired_ids.add(self._pending['transaction_id'])
            self._pending = None
            self._audit.append('MOCK_INTERRUPTED_BY_RECOVERY')
        return {'status': 'NO_AUTO_RETRY', 'actual_provider_requests': 0}
