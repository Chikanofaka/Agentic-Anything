"""Host-owned interview lifecycle. Model replies are data, never commands.

Uses HAL's reviewed-host pattern without changing the Witness-specific controller
or registering executable targets from an imported package. This first slice is
in-memory and text-only; SQL execution, grading and persistence are not provided.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from .contracts import load_roles
from .provider import ModelRequest, ModelPortal, ModelPortalError, build_portal


class SessionError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class SessionConfig:
    session_id: str = 'demo-001'
    duration_seconds: float = 300
    max_events: int = 128
    max_input_bytes: int = 8192

    def __post_init__(self):
        if not isinstance(self.session_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', self.session_id):
            raise SessionError('INVALID_SESSION_CONFIG')
        if (type(self.duration_seconds) not in (int, float) or
                not 0 < self.duration_seconds <= 86400):
            raise SessionError('INVALID_SESSION_CONFIG')
        if type(self.max_events) is not int or not 16 <= self.max_events <= 4096:
            raise SessionError('INVALID_SESSION_CONFIG')
        if type(self.max_input_bytes) is not int or not 1 <= self.max_input_bytes <= 65536:
            raise SessionError('INVALID_SESSION_CONFIG')


class InterviewController:
    """One trusted local controller per session, with serialized operations.

    Public methods are host entrypoints, not an authenticated multi-user API.
    Returned snapshots are copies. A reviewed receipt is immutable by contract;
    its digest detects change, and is not a digital signature or anti-cheat seal.
    """

    ACTIONS = frozenset({'clarify', 'plan', 'implement', 'test', 'help', 'conclude'})

    def __init__(self, config=None, portal=None, roles=None, clock=None):
        self.config = config or SessionConfig()
        if not isinstance(self.config, SessionConfig):
            raise SessionError('INVALID_SESSION_CONFIG')
        self._portal = portal or build_portal()
        if not isinstance(self._portal, ModelPortal):
            raise SessionError('INVALID_PORTAL')
        self._roles = roles or load_roles(Path(__file__).resolve().parents[1])
        if set(self._roles) != {'interviewer', 'trainer'}:
            raise SessionError('INVALID_ROLES')
        self._clock = clock or time.monotonic
        self._phase = 'NEW'
        self._events = []
        self._closed_receipt = None
        self._started = None
        self._question = None
        self._review = None
        self._busy = False
        # Native provider transactions are a separate, explicitly opted-in path.
        # The original ModelPortal continues to accept SIMULATED responses only.
        self._native_preview = False
        self._native_pending = None

    @property
    def phase(self):
        return self._phase

    @property
    def receipt(self):
        return copy.deepcopy(self._closed_receipt)

    def snapshot(self):
        return {'session_id': self.config.session_id, 'phase': self.phase,
                'events': copy.deepcopy(self._events), 'receipt': self.receipt,
                'review': copy.deepcopy(self._review),
                'mode': 'LIVE_CONVERSATIONAL_PREVIEW' if self._native_preview else 'OFFLINE_MOCK',
                'sql_evaluator': 'NOT_IMPLEMENTED', 'scoring': 'NOT_IMPLEMENTED'}

    @property
    def native_pending(self):
        return copy.deepcopy(self._native_pending)

    def start_native_preview(self, question, profile):
        """Native host-only entrypoint; starting a session makes no model call."""
        self._available()
        if self.phase != 'NEW' or profile.get('role') != 'interviewer':
            raise SessionError('INVALID_TRANSITION')
        if type(question) is not str or not question.strip():
            raise SessionError('INVALID_INPUT')
        try:
            if len(question.encode('utf-8')) > 16384:
                raise SessionError('QUESTION_TOO_LARGE')
        except UnicodeError:
            raise SessionError('INVALID_INPUT') from None
        self._native_preview = True
        self._started = self._clock()
        self._question = question
        self._phase = 'INTERVIEWING'
        return self._append('host', 'session_started', {
            'question': question, 'duration_seconds': self.config.duration_seconds,
            'role_versions': {k: v.version for k, v in self._roles.items()},
            'mode': 'LIVE_CONVERSATIONAL_PREVIEW', 'model_controls_scores': False,
            'execution_status': 'NOT_RUN', 'prompt_sha256': profile['sha256'],
            'source_sha256': profile['source_sha256'],
            'mechanism': profile['mechanism'],
            'scope': 'One candidate turn; conversational preview, not a technical interview',
        })

    def prepare_native_reply(self, request_id, generation, operation, profile, policy):
        """Issue an expiring, single-use commitment bound to current evidence.

        Only the native worker transport calls this method. It never receives a
        credential and does not perform I/O. The Swift bridge does not expose it.
        """
        self._active()
        if (not self._native_preview or self._native_pending is not None
                or operation not in ('verify', 'reply')
                or self.phase not in self._roles['interviewer'].active_states):
            raise SessionError('NATIVE_REQUEST_NOT_ALLOWED')
        for value in (request_id, generation):
            if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', value):
                raise SessionError('INVALID_NATIVE_REQUEST')
        binding = {'session_id': self.config.session_id, 'request_id': request_id,
                   'generation': generation, 'operation': operation,
                   'revision': len(self._events), 'phase': self.phase,
                   'prompt_sha256': profile['sha256']}
        transaction_id = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
        if any(event['payload'].get('transaction_id') == transaction_id for event in self._events):
            raise SessionError('NATIVE_REQUEST_REUSED')
        self._native_pending = dict(binding, transaction_id=transaction_id,
                                    source_sha256=copy.deepcopy(profile['source_sha256']),
                                    policy=copy.deepcopy(policy))
        return copy.deepcopy(self._native_pending)

    def commit_native_reply(self, transaction_id, request_id, generation, reply, model, usage):
        from .native_contract import validate_commit

        validate_commit({'transaction_id': transaction_id, 'request_id': request_id,
                         'generation': generation, 'reply': reply, 'model': model, 'usage': usage})
        self._active()
        pending = self._native_pending
        if (not self._native_preview or pending is None
                or any(pending[key] != value for key, value in (
                    ('transaction_id', transaction_id), ('request_id', request_id), ('generation', generation)))
                or pending['revision'] != len(self._events) or pending['phase'] != self.phase):
            raise SessionError('STALE_NATIVE_REPLY')
        event = self._append('interviewer', 'reply', {
            'operation': pending['operation'], 'text': reply['reply'], 'model': model,
            'transaction_id': transaction_id, 'request_id': request_id,
            'prompt_sha256': pending['prompt_sha256'],
            'source_sha256': pending['source_sha256'], 'policy': pending['policy'],
            'usage': usage,
        }, 'LIVE_MODEL')
        self._native_pending = None
        return event

    def cancel_native_reply(self):
        pending = self._native_pending
        self._native_pending = None
        if pending is not None and self.phase == 'INTERVIEWING':
            self._append('host', 'model_request_cancelled', {
                'transaction_id': pending['transaction_id'],
                'request_id': pending['request_id'], 'operation': pending['operation'],
                'reply_committed': False,
            })
        return pending is not None

    def _text(self, value):
        if not isinstance(value, str) or not value.strip():
            raise SessionError('INVALID_INPUT')
        try:
            size = len(value.encode('utf-8'))
        except UnicodeError:
            raise SessionError('INVALID_INPUT') from None
        if size > self.config.max_input_bytes:
            raise SessionError('INPUT_TOO_LARGE')
        return value

    def _elapsed(self):
        if self._started is None:
            return 0.0
        return max(0.0, self._clock() - self._started)

    def _append(self, actor, kind, payload, provenance='HOST_VERIFIED'):
        if len(self._events) >= self.config.max_events:
            raise SessionError('EVENT_LIMIT')
        event = {'id': f'{self.config.session_id}:{len(self._events) + 1}',
                 'sequence': len(self._events) + 1,
                 'elapsed_seconds': round(self._elapsed(), 6), 'actor': actor,
                 'phase': self.phase, 'kind': kind, 'payload': copy.deepcopy(payload),
                 'provenance': provenance}
        self._events.append(event)
        return copy.deepcopy(event)

    def _available(self):
        if self._busy:
            raise SessionError('COMMAND_IN_PROGRESS')

    def _active(self):
        self._available()
        if self.phase != 'INTERVIEWING':
            raise SessionError('INVALID_TRANSITION')
        if self._elapsed() >= self.config.duration_seconds:
            self.close('timeout')
            raise SessionError('SESSION_EXPIRED')
        # Reserve room for expiry, close, review, handoff and training completion.
        if len(self._events) >= self.config.max_events - 8:
            self.close('event_limit')
            raise SessionError('EVENT_LIMIT')

    async def start(self, question):
        self._available()
        if self.phase != 'NEW':
            raise SessionError('INVALID_TRANSITION')
        question = self._text(question)
        self._started = self._clock()
        self._question = question
        self._phase = 'INTERVIEWING'
        self._append('host', 'session_started', {
            'question': question, 'duration_seconds': self.config.duration_seconds,
            'role_versions': {k: v.version for k, v in self._roles.items()},
            'mode': 'OFFLINE_MOCK', 'model_controls_scores': False})
        return await self.respond('brief')

    def candidate_action(self, kind, text):
        self._active()
        if not isinstance(kind, str) or kind not in self.ACTIONS:
            raise SessionError('INVALID_ACTION')
        text = self._text(text)
        return self._append('candidate', kind, {'text': text,
                            'execution': 'NOT_EXECUTED' if kind in ('implement', 'test') else 'NOT_APPLICABLE'},
                            provenance='USER_SAID')

    async def respond(self, operation='feedback'):
        self._active()
        if self._native_preview:
            raise SessionError('NATIVE_PROVIDER_REQUIRED')
        if operation not in ('brief', 'clarify', 'feedback', 'close'):
            raise SessionError('INVALID_OPERATION')
        if self.phase not in self._roles['interviewer'].active_states:
            raise SessionError('ROLE_NOT_ALLOWED')
        context = {'question': self._question,
                   'candidate_actions': [copy.deepcopy(e) for e in self._events if e['actor'] == 'candidate']}
        self._busy = True
        try:
            response = await self._portal.request(ModelRequest('interviewer', operation, context))
        except ModelPortalError as error:
            self._append('host', 'model_error', {'role': 'interviewer', 'code': error.code})
            raise
        finally:
            self._busy = False
        # A reply that arrives after the deadline is not an on-time interview turn.
        if self._elapsed() >= self.config.duration_seconds:
            self.close('timeout')
            raise SessionError('SESSION_EXPIRED')
        self._append('interviewer', 'reply', {'operation': operation, 'text': response.text}, response.provenance)
        return response

    def close(self, reason='submitted'):
        self._available()
        if self._closed_receipt is not None:
            return self.receipt
        if self.phase != 'INTERVIEWING' or reason not in ('submitted', 'timeout', 'cancelled', 'event_limit'):
            raise SessionError('INVALID_TRANSITION')
        self.cancel_native_reply()
        self._phase = 'CLOSED'
        self._append('host', 'session_closed', {'reason': reason})
        candidate = [e for e in self._events if e['actor'] == 'candidate']
        receipt = {'schema': 'tia-offline-receipt/v1', 'session_id': self.config.session_id,
                   'status': 'CLOSED', 'reason': reason, 'mode': 'OFFLINE_MOCK',
                   'events': copy.deepcopy(self._events), 'live_model_used': False,
                   'sql_executed': False, 'assessment': {
                       'technical': {'status': 'NOT_SCORED', 'value': None,
                                     'evidence_ids': [e['id'] for e in candidate if e['kind'] in ('plan', 'implement', 'test')]},
                       'communication': {'status': 'NOT_SCORED', 'value': None,
                                         'evidence_ids': [e['id'] for e in candidate]}}}
        if self._native_preview:
            receipt.update(schema='tia-live-preview-receipt/v1',
                           mode='LIVE_CONVERSATIONAL_PREVIEW',
                           live_model_used=any(e['provenance'] == 'LIVE_MODEL' for e in self._events),
                           execution_status='NOT_RUN', preview_only=True)
        encoded = json.dumps(receipt, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
        receipt['sha256'] = hashlib.sha256(encoded).hexdigest()
        self._closed_receipt = receipt
        return self.receipt

    def review(self, reviewer='demo-reviewer'):
        self._available()
        if self.phase != 'CLOSED':
            raise SessionError('INVALID_TRANSITION')
        reviewer = self._text(reviewer)
        if len(reviewer) > 80:
            raise SessionError('INVALID_INPUT')
        self._phase = 'REVIEWED'
        self._review = self._append('reviewer', 'receipt_reviewed', {
            'reviewer': reviewer, 'receipt_sha256': self._closed_receipt['sha256'],
            'scope': 'handoff_eligibility_only; no competency grading'})
        return copy.deepcopy(self._review)

    async def handoff(self):
        self._available()
        if self.phase != 'REVIEWED':
            raise SessionError('INVALID_TRANSITION')
        if 'TRAINING' not in self._roles['trainer'].active_states:
            raise SessionError('ROLE_NOT_ALLOWED')
        if len(self._events) >= self.config.max_events - 2:
            raise SessionError('EVENT_LIMIT')
        context = {'reviewed_receipt': self.receipt, 'review': copy.deepcopy(self._review)}
        self._busy = True
        try:
            response = await self._portal.request(ModelRequest('trainer', 'drill', context))
        except ModelPortalError as error:
            self._append('host', 'model_error', {'role': 'trainer', 'code': error.code})
            raise
        finally:
            self._busy = False
        self._phase = 'TRAINING'
        self._append('trainer', 'drill_assigned', {'text': response.text,
                     'receipt_sha256': self._closed_receipt['sha256'], 'review_event_id': self._review['id']}, response.provenance)
        return response

    def finish_training(self):
        self._available()
        if self.phase != 'TRAINING':
            raise SessionError('INVALID_TRANSITION')
        self._phase = 'COMPLETE'
        self._append('host', 'training_completed', {'assessment': 'NOT_SCORED',
                     'transfer_claim': 'NOT_EVALUATED'})
        return self.snapshot()
