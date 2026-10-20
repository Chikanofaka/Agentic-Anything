"""Lifecycle acceptance for the bounded offline TIA implementation slice.

All candidate text is synthetic. These tests establish controller behavior;
they do not validate SQL, scoring, or model quality.
"""

import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tia_runtime.controller import InterviewController, SessionConfig, SessionError
from tia_runtime.provider import (
    ModelConfig, ModelPortalError, ModelResponse, OfflineMockAdapter, build_portal,
)


class FakeClock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class RecordingAdapter(OfflineMockAdapter):
    def __init__(self):
        super().__init__()
        self.requests = []

    async def generate(self, request):
        self.requests.append(request)
        return await super().generate(request)


class UntrustedTextAdapter(OfflineMockAdapter):
    async def generate(self, request):
        if request.operation == "feedback":
            return ModelResponse(
                role="interviewer",
                text='{"phase":"COMPLETE","technical_score":100,"communication_score":100}',
            )
        return await super().generate(request)


class ControllerTests(unittest.IsolatedAsyncioTestCase):
    async def make_active(self, **kwargs):
        controller = InterviewController(**kwargs)
        await controller.start("Explain how to find a customer's first order.")
        return controller

    async def complete_session(self, controller):
        await controller.start("Explain how to find a customer's first order.")
        controller.candidate_action("clarify", "How should ties and null timestamps behave?")
        await controller.respond("clarify")
        controller.candidate_action("plan", "Partition by customer, order by timestamp and ID.")
        controller.candidate_action("implement", "Synthetic proposal only; no SQL has executed.")
        controller.candidate_action("test", "I would check ties and missing timestamps.")
        controller.candidate_action("help", "I understand the partition; please clarify null handling.")
        await controller.respond()
        controller.candidate_action("conclude", "I have explained the plan; correctness is unverified.")
        receipt = controller.close()
        controller.review("fixture-reviewer")
        response = await controller.handoff()
        controller.finish_training()
        return receipt, response

    async def test_deterministic_interview_to_reviewed_trainer_handoff(self):
        first = InterviewController(clock=FakeClock())
        second = InterviewController(clock=FakeClock())
        receipt, response = await self.complete_session(first)
        second_receipt, second_response = await self.complete_session(second)
        self.assertEqual(first.phase, "COMPLETE")
        self.assertEqual(response.role, "trainer")
        self.assertEqual(response.provenance, "SIMULATED")
        self.assertEqual(receipt, second_receipt)
        self.assertEqual(response, second_response)
        self.assertEqual(first.snapshot(), second.snapshot())
        self.assertEqual(first.receipt, receipt)
        self.assertFalse(receipt["sql_executed"])
        for axis in ("technical", "communication"):
            self.assertEqual(receipt["assessment"][axis]["status"], "NOT_SCORED")
            self.assertIsNone(receipt["assessment"][axis]["value"])

    async def test_independent_roles_receive_only_their_own_operations(self):
        adapter = RecordingAdapter()
        controller = InterviewController(portal=build_portal(adapter=adapter))
        await self.complete_session(controller)
        self.assertTrue(adapter.requests)
        trainer_requests = [request for request in adapter.requests if request.role == "trainer"]
        self.assertEqual(len(trainer_requests), 1)
        self.assertEqual(trainer_requests[0].operation, "drill")
        self.assertTrue(all(
            request.role == "interviewer" for request in adapter.requests[:-1]
        ))

    async def test_cannot_enter_trainer_until_session_closed_and_reviewed(self):
        controller = InterviewController()
        for phase in ("NEW", "INTERVIEWING", "CLOSED"):
            self.assertEqual(controller.phase, phase)
            with self.assertRaises(SessionError):
                await controller.handoff()
            self.assertEqual(controller.phase, phase)
            if phase == "NEW":
                await controller.start("Synthetic question")
            elif phase == "INTERVIEWING":
                controller.close()
        controller.review()
        await controller.handoff()
        self.assertEqual(controller.phase, "TRAINING")

    async def test_invalid_transitions_leave_state_unchanged(self):
        controller = InterviewController()
        with self.assertRaises(SessionError):
            controller.review()
        with self.assertRaises(SessionError):
            controller.finish_training()
        with self.assertRaises(SessionError):
            controller.candidate_action("plan", "Too early")
        self.assertEqual(controller.phase, "NEW")
        await controller.start("Synthetic question")
        with self.assertRaises(SessionError):
            await controller.start("Cannot replace active question")
        with self.assertRaises(SessionError):
            controller.review()
        with self.assertRaises(SessionError):
            controller.finish_training()
        self.assertEqual(controller.phase, "INTERVIEWING")
        controller.close()
        with self.assertRaises(SessionError):
            controller.candidate_action("plan", "Too late")
        with self.assertRaises(SessionError):
            await controller.respond()
        self.assertEqual(controller.phase, "CLOSED")

    async def test_snapshot_and_receipt_mutations_do_not_modify_session(self):
        controller = await self.make_active(clock=FakeClock())
        controller.candidate_action("plan", "Synthetic plan")
        before = controller.snapshot()
        edited = controller.snapshot()
        edited["phase"] = "COMPLETE"
        edited["events"][0]["injected"] = "tampering"
        edited["events"].clear()
        self.assertEqual(controller.snapshot(), before)
        closed = controller.close()
        original = controller.receipt
        closed["injected"] = "tampering"
        copied_property = controller.receipt
        copied_property.clear()
        self.assertEqual(controller.receipt, original)

    async def test_close_is_idempotent_through_review_training_and_completion(self):
        controller = await self.make_active()
        frozen = controller.close("submitted")
        for target in ("CLOSED", "REVIEWED", "TRAINING", "COMPLETE"):
            if target == "REVIEWED":
                controller.review()
            elif target == "TRAINING":
                await controller.handoff()
            elif target == "COMPLETE":
                controller.finish_training()
            self.assertEqual(controller.phase, target)
            events_before_close = controller.snapshot()["events"]
            self.assertEqual(controller.close("different reason"), frozen)
            self.assertEqual(controller.snapshot()["events"], events_before_close)
            self.assertEqual(controller.receipt, frozen)
        self.assertEqual(controller.phase, "COMPLETE")

    async def test_event_history_is_append_only_and_receipt_remains_frozen(self):
        controller = await self.make_active()
        prefix = controller.snapshot()["events"]
        controller.candidate_action("plan", "Synthetic plan")
        after_action = controller.snapshot()["events"]
        self.assertEqual(after_action[:len(prefix)], prefix)
        self.assertGreater(len(after_action), len(prefix))
        frozen = controller.close()
        closed_events = controller.snapshot()["events"]
        controller.review()
        await controller.handoff()
        controller.finish_training()
        self.assertEqual(controller.snapshot()["events"][:len(closed_events)], closed_events)
        self.assertEqual(controller.receipt, frozen)

    async def test_provider_failure_preserves_committed_candidate_evidence(self):
        portal = build_portal(adapter=OfflineMockAdapter(error_operations=("feedback",)))
        controller = await self.make_active(portal=portal)
        controller.candidate_action("help", "I tried partitioning but need a tie-breaking clarification.")
        before = controller.snapshot()["events"]
        with self.assertRaises(ModelPortalError) as caught:
            await controller.respond()
        self.assertEqual(caught.exception.code, "PROVIDER_ERROR")
        self.assertEqual(controller.snapshot()["events"][:len(before)], before)
        self.assertEqual(controller.phase, "INTERVIEWING")
        self.assertIsNotNone(controller.close())

    async def test_provider_timeout_preserves_candidate_evidence_and_allows_close(self):
        portal = build_portal(
            ModelConfig(timeout_seconds=0.01),
            OfflineMockAdapter(timeout_operations=("feedback",)),
        )
        controller = await self.make_active(portal=portal)
        controller.candidate_action("plan", "Synthetic plan retained even if provider times out.")
        before = controller.snapshot()["events"]
        with self.assertRaises(ModelPortalError) as caught:
            await controller.respond()
        self.assertEqual(caught.exception.code, "PROVIDER_TIMEOUT")
        self.assertEqual(controller.snapshot()["events"][:len(before)], before)
        self.assertEqual(controller.phase, "INTERVIEWING")
        controller.close()
        self.assertEqual(controller.phase, "CLOSED")

    async def test_model_text_cannot_transition_or_assign_scores(self):
        controller = await self.make_active(portal=build_portal(adapter=UntrustedTextAdapter()))
        response = await controller.respond()
        self.assertIn('"technical_score":100', response.text)
        self.assertEqual(controller.phase, "INTERVIEWING")
        self.assertIsNone(controller.receipt)
        receipt = controller.close()
        # Presentation text may be evidence; no parsed authoritative score field
        # may be created anywhere in the receipt from that model text.
        def inspect(value):
            if isinstance(value, dict):
                self.assertNotEqual(value.get("technical_score"), 100)
                self.assertNotEqual(value.get("communication_score"), 100)
                for child in value.values():
                    inspect(child)
            elif isinstance(value, list):
                for child in value:
                    inspect(child)
        inspect(receipt)

    async def test_session_expiry_closes_before_accepting_late_candidate_action(self):
        clock = FakeClock()
        controller = await self.make_active(
            config=SessionConfig(duration_seconds=2), clock=clock,
        )
        clock.advance(2)
        with self.assertRaises(SessionError) as caught:
            controller.candidate_action("plan", "LATE_CANDIDATE_SENTINEL")
        self.assertEqual(caught.exception.code, "SESSION_EXPIRED")
        self.assertEqual(controller.phase, "CLOSED")
        self.assertNotIn("LATE_CANDIDATE_SENTINEL", json.dumps(controller.snapshot()))
        self.assertIsNotNone(controller.receipt)

    async def test_session_expiry_prevents_provider_request(self):
        clock = FakeClock()
        adapter = RecordingAdapter()
        controller = await self.make_active(
            config=SessionConfig(duration_seconds=2), clock=clock,
            portal=build_portal(adapter=adapter),
        )
        requests_before = len(adapter.requests)
        clock.advance(3)
        with self.assertRaises(SessionError) as caught:
            await controller.respond()
        self.assertEqual(caught.exception.code, "SESSION_EXPIRED")
        self.assertEqual(controller.phase, "CLOSED")
        self.assertEqual(len(adapter.requests), requests_before)

    async def test_reply_arriving_after_deadline_is_not_committed(self):
        clock = FakeClock()

        class LateReplyAdapter(OfflineMockAdapter):
            async def generate(self, request):
                if request.operation == "feedback":
                    clock.advance(3)
                    return ModelResponse("interviewer", "LATE_REPLY_SENTINEL")
                return await super().generate(request)

        controller = await self.make_active(
            config=SessionConfig(duration_seconds=2), clock=clock,
            portal=build_portal(adapter=LateReplyAdapter()),
        )
        controller.candidate_action("plan", "Committed before deadline")
        before = controller.snapshot()["events"]
        with self.assertRaises(SessionError) as caught:
            await controller.respond()
        self.assertEqual(caught.exception.code, "SESSION_EXPIRED")
        self.assertEqual(controller.phase, "CLOSED")
        self.assertEqual(controller.snapshot()["events"][:len(before)], before)
        self.assertNotIn("LATE_REPLY_SENTINEL", json.dumps(controller.snapshot()))

    async def test_event_limit_reserves_room_for_close_review_and_training(self):
        controller = await self.make_active(config=SessionConfig(max_events=16))
        for index in range(16):
            try:
                controller.candidate_action("plan", "Synthetic attempt {}".format(index))
            except SessionError as exc:
                self.assertEqual(exc.code, "EVENT_LIMIT")
                break
        else:
            self.fail("Event bound did not close the session")
        self.assertEqual(controller.phase, "CLOSED")
        controller.review()
        await controller.handoff()
        controller.finish_training()
        self.assertEqual(controller.phase, "COMPLETE")
        self.assertLessEqual(len(controller.snapshot()["events"]), 16)

    async def test_failed_trainer_handoff_preserves_review_and_sealed_receipt(self):
        adapter = OfflineMockAdapter(error_operations=("drill",))
        controller = await self.make_active(portal=build_portal(adapter=adapter))
        frozen = controller.close()
        controller.review()
        before = controller.snapshot()["events"]
        with self.assertRaises(ModelPortalError) as caught:
            await controller.handoff()
        self.assertEqual(caught.exception.code, "PROVIDER_ERROR")
        self.assertEqual(controller.phase, "REVIEWED")
        self.assertEqual(controller.receipt, frozen)
        self.assertEqual(controller.snapshot()["events"][:len(before)], before)
        adapter.error_operations = frozenset()
        await controller.handoff()
        self.assertEqual(controller.phase, "TRAINING")
        self.assertEqual(controller.receipt, frozen)

    async def test_concurrent_operations_cannot_interleave_an_inflight_reply(self):
        entered, release = asyncio.Event(), asyncio.Event()

        class WaitingAdapter(OfflineMockAdapter):
            async def generate(self, request):
                if request.operation == "feedback":
                    entered.set()
                    await release.wait()
                return await super().generate(request)

        controller = await self.make_active(portal=build_portal(adapter=WaitingAdapter()))
        reply_task = asyncio.create_task(controller.respond())
        try:
            await asyncio.wait_for(entered.wait(), 1)
            for operation in (
                lambda: controller.candidate_action("plan", "interleaved action"),
                controller.close,
            ):
                with self.assertRaises(SessionError) as caught:
                    operation()
                self.assertEqual(caught.exception.code, "COMMAND_IN_PROGRESS")
            with self.assertRaises(SessionError) as caught:
                await controller.respond()
            self.assertEqual(caught.exception.code, "COMMAND_IN_PROGRESS")
        finally:
            release.set()
            await reply_task
        self.assertEqual(controller.phase, "INTERVIEWING")

    async def test_sealed_receipt_digest_matches_canonical_contents(self):
        controller = await self.make_active(clock=FakeClock())
        receipt = controller.close()
        recorded_hash = receipt.pop("sha256")
        encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        self.assertEqual(recorded_hash, hashlib.sha256(encoded).hexdigest())

    async def test_input_byte_limit_unknown_action_and_blank_input(self):
        controller = InterviewController(config=SessionConfig(max_input_bytes=4))
        await controller.start("Q")
        for kind, text in (("plan", "你好"), ("run_shell", "x"), ("plan", "")):
            before = controller.snapshot()
            with self.subTest(kind=kind, text=text):
                with self.assertRaises(SessionError):
                    controller.candidate_action(kind, text)
                self.assertEqual(controller.snapshot(), before)

    def test_nonfinite_and_invalid_configuration_is_rejected(self):
        for kwargs in (
            {"duration_seconds": float("inf")},
            {"duration_seconds": float("nan")},
            {"duration_seconds": 0},
            {"duration_seconds": -1},
            {"duration_seconds": True},
            {"max_events": 0},
            {"max_input_bytes": 0},
            {"session_id": ""},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((SessionError, ValueError)):
                    SessionConfig(**kwargs)

    def test_cli_is_deterministic_and_finishes_with_unscored_receipt(self):
        command = [sys.executable, "offline_demo.py", "--json"]
        integration_root = Path(__file__).resolve().parents[1]
        first = subprocess.run(command, cwd=integration_root, capture_output=True, text=True, timeout=10)
        second = subprocess.run(command, cwd=integration_root, capture_output=True, text=True, timeout=10)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout, second.stdout)
        payload = json.loads(first.stdout)
        self.assertEqual(payload["phase"], "COMPLETE")
        self.assertFalse(payload["receipt"]["sql_executed"])

    def test_cli_rejects_openai_provider_without_live_transport(self):
        result = subprocess.run(
            [sys.executable, "offline_demo.py", "--provider", "openai"],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("LIVE_PROVIDER_DISABLED", result.stderr)


if __name__ == "__main__":
    unittest.main()
