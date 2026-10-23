"""S03 tutorial host: native renderer commands are data, not authority.

The S02 InterviewController remains the interview state machine. Wizard state
belongs here, never to JavaScript. Recovery replays a bounded journal through
the same controller with saved clock samples and the deterministic offline
adapter, then verifies the complete result digest. No model or SQL engine runs
during recovery. The older tutorial clock excludes downtime. The E2 rehearsal
clock is separate: journalled wall + monotonic samples include offline time.
"""

import argparse
import asyncio
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import uuid

from .controller import InterviewController, SessionConfig, SessionError
from .persistence import SaveError, TutorialStore, strict_json
from .prompt_profiles import ProfileError, compile_profile, compile_live_profile, decide_interaction
from .provider import ModelPortalError
from .setup import SetupError, assess_allocation, review_question, validate_config
from .freeform_import import extract_freeform, ImportIssue, MAX_RAW_QUESTION_BYTES
from .native_contract import PREPARE_FIELDS, COMMIT_FIELDS, validate_prepare, validate_commit
from .rehearsal import create_plan, public_plan, question_from_review, MAX_REHEARSAL_TURNS, RehearsalError
from .grading_binding import (GradingBindingError, inspect_binding, verify_grade_receipt, find_approved_pg_config)
from .sql_accuracy import AccuracyError, grade_fixture
from .evidence_scorecard import build_scorecard
from .communication_rubric import build_communication_evidence
from .grounded_trainer import build_grounded_trainer
from .time_intelligence import begin as begin_rehearsal_time, advance as advance_rehearsal_time, start_on_question_presented, request_started, request_finished, close_question, final_metrics, event as time_event


PROTOCOL = "tia-native-tutorial/v1"
SAVE_SCHEMA = "tia-tutorial-save/v1"
MAX_REQUEST_BYTES = 32768
MAX_JOURNAL_ENTRIES = 512
MAX_CANDIDATE_ACTIONS = 48
QUESTION = {
    "id": "tutorial-first-order-v1",
    "title": "First Order per Customer",
    "statement": (
        "For every customer, return their earliest order. When timestamps tie, "
        "choose the smallest order ID. Exclude records with missing timestamps. "
        "Return customer_id, order_id, and order_date, ordered by customer_id."
    ),
    "schema": "Orders(\n  order_id INT,\n  customer_id INT,\n  order_date TIMESTAMP\n)",
    "difficulty": "MEDIUM",
    "environment": "POSTGRESQL",
}
COMMAND_FIELDS = {
    "snapshot": set(), "tutorial_start": set(), "tutorial_next": set(),
    "tutorial_back": set(), "tutorial_submit": {"kind", "text"},
    "tutorial_complete": set(), "tutorial_replay": set(), "choose_real": set(),
    "language": {"language"}, "reset": set(), "export": set(),
    "setup_continue": set(), "setup_config": {"config"},
    "setup_questions": {"questions"}, "setup_mechanism": {"mechanism"},
    "setup_question_set": {"index", "raw_text", "source"},
    "setup_question_confirm": {"index", "fields", "raw_sha256"},
    "setup_questions_finish": set(),
    "practice_start": {"index", "content_sha256"},
    "setup_back": set(), "setup_launch": set(),
    # These native_* commands are private worker IPC. Bridge.swift explicitly
    # rejects them as renderer actions. They contain no credentials or URLs.
    "native_prepare_preview": PREPARE_FIELDS, "native_commit_preview": COMMIT_FIELDS,
    "native_cancel_preview": set(), "preview_close": set(),
    "rehearsal_start": set(), "rehearsal_submit": set(), "rehearsal_skip": set(),
    "rehearsal_tick": set(),
    "grade_inspect": {"fixture_json"}, "grade_execute": {"fixture_sha256"},
}
MUTATING_COMMANDS = frozenset(COMMAND_FIELDS) - {"snapshot", "export", "reset"}
SCREENS = ("ENTRY", "WELCOME", "RULES", "QUESTION", "ROOM", "COMPLETE", "API_PORTAL",
           "CONFIG", "QUESTION_SOURCE", "MECHANISM", "REVIEW", "LIVE_PREVIEW", "REHEARSAL_COMPLETE")
CONFIG_FIELDS = {"technical_environment", "duration_minutes", "difficulty",
                 "question_source", "interviewer_mechanism"}
SETUP_STATE_FIELDS = ("setup_config", "setup_questions", "setup_allocation",
                      "setup_profiles", "setup_blockers")


class HostError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class TutorialHost:
    def __init__(self, data_dir, clock=None, wall_clock=None):
        self._wall_clock = wall_clock or time.time
        self._wall_sample = None
        self.store = TutorialStore(data_dir)
        self._clock = clock or time.monotonic
        self._origin = self._clock()
        self._clock_offset = 0.0
        self._tick = 0.0
        self._journal = []
        self._instance_id = uuid.uuid4().hex
        self._reset_memory()
        self._saved = False
        self._recovery_error = None

    @classmethod
    async def open(cls, data_dir, clock=None, wall_clock=None):
        host = cls(data_dir, clock=clock, wall_clock=wall_clock)
        try:
            document = host.store.read()
            if document is not None:
                await host._restore(document)
        except (SaveError, HostError, SessionError, ModelPortalError,
                TypeError, ValueError, KeyError, OverflowError, RecursionError):
            host._reset_memory()
            host._journal = []
            host._saved = False
            host._recovery_error = "INVALID_SAVE"
        return host

    def close(self):
        self.store.close()

    def _reset_memory(self):
        self.screen = "ENTRY"
        self.language = "en"
        self.controller = None
        self.feedback = ""
        self.trainer_preview = None
        self._cycle = 0
        self._setup_config = None
        self.setup_questions = []
        self.setup_allocation = None
        self._effective_profiles = None
        self.setup_profiles = None
        self.setup_blockers = []
        self._live_controller = None
        self._live_profile = None
        self._live_question = None
        self._prepared_return = None
        self._preview_history = []
        self._practice_question = None
        self._rehearsal = None
        self._grading_review = None
        self._grading_observation = None
        self._replay_observation = None

    def _selected_preview_question(self):
        # Freeze source binding for each preview; later edits cannot relabel a
        # prior session's model input or evidence on reopening.
        return copy.deepcopy(self._live_question if self._live_controller is not None else
                             (self._rehearsal["questions"][self._rehearsal["current_index"]]
                              if self._rehearsal is not None and self._rehearsal["status"] == "ACTIVE"
                              else (self._practice_question or QUESTION)))

    def _practice_snapshot(self):
        return copy.deepcopy(self._practice_question) if self._practice_question else None

    def _preview_state(self):
        if self._live_controller is None:
            return None
        session = self._live_controller.snapshot()
        candidates = [e for e in session['events'] if e['actor'] == 'candidate']
        replies = [e for e in session['events']
                   if e['actor'] == 'interviewer' and e['provenance'] == 'LIVE_MODEL']
        verified = any(e['payload']['operation'] == 'verify' for e in replies)
        answered_count = sum(e['payload']['operation'] == 'reply' for e in replies)
        pending = self._live_controller.native_pending is not None
        closed = self._live_controller.phase != 'INTERVIEWING'
        rehearsal_active = self._rehearsal is not None and self._rehearsal['status'] == 'ACTIVE'
        limit = MAX_REHEARSAL_TURNS if rehearsal_active else 1
        unanswered = len(candidates) > answered_count
        return {
            'question': self._selected_preview_question(), 'session': session,
            'pending': pending, 'closed': closed,
            'mechanism': self._live_profile['mechanism'],
            'prompt_provenance': {key: copy.deepcopy(value)
                                  for key, value in self._live_profile.items() if key != 'instructions'},
            'execution_status': ('RUN_LOCAL_FIXTURE' if self._active_grade_receipt() else 'NOT_RUN'),
            'sql_accuracy': copy.deepcopy(self._active_grade_receipt()), 'technical': 'NOT_SCORED',
            'communication': 'NOT_SCORED', 'candidate_turn_limit': limit,
            'candidate_turns_used': len(candidates),
            'can_send': verified and (unanswered or len(candidates) < limit) and not pending and not closed,
            'retry_input': ({'kind': candidates[-1]['kind'], 'text': candidates[-1]['payload']['text']}
                            if unanswered else None),
            'verified_response_count': len(replies),
            'full_interview_authorized': False,
        }

    def state(self):
        steps = {"WELCOME": 1, "RULES": 2, "QUESTION": 3, "ROOM": 4, "COMPLETE": 5}
        result = {
            "screen": self.screen, "language": self.language,
            "tutorial_step": steps.get(self.screen, 0),
            "session": self.controller.snapshot() if self.controller else None,
            "question": copy.deepcopy(QUESTION), "feedback": self.feedback,
            "trainer_preview": copy.deepcopy(self.trainer_preview),
            "execution_status": "NOT_RUN", "model_state": "offline",
            "api_requests": 0, "saved_locally": self._saved,
            "recovery_error": self._recovery_error,
            "setup_config": (dict(self._setup_config.snapshot(), status="DRAFT")
                             if self._setup_config else None),
            "setup_questions": copy.deepcopy(self.setup_questions),
            "setup_allocation": copy.deepcopy(self.setup_allocation),
            "setup_profiles": copy.deepcopy(self.setup_profiles),
            "setup_blockers": list(self.setup_blockers),
        }
        if self._practice_question is not None:
            result['practice_question'] = self._practice_snapshot()
        if self._rehearsal is not None:
            result['rehearsal'] = public_plan(self._rehearsal)
            result['evidence_scorecard'] = build_scorecard(self._rehearsal)
            result['communication_evidence'] = build_communication_evidence(self._rehearsal)
            result['grounded_trainer'] = build_grounded_trainer(self._rehearsal)
            if self._grading_review is not None and self._rehearsal['status'] == 'ACTIVE':
                result['grading_review'] = {key: copy.deepcopy(value) for key, value in self._grading_review.items()
                                            if key != 'fixture_json'}
        if self._live_controller is not None:
            result['live_preview'] = self._preview_state()
            result['live_preview_history'] = copy.deepcopy(self._preview_history)
            # Native memory owns provider authentication and charged attempts;
            # committed responses cannot establish an actual paid request count.
            result['api_requests'] = None
        return result

    def _active_grade_receipt(self):
        if self._rehearsal is None or self._rehearsal['status'] != 'ACTIVE':
            return None
        grades = self._rehearsal.get('grades') or {}
        return grades.get(str(self._rehearsal['current_index']))

    def _last_implementation(self):
        if self._live_controller is None or self._live_controller.phase != 'INTERVIEWING':
            raise HostError('NO_ACTIVE_SQL_SUBMISSION')
        candidate = [e for e in self._live_controller.snapshot()['events']
                     if e['actor'] == 'candidate' and e['kind'] == 'implement']
        if not candidate:
            raise HostError('NO_ACTIVE_SQL_SUBMISSION')
        return candidate[-1]

    def _state_digest(self):
        public = self.state()
        # Storage availability is not interview authority or replayed evidence.
        public.pop("saved_locally")
        public.pop("recovery_error")
        # E3 is an additive read-only projection, not new replay authority.
        # Excluding it preserves all E1/E2/E25B saved state digests verbatim.
        public.pop("evidence_scorecard", None)
        public.pop("grounded_trainer", None)
        # Additive S03-B fields have no authority when no draft exists. Omitting
        # their empty defaults preserves the digest of existing S03-A v1 saves.
        if self._setup_config is None:
            for name in SETUP_STATE_FIELDS:
                public.pop(name)
        return digest(public)

    @staticmethod
    def _validate_command(action, params):
        if (type(action) is not str or action not in COMMAND_FIELDS
                or type(params) is not dict or set(params) != COMMAND_FIELDS[action]):
            raise HostError("INVALID_COMMAND")
        if action == 'native_prepare_preview':
            validate_prepare(params)
        if action == 'grade_inspect':
            if (type(params['fixture_json']) is not str or
                    len(params['fixture_json'].encode('utf-8')) > 12000):
                raise HostError('INVALID_GRADE_FIXTURE_SIZE')
        if action == 'grade_execute' and (type(params['fixture_sha256']) is not str or
                                         re.fullmatch(r'[0-9a-f]{64}', params['fixture_sha256']) is None):
            raise HostError('INVALID_GRADE_APPROVAL')
        if action == 'native_commit_preview':
            validate_commit(params)
        if action == "language" and (
                type(params["language"]) is not str or params["language"] not in ("en", "zh")):
            raise HostError("INVALID_LANGUAGE")
        if action == "tutorial_submit":
            if (type(params["kind"]) is not str
                    or params["kind"] not in ("clarify", "plan", "implement", "test", "help")):
                raise HostError("INVALID_ACTION")
            if type(params["text"]) is not str or not params["text"].strip():
                raise HostError("INVALID_INPUT")
            try:
                if len(params["text"].encode("utf-8")) > 8192:
                    raise HostError("INPUT_TOO_LARGE")
            except UnicodeError:
                raise HostError("INVALID_INPUT") from None
        if action == "setup_config":
            if type(params["config"]) is not dict or set(params["config"]) != CONFIG_FIELDS:
                raise HostError("INVALID_CONFIGURATION_FIELDS")
            try:
                validate_config(params["config"])
            except SetupError as error:
                raise HostError(str(error)) from None
        if action == "setup_questions":
            questions = params["questions"]
            if type(questions) is not list or len(questions) > 4:
                raise HostError("INVALID_QUESTION_ALLOCATION")
            for text in questions:
                if type(text) is not str:
                    raise HostError("INVALID_IMPORT_TYPE")
                try:
                    if len(text.encode("utf-8")) > 4096:
                        raise HostError("IMPORT_TOO_LARGE")
                except UnicodeError:
                    raise HostError("INVALID_IMPORT_ENCODING") from None
        if action == "setup_question_set":
            if type(params["index"]) is not int or not 0 <= params["index"] < 4:
                raise HostError("INVALID_QUESTION_SLOT")
            if type(params["source"]) is not str or params["source"] not in ("LEETCODE", "HACKERRANK", "OWNER"):
                raise HostError("INVALID_QUESTION_SOURCE")
            raw = params["raw_text"]
            if type(raw) is not str or not raw.strip():
                raise HostError("EMPTY_QUESTION")
            try:
                if len(raw.encode("utf-8")) > MAX_RAW_QUESTION_BYTES:
                    raise HostError("IMPORT_TOO_LARGE")
            except UnicodeError:
                raise HostError("INVALID_IMPORT_ENCODING") from None
        if action == "setup_question_confirm":
            if type(params["index"]) is not int or not 0 <= params["index"] < 4:
                raise HostError("INVALID_QUESTION_SLOT")
            fields = params["fields"]
            if (type(fields) is not dict or set(fields) != {
                    "problem_statement", "task", "schema", "example_input", "expected_output",
                    "environment", "source", "constraints", "source_reference"}):
                raise HostError("INVALID_CONFIRMATION_FIELDS")
            if any(type(item) is not str for item in fields.values()):
                raise HostError("INVALID_CONFIRMATION_FIELDS")
            try:
                if len(json.dumps(fields, ensure_ascii=True).encode("utf-8")) > 24000:
                    raise HostError("CONFIRMATION_TOO_LARGE")
            except UnicodeError:
                raise HostError("INVALID_IMPORT_ENCODING") from None
            if type(params["raw_sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", params["raw_sha256"]):
                raise HostError("INVALID_QUESTION_DIGEST")
        if action == "practice_start":
            if type(params["index"]) is not int or not 0 <= params["index"] < 4:
                raise HostError("INVALID_QUESTION_SLOT")
            if type(params["content_sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", params["content_sha256"]):
                raise HostError("INVALID_QUESTION_DIGEST")
        if action == "setup_mechanism" and (
                type(params["mechanism"]) is not str
                or params["mechanism"] not in ("STRICT_CHALLENGING", "PROFESSIONAL_SUPPORTIVE")):
            raise HostError("UNKNOWN_MECHANISM")

    def _refresh_allocation(self):
        self.setup_allocation = assess_allocation(self._setup_config, self.setup_questions)
        wrong_difficulty = any(
            (review.get("extraction") or {}).get("declared_difficulty") in ("EASY", "MEDIUM")
            for review in self.setup_questions
        )
        self.setup_blockers = list(dict.fromkeys([
            "PROVIDER_AUTHENTICATION_REQUIRED",
            *self.setup_allocation["issues"],
            *(["QUESTION_DIFFICULTY_NOT_HARD"] if wrong_difficulty else []),
            "LIVE_INTERVIEW_NOT_IMPLEMENTED",
        ]))

    def _review_paste(self, text, source="OWNER"):
        extracted = None
        try:
            review = review_question(text, self._setup_config.technical_environment)
        except SetupError as error:
            # JSON/labeled failures remain errors; never reinterpret malformed JSON
            # as a successful freeform import.
            if (str(error) == "LABELED_IMPORT_REQUIRED" and not text.lstrip().startswith("{")
                    and re.search(r"(?:\bTable\s*:|\bSQL Schema\b|\bPandas Schema\b|\bInput\s*:|\bOutput\s*:|\bWrite a solution\b|\bQuery a list\b)", text, re.I)):
                try:
                    extracted = extract_freeform(text, environment=self._setup_config.technical_environment,
                                                 source=source)
                    review = review_question(extracted["fields"], self._setup_config.technical_environment)
                except (ImportIssue, SetupError) as failure:
                    review = review_question({}, self._setup_config.technical_environment)
                    review["issues"].append({"field": "import", "code": str(failure)})
            else:
                review = review_question({}, self._setup_config.technical_environment)
                review["issues"].append({"field": "import", "code": str(error)})
        review["raw_input"] = text
        review["raw_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if extracted:
            review["extraction"] = extracted["metadata"]
            review["extraction_issues"] = extracted["issues"]
        review["human_confirmed"] = False
        review["practice_eligible"] = False
        return review

    def _candidate_events(self):
        if not self.controller:
            return []
        return [event for event in self.controller.snapshot()["events"]
                if event["actor"] == "candidate"]

    def _end_rehearsal_due_to_time(self, integrity_hold=False):
        """Host-only, irreversible timeout/clock-hold transition; no model call."""
        plan = self._rehearsal
        if plan is None or plan['status'] != 'ACTIVE':
            return
        code = 'CLOCK_INTEGRITY_HOLD' if integrity_hold else 'TIMED_OUT'
        if self._live_controller is not None:
            if self._live_controller.phase == 'INTERVIEWING':
                self._live_controller.close('cancelled' if integrity_hold else 'timeout')
                self._live_controller.review('rehearsal-host-time-integrity')
        request_finished(plan)
        time_event(plan, 'CLOCK_INTEGRITY_HOLD' if integrity_hold else 'SESSION_TIMED_OUT')
        if plan.get('timing'):
            plan['timing']['questions'][plan['timing']['current_question']]['ended'] = True
        for i in range(plan['current_index'], 3):
            preserved_grade = (plan.get('grades') or {}).get(str(i))
            result = {
                'index': i, 'outcome': code if i == plan['current_index'] else 'NOT_REACHED',
                'execution_status': ('RUN_LOCAL_FIXTURE' if preserved_grade and preserved_grade['correctness'] == 'VERIFIED_LOCAL_FIXTURE'
                                     else 'NOT_VERIFIED' if preserved_grade else 'NOT_RUN'),
                'technical': 'NOT_SCORED', 'communication': 'NOT_SCORED',
                'question_sha256': plan['questions'][i]['content_sha256'],
                'session': (self._live_controller.snapshot() if i == plan['current_index']
                            and self._live_controller is not None else None),
                'time_metrics': (copy.deepcopy(plan['timing']['questions'][i])
                                 if plan.get('timing') else None),
            }
            if preserved_grade is not None:
                result['sql_accuracy'] = copy.deepcopy(preserved_grade)
            plan['results'].append(result)
        plan['current_index'] = 3
        plan['status'] = code
        self._live_controller = self._live_profile = self._live_question = None
        self.screen = 'REHEARSAL_COMPLETE'

    def _advance_rehearsal_before_action(self, action):
        if (self._rehearsal is None or self._rehearsal['status'] != 'ACTIVE'
                or self._rehearsal.get('timing') is None or self._wall_sample is None):
            return
        try:
            result = advance_rehearsal_time(self._rehearsal, self._wall_sample, self._tick)
        except ValueError:
            raise HostError('INVALID_CLOCK_SAMPLE') from None
        if result in ('TIMEOUT', 'CLOCK_HOLD'):
            self._end_rehearsal_due_to_time(result == 'CLOCK_HOLD')
            if action != 'rehearsal_tick':
                raise HostError('REHEARSAL_TIME_LIMIT' if result == 'TIMEOUT'
                                else 'REHEARSAL_CLOCK_INTEGRITY_HOLD')

    async def _dispatch(self, action, params):
        self._validate_command(action, params)
        self._advance_rehearsal_before_action(action)
        if action == 'rehearsal_tick':
            # Polls are Host-only time checkpoints. Nothing is charged.
            return
        if action in ('grade_inspect', 'grade_execute'):
            await self._grade_dispatch(action, params)
            return
        if (self._live_controller is not None and self._live_controller.native_pending is not None
                and action not in ('native_commit_preview', 'native_cancel_preview', 'preview_close', 'rehearsal_tick')):
            raise HostError('NATIVE_REQUEST_PENDING')
        if (self._rehearsal is not None and self._rehearsal['status'] == 'ACTIVE'
                and action not in ('language', 'snapshot', 'export', 'api_portal',
                                   'rehearsal_submit', 'rehearsal_skip',
                                   'preview_verify', 'preview_send', 'preview_close',
                                   'native_prepare_preview', 'native_commit_preview',
                                   'native_cancel_preview', 'rehearsal_tick',
                                   'grade_inspect', 'grade_execute')):
            raise HostError('REHEARSAL_ACTIVE')
        if action == "language":
            self.language = params["language"]
        elif action in ("tutorial_start", "tutorial_replay"):
            if action == "tutorial_start" and self.screen != "ENTRY":
                raise HostError("INVALID_TRANSITION")
            if action == "tutorial_replay" and self.screen != "COMPLETE":
                raise HostError("INVALID_TRANSITION")
            self._cycle += 1
            self.controller = None
            self.feedback = ""
            self.trainer_preview = None
            self.screen = "WELCOME"
        elif action == "tutorial_next":
            next_screen = {"WELCOME": "RULES", "RULES": "QUESTION", "QUESTION": "ROOM"}
            if self.screen not in next_screen:
                raise HostError("INVALID_TRANSITION")
            if self.screen == "QUESTION" and self.controller is None:
                self.controller = InterviewController(
                    SessionConfig(
                        session_id="tutorial-" + self._instance_id + "-" + str(self._cycle),
                        duration_seconds=86400,
                    ),
                    clock=lambda: self._tick,
                )
                reply = await self.controller.start(QUESTION["statement"])
                self.feedback = reply.text
            self.screen = next_screen[self.screen]
        elif action == "tutorial_back":
            previous = {"WELCOME": "ENTRY", "RULES": "WELCOME", "QUESTION": "RULES",
                        "ROOM": "QUESTION", "API_PORTAL": "ENTRY"}
            if self.screen not in previous:
                raise HostError("INVALID_TRANSITION")
            self.screen = previous[self.screen]
        elif action == "tutorial_submit":
            if self.screen != "ROOM" or self.controller is None:
                raise HostError("INVALID_TRANSITION")
            if len(self._candidate_events()) >= MAX_CANDIDATE_ACTIONS:
                raise HostError("ACTION_LIMIT")
            self.controller.candidate_action(params["kind"], params["text"])
            reply = await self.controller.respond(
                "clarify" if params["kind"] == "clarify" else "feedback"
            )
            self.feedback = reply.text
        elif action == "tutorial_complete":
            if self.screen != "ROOM" or not self._candidate_events():
                raise HostError("INPUT_REQUIRED")
            self.controller.close()
            self.controller.review("tutorial-host-eligibility-check")
            reply = await self.controller.handoff()
            self.controller.finish_training()
            self.trainer_preview = {
                "text": reply.text,
                "evidence_ids": [event["id"] for event in self._candidate_events()],
                "follow_up": (
                    "Unfamiliar follow-up: select each device's latest non-null sensor "
                    "reading, resolving timestamp ties with the largest reading ID. "
                    "Explain the changed ordering and one diagnostic fixture before coding."
                ),
                "provenance": "SIMULATED",
            }
            self.screen = "COMPLETE"
        elif action == "choose_real":
            self.screen = "API_PORTAL"
        elif action == "setup_continue":
            if self.screen != "API_PORTAL":
                raise HostError("INVALID_TRANSITION")
            # S03-C permits this draft without a credential. No authentication
            # assertion enters Python; full launch remains blocked independently.
            self.screen = "CONFIG"
        elif action == "setup_config":
            if self.screen not in ("CONFIG", "QUESTION_SOURCE"):
                raise HostError("INVALID_TRANSITION")
            config = validate_config(params["config"])
            previous_source = self._setup_config.question_source if self._setup_config else None
            self._setup_config = config
            self._practice_question = None
            self._effective_profiles = self.setup_profiles = None
            old_text = ([review["raw_input"] for review in self.setup_questions]
                        if previous_source == config.question_source else [])
            self.setup_questions = [self._review_paste(text) for text in old_text]
            self._refresh_allocation()
            self.screen = "QUESTION_SOURCE"
        elif action == "setup_questions":
            # Legacy batch behavior is retained for existing saves and S03-B tests.
            if self.screen != "QUESTION_SOURCE" or self._setup_config is None:
                raise HostError("INVALID_TRANSITION")
            self.setup_questions = [self._review_paste(text) for text in params["questions"]]
            self._effective_profiles = self.setup_profiles = None
            self._refresh_allocation()
            if (self._setup_config.question_source == "BYOQ"
                    and not self.setup_allocation["ready_for_content_review"]):
                raise HostError("QUESTION_REVIEW_REQUIRED")
            self.screen = "MECHANISM"
        elif action == "setup_question_set":
            if (self.screen != "QUESTION_SOURCE" or self._setup_config is None
                    or self._setup_config.question_source != "BYOQ"):
                raise HostError("INVALID_TRANSITION")
            index = params["index"]
            if index >= self._setup_config.question_count or index > len(self.setup_questions):
                raise HostError("QUESTION_SLOT_ORDER")
            reviewed = self._review_paste(params["raw_text"], params["source"])
            if index == len(self.setup_questions):
                self.setup_questions.append(reviewed)
            else:
                self.setup_questions[index] = reviewed
            self._practice_question = None
            self._effective_profiles = self.setup_profiles = None
            self._refresh_allocation()
        elif action == "setup_question_confirm":
            if (self.screen != "QUESTION_SOURCE" or self._setup_config is None
                    or self._setup_config.question_source != "BYOQ"):
                raise HostError("INVALID_TRANSITION")
            index = params["index"]
            if index >= len(self.setup_questions):
                raise HostError("QUESTION_SLOT_NOT_FOUND")
            original = self.setup_questions[index]
            if original["raw_sha256"] != params["raw_sha256"]:
                raise HostError("STALE_QUESTION_REVIEW")
            try:
                reviewed = review_question(params["fields"], self._setup_config.technical_environment)
            except SetupError as error:
                raise HostError(str(error)) from None
            # A live conversation needs a real task and reviewed schema, not
            # necessarily official executable examples. Formal launch is unchanged.
            required = ("problem_statement", "task", "schema", "environment", "source")
            if any(not reviewed["fields"].get(key, "").strip() for key in required):
                raise HostError("PRACTICE_REQUIRED_FIELDS_MISSING")
            if any(issue["field"] in required or issue["code"] in
                   ("FIELD_TOO_LARGE", "INVALID_CONTROL_CHARACTER") for issue in reviewed["issues"]):
                raise HostError("PRACTICE_REVIEW_REQUIRED")
            reviewed.update(raw_input=original["raw_input"], raw_sha256=original["raw_sha256"],
                            human_confirmed=True, practice_eligible=True)
            if "extraction" in original:
                reviewed["extraction"] = original["extraction"]
                reviewed["extraction_issues"] = original.get("extraction_issues", [])
            self.setup_questions[index] = reviewed
            self._practice_question = None
            self._refresh_allocation()
        elif action == "setup_questions_finish":
            if self.screen != "QUESTION_SOURCE" or self._setup_config is None:
                raise HostError("INVALID_TRANSITION")
            self._refresh_allocation()
            if (self._setup_config.question_source == "BYOQ"
                    and not self.setup_allocation["ready_for_content_review"]):
                raise HostError("QUESTION_REVIEW_REQUIRED")
            if "QUESTION_DIFFICULTY_NOT_HARD" in self.setup_blockers:
                raise HostError("QUESTION_DIFFICULTY_NOT_HARD")
            self.screen = "MECHANISM"
        elif action == "practice_start":
            if (self.screen != "QUESTION_SOURCE" or self._setup_config is None
                    or self._setup_config.question_source != "BYOQ"):
                raise HostError("INVALID_TRANSITION")
            index = params["index"]
            if index >= len(self.setup_questions):
                raise HostError("QUESTION_SLOT_NOT_FOUND")
            review = self.setup_questions[index]
            if (not review.get("human_confirmed") or not review.get("practice_eligible")
                    or review["content_sha256"] != params["content_sha256"]):
                raise HostError("PRACTICE_REVIEW_REQUIRED")
            fields = review["fields"]
            if self._live_controller is not None and self._live_controller.phase == 'INTERVIEWING':
                raise HostError('PREVIEW_ACTIVE')
            self._practice_question = {
                "id": review["question_id"],
                "title": ((review.get("extraction") or {}).get("title") or {}).get("text") or "User-submitted question",
                "statement": fields["problem_statement"] + "\n\nTask: " + fields["task"],
                "schema": fields["schema"],
                "example_input": fields.get("example_input", ""),
                "expected_output": fields.get("expected_output", ""),
                "constraints": fields.get("constraints", ""),
                "difficulty": (review.get("extraction") or {}).get("declared_difficulty") or "UNVERIFIED",
                "environment": fields["environment"],
                "source": fields["source"],
                "content_sha256": review["content_sha256"],
                "practice_only": True,
            }
            self.screen = "API_PORTAL"
        elif action == "setup_mechanism":
            if self.screen != "MECHANISM" or self._setup_config is None:
                raise HostError("INVALID_TRANSITION")
            values = {key: getattr(self._setup_config, key) for key in CONFIG_FIELDS}
            values["interviewer_mechanism"] = params["mechanism"]
            config = validate_config(values)
            try:
                profiles = {role: compile_profile(
                    Path(__file__).resolve().parents[1], params["mechanism"], role
                ) for role in ("interviewer", "trainer")}
            except ProfileError as error:
                raise HostError(str(error)) from None
            self._setup_config = config
            self._effective_profiles = profiles
            self.setup_profiles = {
                role: {key: copy.deepcopy(value) for key, value in profile.items()
                       if key != "instructions"} for role, profile in profiles.items()
            }
            self._refresh_allocation()
            self.screen = "REVIEW"
        elif action == 'rehearsal_start':
            if self.screen not in ('QUESTION_SOURCE', 'REVIEW'):
                raise HostError('INVALID_TRANSITION')
            if self._live_controller is not None and self._live_controller.phase == 'INTERVIEWING':
                raise HostError('PREVIEW_ACTIVE')
            if self._rehearsal is not None:
                raise HostError('REHEARSAL_ALREADY_STARTED')
            if self._live_controller is not None and len(self._preview_history) >= 8:
                raise HostError('PREVIEW_HISTORY_LIMIT')
            try:
                plan = create_plan(self._setup_config, self.setup_questions)
            except RehearsalError as error:
                raise HostError(str(error)) from None
            if self._live_controller is not None:
                # Do not erase an already frozen S03-C/D record when a new
                # three-question rehearsal begins from the same private save.
                self._preview_history.append(self._preview_state())
            # Old journals replay with no wall sample, preserving E1 snapshots.
            if self._wall_sample is not None:
                plan['timing'] = begin_rehearsal_time(self._wall_sample, self._tick)
            self._rehearsal = plan
            self._grading_review = None
            self._practice_question = None
            self._live_controller = self._live_profile = None
            self._live_question = None
            self.screen = 'API_PORTAL'
        elif action in ('rehearsal_submit', 'rehearsal_skip'):
            if (self._rehearsal is None or self._rehearsal['status'] != 'ACTIVE'
                    or self.screen not in ('LIVE_PREVIEW', 'API_PORTAL')):
                raise HostError('REHEARSAL_NOT_ACTIVE')
            if self._live_controller is not None and self._live_controller.native_pending is not None:
                raise HostError('NATIVE_REQUEST_PENDING')
            result = {
                'index': self._rehearsal['current_index'],
                'outcome': ('SKIPPED' if action == 'rehearsal_skip' else
                            'NO_SUBMISSION' if self._live_controller is None or not any(
                                e['actor'] == 'candidate' for e in self._live_controller.snapshot()['events'])
                            else 'SUBMITTED_UNVERIFIED' if any(
                                e['actor'] == 'candidate' and e['kind'] == 'implement'
                                for e in self._live_controller.snapshot()['events'])
                            else 'DISCUSSION_ONLY'),
                'execution_status': 'NOT_RUN', 'technical': 'NOT_SCORED',
                'communication': 'NOT_SCORED',
                'question_sha256': self._rehearsal['questions'][self._rehearsal['current_index']]['content_sha256'],
                'session': None,
            }
            receipt = self._active_grade_receipt()
            if receipt is not None:
                result['sql_accuracy'] = copy.deepcopy(receipt)
                result['execution_status'] = ('RUN_LOCAL_FIXTURE' if receipt['correctness'] == 'VERIFIED_LOCAL_FIXTURE'
                                              else 'NOT_VERIFIED')
            if self._rehearsal.get('timing') is not None:
                result['time_metrics'] = close_question(self._rehearsal, outcome=result['outcome'])
            if self._live_controller is not None:
                candidate = [e for e in self._live_controller.snapshot()['events'] if e['actor'] == 'candidate']
                result['behavior_metrics'] = {
                    'candidate_turn_count': len(candidate),
                    'clarification_requests': sum(e['kind'] == 'clarify' for e in candidate),
                    'help_requests': sum(e['kind'] == 'help' for e in candidate),
                    'code_submissions': sum(e['kind'] == 'implement' for e in candidate),
                    'evidence_event_ids': [e['id'] for e in candidate],
                    'correctness': (receipt['correctness'] if receipt else 'NOT_VERIFIED'),
                }
                if self._live_controller.phase == 'INTERVIEWING':
                    self._live_controller.close('submitted' if action == 'rehearsal_submit' else 'cancelled')
                    self._live_controller.review('rehearsal-host-handoff-eligibility-only')
                result['session'] = self._live_controller.snapshot()
            self._rehearsal['results'].append(result)
            self._rehearsal['current_index'] += 1
            self._live_controller = self._live_profile = None
            self._live_question = None
            self._grading_review = None
            if self._rehearsal['current_index'] == 3:
                self._rehearsal['status'] = 'COMPLETE'
                self.screen = 'REHEARSAL_COMPLETE'
            else:
                self.screen = 'API_PORTAL'
        elif action == "setup_back":
            previous = {"REVIEW": "MECHANISM", "MECHANISM": "QUESTION_SOURCE",
                        "QUESTION_SOURCE": "CONFIG", "CONFIG": "API_PORTAL"}
            if self.screen not in previous:
                raise HostError("INVALID_TRANSITION")
            self.screen = previous[self.screen]
        elif action == "setup_launch":
            if self.screen != "REVIEW":
                raise HostError("INVALID_TRANSITION")
            raise HostError("LAUNCH_BLOCKED")
        elif action == 'native_prepare_preview':
            self._prepare_preview(params)
            if self._rehearsal is not None:
                request_started(self._rehearsal)
        elif action == 'native_commit_preview':
            if self._live_controller is None:
                raise HostError('STALE_NATIVE_REPLY')
            self._live_controller.commit_native_reply(**params)
            if self._rehearsal is not None:
                request_finished(self._rehearsal)
                # The 45-minute clock starts when the first REAL question
                # reaches the candidate, not during API Portal credential setup.
                if self._wall_sample is not None and params.get('reply') is not None:
                    start_on_question_presented(self._rehearsal, self._wall_sample, self._tick,
                        evidence_id=self._live_controller.snapshot()['events'][-1]['id'])
            self.screen = 'LIVE_PREVIEW'
        elif action == 'native_cancel_preview':
            if self._live_controller is not None:
                self._live_controller.cancel_native_reply()
            if self._rehearsal is not None:
                request_finished(self._rehearsal)
        elif action == 'preview_close':
            if self._live_controller is None:
                raise HostError('INVALID_TRANSITION')
            if self._live_controller.phase == 'INTERVIEWING':
                self._live_controller.close()
                self._live_controller.review('preview-host-eligibility-check')
            self.screen = 'LIVE_PREVIEW'
        else:
            raise HostError("INVALID_COMMAND")

    async def _grade_dispatch(self, action, params):
        plan = self._rehearsal
        if (plan is None or plan['status'] != 'ACTIVE' or
                self.screen != 'LIVE_PREVIEW' or self._setup_config is None or
                self._setup_config.technical_environment != 'POSTGRESQL'):
            raise HostError('GRADING_REHEARSAL_ONLY')
        if self._live_controller is not None and self._live_controller.native_pending is not None:
            raise HostError('NATIVE_REQUEST_PENDING')
        if self._live_controller is None:
            raise HostError('GRADING_NOT_READY')
        current_index = plan['current_index']
        qhash = plan['questions'][current_index]['content_sha256']
        candidate = self._last_implementation()
        candidate_text = candidate['payload']['text']
        candidate_id = candidate['id']
        sql_sha = hashlib.sha256(candidate_text.encode('utf-8')).hexdigest()
        previous = self._active_grade_receipt()
        if previous is not None and previous.get('correctness') == 'VERIFIED_LOCAL_FIXTURE':
            raise HostError('QUESTION_ALREADY_GRADED')
        if action == 'grade_inspect':
            try:
                review = inspect_binding(params['fixture_json'], qhash, candidate_id, sql_sha, current_index)
            except (GradingBindingError, AccuracyError) as error:
                raise HostError(error.code) from None
            self._grading_review = review
            return
        review = self._grading_review
        if (review is None or review['fixture_sha256'] != params['fixture_sha256'] or
                review['question_sha256'] != qhash or review['candidate_event_id'] != candidate_id or
                review['candidate_sql_sha256'] != sql_sha or review['question_index'] != current_index):
            raise HostError('STALE_OR_UNAPPROVED_GRADE')
        # A real execution occurs exactly once, on the human-confirmed command.
        # During deterministic replay, only the previously saved observation is
        # committed: opening the App can never launch PostgreSQL or change grades.
        observation = self._replay_observation
        if observation is None:
            try:
                pg_config = find_approved_pg_config()
                receipt = grade_fixture(review['fixture_json'].encode('utf-8'), candidate_text,
                                        params['fixture_sha256'], pg_config=pg_config)
            except (GradingBindingError, AccuracyError) as error:
                receipt = {'correctness': 'NOT_VERIFIED', 'result': {'status': 'NOT_VERIFIED',
                           'error_code': error.code}, 'source': 'LOCAL_GRADER_UNAVAILABLE',
                           'fixture_sha256': review['fixture_sha256'],
                           'question_sha256': qhash, 'candidate_sql_sha256': sql_sha,
                           'official_hidden_tests': False, 'passed_fixtures': 0,
                           'total_approved_fixtures': 0}
            end_tick = max(self._tick, self._clock_offset + self._clock() - self._origin)
            end_wall = round(self._wall_clock(), 6)
            observation = {'result': receipt, 'finished_tick_seconds': end_tick,
                           'finished_wall_seconds': end_wall}
        try:
            verify_grade_receipt(observation, review)
        except GradingBindingError as error:
            raise HostError(error.code) from None
        # Record time actually spent executing: it is not exempt from 45 minutes.
        end_tick = observation['finished_tick_seconds']
        end_wall = observation['finished_wall_seconds']
        if end_tick < self._tick or end_wall < (self._wall_sample or 0) - 2:
            raise HostError('GRADING_CLOCK_INTEGRITY_HOLD')
        self._tick = end_tick
        self._wall_sample = end_wall
        if plan.get('timing') is not None:
            timed = advance_rehearsal_time(plan, end_wall, end_tick)
            if timed in ('TIMEOUT', 'CLOCK_HOLD'):
                # Fail closed: even a PASS from PostgreSQL cannot become a
                # counted grade after the deadline. Preserve time outcome.
                self._end_rehearsal_due_to_time(timed == 'CLOCK_HOLD')
                self._grading_observation = observation
                return
        receipt = copy.deepcopy(observation['result'])
        receipt.update({'candidate_event_id': candidate_id, 'question_index': current_index,
                        'approval_kind': 'NATIVE_HUMAN_CONFIRMATION',
                        'grade_evidence_source': 'LOCAL_POSTGRESQL_OR_TYPED_FAILURE'})
        plan.setdefault('grades', {})[str(current_index)] = receipt
        time_event(plan, 'SQL_GRADE_EXECUTED', evidence_id=candidate_id)
        self._grading_observation = observation

    def _prepare_preview(self, params):
        root = Path(__file__).resolve().parents[1]
        mechanism = (self._setup_config.interviewer_mechanism if self._setup_config
                     else 'STRICT_CHALLENGING')
        if params['mechanism'] != mechanism:
            raise HostError('PREVIEW_MECHANISM_MISMATCH')
        operation = params['operation']
        if operation == 'verify':
            if self.screen not in ('API_PORTAL', 'REVIEW', 'LIVE_PREVIEW'):
                raise HostError('INVALID_TRANSITION')
            profile = None
            if self._live_controller is None or self._live_controller.phase != 'INTERVIEWING':
                try:
                    profile = compile_live_profile(root, mechanism)
                except ProfileError as error:
                    raise HostError(str(error)) from None
            if self._live_controller is not None and self._live_controller.phase != 'INTERVIEWING':
                if self.screen not in ('API_PORTAL', 'REVIEW'):
                    raise HostError('PREVIEW_CLOSED')
                if len(self._preview_history) >= 8:
                    raise HostError('PREVIEW_HISTORY_LIMIT')
                self._preview_history.append(self._preview_state())
                self._live_controller = None
                self._live_profile = None
                self._live_question = None
            if self._live_controller is None:
                self._live_profile = profile
                self._live_question = self._selected_preview_question()
                self._live_controller = InterviewController(
                    SessionConfig(session_id=('rehearsal-' + self._instance_id + '-q' + str(self._rehearsal['current_index'] + 1)
                                                if self._rehearsal is not None else
                                                'preview-' + self._instance_id + '-' + str(len(self._preview_history) + 1)),
                                  duration_seconds=86400, max_input_bytes=4096),
                    clock=lambda: self._tick,
                )
                self._live_controller.start_native_preview(self._live_question['statement'], profile)
            if self._live_profile['mechanism'] != mechanism:
                raise HostError('PREVIEW_MECHANISM_MISMATCH')
            if self._live_controller.phase != 'INTERVIEWING':
                raise HostError('PREVIEW_CLOSED')
            policy = {'rule_id': 'S03C_PUBLIC_TASK_ONLY', 'action': 'INTRODUCE_PUBLIC_TASK',
                      'source': 'owner:TIA-S03-C-WITNESS-GRADE-LIVE-OPENAI-BYOK-INTEGRATION',
                      'instructions': 'Introduce the public task and ask for a clarification or plan. '
                                      'Do not solve it, offer hints, claim tests or assign a score.'}
        else:
            if self._live_controller is None or self.screen != 'LIVE_PREVIEW':
                raise HostError('PREVIEW_VERIFICATION_REQUIRED')
            if not self._preview_state()['can_send']:
                raise HostError('PREVIEW_TURN_UNAVAILABLE')
            if self._live_profile['mechanism'] != mechanism:
                raise HostError('PREVIEW_MECHANISM_MISMATCH')
            previous = [e for e in self._live_controller.snapshot()['events'] if e['actor'] == 'candidate']
            answered = sum(e['actor'] == 'interviewer' and e['payload'].get('operation') == 'reply'
                           for e in self._live_controller.snapshot()['events'])
            if len(previous) > answered:
                event = previous[-1]
                if event['kind'] != params['kind'] or event['payload']['text'] != params['text']:
                    raise HostError('RETRY_INPUT_MISMATCH')
            else:
                event = self._live_controller.candidate_action(params['kind'], params['text'])
            if params['kind'] in ('clarify', 'help'):
                try:
                    policy = decide_interaction(root, mechanism,
                        'HELP_REQUESTED' if params['kind'] == 'help' else 'REQUIREMENTS_CHECK',
                        {'phase': self._live_controller.phase, 'candidate_event_id': event['id'],
                         'requirements_unclear': True})
                except ProfileError as error:
                    raise HostError(str(error)) from None
            else:
                policy = {'rule_id': 'S03C_EVIDENCE_ONLY', 'action': 'ASK_FOR_EVIDENCE',
                          'evidence': [event['id']], 'technical': 'NOT_SCORED',
                          'communication': 'OBSERVATION_ONLY'}
        # Policy is host-generated and placed in effective instructions. Candidate
        # text and all problem content remain exclusively in the input data JSON.
        profile = copy.deepcopy(self._live_profile)
        profile['instructions'] += '\nHOST AUTHORIZATION FOR THIS RESPONSE:\n' + json.dumps(policy, sort_keys=True)
        profile['instructions'] += ('\nFollow only this authorized action. DECLINE means politely refuse a hint; '
                                    'DIAGNOSTIC_QUESTION means ask one question about the candidate\'s obstacle, '
                                    'without supplying an answer or SQL technique. CLARIFY means restate '
                                    'the public requirement and reassess understanding (B05).\n')
        # The host has no execution adapter in S03-E1. This is factual runtime
        # provenance, not a candidate-reported result or a model judgment.
        profile['instructions'] += (
            '\nHOST-VERIFIED EXECUTION STATUS: SQL_NOT_RUN; PANDAS_NOT_RUN; '
            'NO_VERIFIED_OUTPUT; NO_CORRECTNESS_SCORE. '
            'Never say or imply that the candidate executed code or observed test output. '
            'Never ask for the *actual observed* output as though an execution occurred. '
            'You MAY ask for predicted/expected output, a dry run, or a proposed test, '
            'explicitly labeled unverified. If the candidate says they ran code '
            'externally, treat that as candidate-reported and unverified. '
            'A candidate SQL submission is text evidence only, not proof of correctness. '
            'If the candidate requests an input/output example, use only examples '
            'present in the approved question, or explicitly describe any newly '
            'constructed example as hypothetical and not an official test. '
            'Do not claim SQL/Pandas correctness or award a score.\n'
        )
        profile['sha256'] = hashlib.sha256(profile['instructions'].encode()).hexdigest()
        candidate = [{'event_id': e['id'], 'kind': e['kind'], 'text': e['payload']['text']}
                     for e in self._live_controller.snapshot()['events'] if e['actor'] == 'candidate']
        dialogue = [{'event_id': e['id'], 'text': e['payload']['text'], 'provenance': e['provenance']}
                    for e in self._live_controller.snapshot()['events']
                    if e['actor'] == 'interviewer' and e['payload'].get('operation') in ('verify', 'reply')]
        # Retain the newest submitted text and recent dialogue. Never let a
        # long history overflow native 16KB input and never silently shrink the
        # candidate's newest message. Full evidence remains in the local journal.
        history_dropped = 0
        while True:
            context = {'context_label': 'UNTRUSTED_PUBLIC_TASK_AND_CANDIDATE_DATA',
                       'question': self._selected_preview_question(),
                       'candidate_events': candidate, 'prior_interviewer_dialogue': dialogue,
                       'history_events_omitted': history_dropped,
                       'execution_status': 'NOT_RUN',
                       'verified_execution_results': [],
                       'interface_language': self.language}
            input_text = json.dumps(context, ensure_ascii=False)
            if len(input_text.encode()) <= 16000:
                break
            if len(dialogue) > 1:
                dialogue.pop(0)
            elif len(candidate) > 1:
                candidate.pop(0)
            elif len(dialogue):
                dialogue.pop(0)
            else:
                raise HostError('NATIVE_INPUT_TOO_LARGE')
            history_dropped += 1
        if len(profile['instructions'].encode()) > 32768:
            raise HostError('NATIVE_INPUT_TOO_LARGE')
        pending = self._live_controller.prepare_native_reply(
            params['request_id'], params['generation'], operation, profile, policy)
        self._prepared_return = {
            'schema_version': 'tia-native-request/v1', 'transaction_id': pending['transaction_id'],
            'request_id': params['request_id'], 'generation': params['generation'],
            'role': 'interviewer', 'instructions': profile['instructions'], 'input': input_text,
            'schema_name': 'tia_interviewer_reply', 'max_output_tokens': 600,
            'prompt_sha256': profile['sha256'], 'source_sha256': profile['source_sha256'],
        }

    async def _restore(self, document):
        if (type(document) is not dict
                or set(document) != {"schema", "protocol", "instance_id", "journal",
                                     "state_sha256", "document_sha256"}
                or document["schema"] != SAVE_SCHEMA or document["protocol"] != PROTOCOL
                or type(document["instance_id"]) is not str
                or not re.fullmatch(r"[0-9a-f]{32}", document["instance_id"])
                or type(document["journal"]) is not list
                or not 1 <= len(document["journal"]) <= MAX_JOURNAL_ENTRIES):
            raise HostError("INVALID_SAVE")
        sealed = dict(document)
        expected = sealed.pop("document_sha256")
        if type(expected) is not str or digest(sealed) != expected:
            raise HostError("INVALID_SAVE")
        self._instance_id = document["instance_id"]
        prior_tick = 0.0
        for item in document["journal"]:
            if (type(item) is not dict
                    or set(item) not in ({"action", "params", "tick_seconds", "outcome"},
                                         {"action", "params", "tick_seconds", "outcome", "wall_seconds"},
                                         {"action", "params", "tick_seconds", "outcome", "wall_seconds", "grade_observation"})
                    or ("wall_seconds" in item and not (type(item["wall_seconds"]) in (int, float)
                         and math.isfinite(item["wall_seconds"]) and 0 <= item["wall_seconds"] <= 10**12))
                    or item['action'] not in MUTATING_COMMANDS
                    or ('grade_observation' in item and item['action'] != 'grade_execute')
                    or (item['action'] == 'grade_execute' and item['outcome'] == 'OK'
                        and 'grade_observation' not in item)
                    or type(item["tick_seconds"]) not in (int, float)
                    or not math.isfinite(item["tick_seconds"])
                    or not prior_tick <= item["tick_seconds"] <= 315360000
                    or type(item["outcome"]) is not str):
                raise HostError("INVALID_SAVE")
            self._tick = item['tick_seconds']
            self._wall_sample = item.get('wall_seconds')
            self._replay_observation = item.get('grade_observation')
            outcome = 'OK'
            try:
                await self._dispatch(item["action"], item["params"])
            except (HostError, SessionError, ModelPortalError) as error:
                outcome = error.code
            if outcome != item['outcome']:
                raise HostError('INVALID_SAVE')
            prior_tick = self._tick
            self._replay_observation = None
        if self._state_digest() != document["state_sha256"]:
            raise HostError("INVALID_SAVE")
        self._journal = copy.deepcopy(document["journal"])
        self._clock_offset = prior_tick
        self._origin = self._clock()
        self._saved = True
        # E2 reconciles process downtime before accepting another candidate/model
        # action. Within <1 second, avoid gratuitous save churn after restart.
        if self._rehearsal is not None and self._rehearsal['status'] == 'ACTIVE' and self._rehearsal.get('timing'):
            downtime = self._wall_clock() - self._rehearsal['timing']['last_wall_seconds']
            if downtime >= 1.0 or downtime < -2.0:
                await self.command('rehearsal_tick', {})
        # Pending native work never survives restart. Cancellation is journalled;
        # the time until restart remains in the per-question wait bucket.
        if self._live_controller and self._live_controller.native_pending is not None:
            await self.command('native_cancel_preview', {})

    def _persist(self):
        document = {
            "schema": SAVE_SCHEMA, "protocol": PROTOCOL, "instance_id": self._instance_id,
            "journal": self._journal, "state_sha256": self._state_digest(),
        }
        document["document_sha256"] = digest(document)
        self.store.write(document)
        self._saved = True

    def export(self):
        if self._recovery_error == "INVALID_SAVE":
            raise HostError("RECOVERY_REQUIRED")
        result = {
            "schema": "tia-tutorial-export/v1",
            "provenance": "SIMULATED_TUTORIAL",
            "clock_basis": "active_host_process_seconds; not performance evidence",
            "question": copy.deepcopy(QUESTION),
            "session": self.controller.snapshot() if self.controller else None,
            "trainer_preview": copy.deepcopy(self.trainer_preview),
            "execution_status": "NOT_RUN", "api_requests": 0,
            "save_status": "UNAVAILABLE" if self._recovery_error else "AVAILABLE",
            "contains_personal_input": bool(self._candidate_events() or self.setup_questions),
            "privacy": "Explicit local export; includes your submitted text and code. No credentials.",
            "setup": {
                "configuration": (dict(self._setup_config.snapshot(), status="DRAFT")
                                  if self._setup_config else None),
                "questions": copy.deepcopy(self.setup_questions),
                "practice_question": self._practice_snapshot(),
                "allocation": copy.deepcopy(self.setup_allocation),
                "profiles": copy.deepcopy(self.setup_profiles),
                "blockers": list(self.setup_blockers),
            },
        }
        if self._rehearsal is not None:
            result.update(rehearsal=public_plan(self._rehearsal),
                          evidence_scorecard=build_scorecard(self._rehearsal),
                          communication_evidence=build_communication_evidence(self._rehearsal),
                          grounded_trainer=build_grounded_trainer(self._rehearsal),
                          timing=final_metrics(self._rehearsal),
                          live_preview_history=copy.deepcopy(self._preview_history),
                          provenance=('THREE_QUESTION_REHEARSAL_LOCAL_SQL_VERIFIED'
                                      if public_plan(self._rehearsal)['execution'] == 'SOME_LOCAL_FIXTURES_RUN'
                                      else 'THREE_QUESTION_REHEARSAL_UNSCORED'),
                          contains_personal_input=True)
        if self._live_controller is not None:
            result.update(provenance='TUTORIAL_AND_LIVE_PREVIEW' if self.controller
                          else 'LIVE_CONVERSATIONAL_PREVIEW',
                          live_preview=self._preview_state(),
                          live_preview_history=copy.deepcopy(self._preview_history), api_requests=None,
                          provider_usage_source='Native session memory; failed request counts unavailable after restart',
                          contains_personal_input=bool(result['contains_personal_input']
                              or self._preview_state()['candidate_turns_used']
                              or any(item['candidate_turns_used'] for item in self._preview_history)))
        return result

    async def command(self, action, params):
        self._validate_command(action, params)
        self._prepared_return = None
        if action == "snapshot":
            return self.state()
        if action == "reset":
            self.store.delete()
            self._reset_memory()
            self._journal = []
            self._saved = False
            self._recovery_error = None
            self._instance_id = uuid.uuid4().hex
            self._origin = self._clock()
            self._clock_offset = self._tick = 0.0
            return self.state()
        if action == "export":
            return self.export()
        if self._recovery_error:
            raise HostError("RECOVERY_REQUIRED")
        if len(self._journal) >= MAX_JOURNAL_ENTRIES:
            raise HostError("HISTORY_LIMIT")
        if action == 'native_prepare_preview' and len(self._journal) >= MAX_JOURNAL_ENTRIES - 1:
            # Keep one durable slot for a cancellation if the process exits while
            # native HTTP is pending; recovery must never create an unreadable save.
            raise HostError('HISTORY_LIMIT')
        self._tick = max(self._tick, self._clock_offset + self._clock() - self._origin)
        # The sample is written into the journal and used for deterministic
        # replay. No renderer-provided clock or timestamp is accepted.
        self._wall_sample = round(self._wall_clock(), 6)
        started_tick, started_wall = self._tick, self._wall_sample
        self._grading_observation = None
        before = self._state_digest()
        outcome = "OK"
        caught = None
        try:
            await self._dispatch(action, params)
        except (HostError, SessionError, ModelPortalError) as error:
            caught = error
            outcome = error.code
        # Preserve already committed candidate evidence even if a bounded provider
        # response fails or the S02 host closes an expired session.
        changed = self._state_digest() != before
        # Avoid filling the bounded journal with empty timer polls.
        if (caught is None and action != 'rehearsal_tick') or changed:
            entry = {'action': action, 'params': copy.deepcopy(params),
                     'tick_seconds': started_tick, 'wall_seconds': started_wall,
                     'outcome': outcome}
            if action == 'grade_execute' and self._grading_observation is not None:
                # On replay only the persisted, source-bound observation is used.
                entry['grade_observation'] = copy.deepcopy(self._grading_observation)
            self._journal.append(entry)
            try:
                self._persist()
            except SaveError:
                self._saved = False
                self._recovery_error = "SAVE_UNAVAILABLE"
                raise
        if caught:
            raise caught
        return self.state()

    async def handle(self, request):
        request_id = None
        try:
            if (type(request) is not dict or set(request) != {"id", "action", "params"}
                    or type(request["id"]) is not str
                    or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", request["id"])):
                raise HostError("INVALID_REQUEST")
            request_id = request["id"]
            result = await self.command(request["action"], request["params"])
            if request["action"] == "export":
                return {"id": request_id, "ok": True, "state": self.state(), "export": result}
            if request['action'] == 'native_prepare_preview':
                return {'id': request_id, 'ok': True, 'state': result,
                        'prepared': copy.deepcopy(self._prepared_return)}
            return {"id": request_id, "ok": True, "state": result}
        except (HostError, SessionError, ModelPortalError, SaveError) as error:
            return {"id": request_id, "ok": False, "state": self.state(), "error": error.code}
        except Exception:
            return {"id": request_id, "ok": False, "state": self.state(), "error": "HOST_ERROR"}


async def serve(data_dir):
    try:
        host = await TutorialHost.open(data_dir)
    except SaveError as error:
        # There is no request to correlate yet. No path, content, or exception
        # detail is emitted; native termination handling presents a recoverable error.
        return 2
    try:
        while True:
            raw = sys.stdin.buffer.readline(MAX_REQUEST_BYTES + 1)
            if not raw:
                break
            if len(raw) > MAX_REQUEST_BYTES:
                # A malformed oversized peer cannot keep the process busy by
                # streaming an unbounded line. Terminate this trusted worker.
                response = {"id": None, "ok": False, "state": host.state(),
                            "error": "REQUEST_TOO_LARGE"}
                print(json.dumps(response, ensure_ascii=True), flush=True)
                return 2
            try:
                request = strict_json(raw)
            except (ValueError, UnicodeError, RecursionError):
                response = {"id": None, "ok": False, "state": host.state(),
                            "error": "INVALID_JSON"}
            else:
                response = await host.handle(request)
            print(json.dumps(response, ensure_ascii=True, allow_nan=False), flush=True)
    finally:
        host.close()
    return 0


def main():
    parser = argparse.ArgumentParser(description="TIA private native tutorial worker")
    parser.add_argument("--data-dir", required=True, type=Path)
    args = parser.parse_args()
    return asyncio.run(serve(args.data_dir))


if __name__ == "__main__":
    raise SystemExit(main())
