"""S03 tutorial host: native renderer commands are data, not authority.

The S02 InterviewController remains the interview state machine. Wizard state
belongs here, never to JavaScript. Recovery replays a bounded journal through
the same controller with saved clock samples and the deterministic offline
adapter, then verifies the complete result digest. No model or SQL engine runs
during recovery. The clock measures active host-process time, excluding app
downtime; tutorial times are not performance evidence.
"""

import argparse
import asyncio
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time
import uuid

from .controller import InterviewController, SessionConfig, SessionError
from .persistence import SaveError, TutorialStore, strict_json
from .provider import ModelPortalError


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
}
MUTATING_COMMANDS = frozenset(COMMAND_FIELDS) - {"snapshot", "export", "reset"}
SCREENS = ("ENTRY", "WELCOME", "RULES", "QUESTION", "ROOM", "COMPLETE", "API_PORTAL")


class HostError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class TutorialHost:
    def __init__(self, data_dir, clock=None):
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
    async def open(cls, data_dir, clock=None):
        host = cls(data_dir, clock=clock)
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

    def state(self):
        steps = {"WELCOME": 1, "RULES": 2, "QUESTION": 3, "ROOM": 4, "COMPLETE": 5}
        return {
            "screen": self.screen, "language": self.language,
            "tutorial_step": steps.get(self.screen, 0),
            "session": self.controller.snapshot() if self.controller else None,
            "question": copy.deepcopy(QUESTION), "feedback": self.feedback,
            "trainer_preview": copy.deepcopy(self.trainer_preview),
            "execution_status": "NOT_RUN", "model_state": "offline",
            "api_requests": 0, "saved_locally": self._saved,
            "recovery_error": self._recovery_error,
        }

    def _state_digest(self):
        public = self.state()
        # Storage availability is not interview authority or replayed evidence.
        public.pop("saved_locally")
        public.pop("recovery_error")
        return digest(public)

    @staticmethod
    def _validate_command(action, params):
        if (type(action) is not str or action not in COMMAND_FIELDS
                or type(params) is not dict or set(params) != COMMAND_FIELDS[action]):
            raise HostError("INVALID_COMMAND")
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

    def _candidate_events(self):
        if not self.controller:
            return []
        return [event for event in self.controller.snapshot()["events"]
                if event["actor"] == "candidate"]

    async def _dispatch(self, action, params):
        self._validate_command(action, params)
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
        else:
            raise HostError("INVALID_COMMAND")

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
                    or set(item) != {"action", "params", "tick_seconds", "outcome"}
                    or item["action"] not in MUTATING_COMMANDS
                    or type(item["tick_seconds"]) not in (int, float)
                    or not math.isfinite(item["tick_seconds"])
                    or not prior_tick <= item["tick_seconds"] <= 315360000
                    or type(item["outcome"]) is not str):
                raise HostError("INVALID_SAVE")
            self._tick = item["tick_seconds"]
            prior_tick = self._tick
            outcome = "OK"
            try:
                await self._dispatch(item["action"], item["params"])
            except (HostError, SessionError, ModelPortalError) as error:
                outcome = error.code
            if outcome != item["outcome"]:
                raise HostError("INVALID_SAVE")
        if self._state_digest() != document["state_sha256"]:
            raise HostError("INVALID_SAVE")
        self._journal = copy.deepcopy(document["journal"])
        self._clock_offset = prior_tick
        self._origin = self._clock()
        self._saved = True

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
        return {
            "schema": "tia-tutorial-export/v1",
            "provenance": "SIMULATED_TUTORIAL",
            "clock_basis": "active_host_process_seconds; not performance evidence",
            "question": copy.deepcopy(QUESTION),
            "session": self.controller.snapshot() if self.controller else None,
            "trainer_preview": copy.deepcopy(self.trainer_preview),
            "execution_status": "NOT_RUN", "api_requests": 0,
            "save_status": "UNAVAILABLE" if self._recovery_error else "AVAILABLE",
            "contains_personal_input": bool(self._candidate_events()),
            "privacy": "Explicit local export; includes your submitted text and code. No credentials.",
        }

    async def command(self, action, params):
        self._validate_command(action, params)
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
        self._tick = max(self._tick, self._clock_offset + self._clock() - self._origin)
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
        if caught is None or self._state_digest() != before:
            self._journal.append({"action": action, "params": copy.deepcopy(params),
                                  "tick_seconds": self._tick, "outcome": outcome})
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
