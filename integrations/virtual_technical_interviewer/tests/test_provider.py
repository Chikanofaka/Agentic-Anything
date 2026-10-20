"""Executable checks of the offline adapter's data and failure boundaries."""

import asyncio
import dataclasses
import unittest

from tia_runtime.provider import (
    FutureOpenAIAdapter,
    ModelConfig,
    ModelPortalError,
    ModelRequest,
    ModelResponse,
    OfflineMockAdapter,
    build_portal,
)


class FixedAdapter:
    def __init__(self, result):
        self.result = result

    async def generate(self, request):
        return self.result


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_default_is_offline_and_all_operations_are_deterministic(self):
        portal = build_portal()
        self.assertEqual(portal.config.provider, "offline_mock")
        for operation in ("brief", "clarify", "feedback", "close", "drill"):
            role = "trainer" if operation == "drill" else "interviewer"
            request = ModelRequest(role, operation, {"session_id": "synthetic"})
            first = await portal.request(request)
            self.assertEqual(first, await portal.request(request))
            self.assertEqual(first.role, role)
            self.assertEqual(first.provenance, "SIMULATED")
            self.assertTrue(first.text)

    async def test_unknown_operation_and_role_operation_mismatch_rejected(self):
        for request, code in (
            (ModelRequest("interviewer", "grade"), "UNKNOWN_OPERATION"),
            (ModelRequest("trainer", "brief"), "INVALID_REQUEST"),
            (ModelRequest("interviewer", "drill"), "INVALID_REQUEST"),
        ):
            with self.subTest(request=request):
                with self.assertRaises(ModelPortalError) as raised:
                    await build_portal().request(request)
                self.assertEqual(raised.exception.code, code)

    async def test_live_providers_fail_closed_without_calling_adapter(self):
        class MustNotRun:
            async def generate(self, request):
                raise AssertionError("A disabled provider was invoked")

        for provider in ("openai", "anthropic", "https://example.invalid", "mock"):
            with self.subTest(provider=provider):
                with self.assertRaises(ModelPortalError) as raised:
                    build_portal(ModelConfig(provider=provider), MustNotRun())
                self.assertEqual(raised.exception.code, "LIVE_PROVIDER_DISABLED")
        with self.assertRaises(ModelPortalError) as raised:
            build_portal(adapter=FutureOpenAIAdapter())
        self.assertEqual(raised.exception.code, "LIVE_PROVIDER_DISABLED")
        with self.assertRaises(ModelPortalError) as raised:
            await FutureOpenAIAdapter().generate(ModelRequest("interviewer", "brief"))
        self.assertEqual(raised.exception.code, "LIVE_PROVIDER_DISABLED")

    async def test_timeout_is_real_and_cancels_pending_generation(self):
        class CancellableAdapter:
            def __init__(self):
                self.cancelled = False

            async def generate(self, request):
                try:
                    await asyncio.Event().wait()
                finally:
                    self.cancelled = True

        adapter = CancellableAdapter()
        with self.assertRaises(ModelPortalError) as raised:
            await build_portal(ModelConfig(timeout_seconds=0.01), adapter).request(
                ModelRequest("interviewer", "brief")
            )
        self.assertEqual(raised.exception.code, "PROVIDER_TIMEOUT")
        self.assertTrue(adapter.cancelled)

    async def test_fixture_timeout_and_error_controls(self):
        for adapter, code in (
            (OfflineMockAdapter(timeout_operations=("brief",)), "PROVIDER_TIMEOUT"),
            (OfflineMockAdapter(error_operations=("brief",)), "PROVIDER_ERROR"),
        ):
            with self.subTest(code=code):
                with self.assertRaises(ModelPortalError) as raised:
                    await build_portal(ModelConfig(timeout_seconds=0.01), adapter).request(
                        ModelRequest("interviewer", "brief")
                    )
                self.assertEqual(raised.exception.code, code)

    async def test_provider_error_does_not_echo_exception_contents(self):
        class SensitiveFailure:
            async def generate(self, request):
                raise RuntimeError("SYNTHETIC_SENSITIVE_TOKEN /private/user/transcript")

        with self.assertRaises(ModelPortalError) as raised:
            await build_portal(adapter=SensitiveFailure()).request(
                ModelRequest("interviewer", "brief")
            )
        self.assertEqual(str(raised.exception), "PROVIDER_ERROR")
        self.assertNotIn("SENSITIVE", str(raised.exception))
        self.assertTrue(raised.exception.__suppress_context__)

    async def test_invalid_outputs_cannot_set_score_state_or_wrong_role(self):
        injected = ModelResponse("interviewer", "message")
        object.__setattr__(injected, "score", 100)
        invalid = (
            {"role": "interviewer", "text": "message", "score": 100},
            {"role": "interviewer", "text": "message", "state": "COMPLETED"},
            injected,
            ModelResponse("trainer", "wrong role"),
            ModelResponse("interviewer", ""),
            ModelResponse("interviewer", "   "),
            ModelResponse("interviewer", "x" * 2001),
            ModelResponse("interviewer", 42),
            ModelResponse("interviewer", "message", "REAL"),
            None,
        )
        for result in invalid:
            with self.subTest(result=result):
                with self.assertRaises(ModelPortalError) as raised:
                    await build_portal(adapter=FixedAdapter(result)).request(
                        ModelRequest("interviewer", "brief")
                    )
                self.assertEqual(raised.exception.code, "INVALID_RESPONSE")

    async def test_valid_output_text_stays_text_even_if_it_requests_a_score(self):
        text = '{"score":100,"state":"COMPLETED"}'
        result = await build_portal(adapter=FixedAdapter(
            ModelResponse("interviewer", text)
        )).request(ModelRequest("interviewer", "brief"))
        self.assertEqual(result.text, text)
        self.assertEqual(set(dataclasses.asdict(result)), {"role", "text", "provenance"})

    async def test_bad_request_rejected_before_adapter(self):
        for request in (
            {}, ModelRequest("system", "brief"), ModelRequest("interviewer", ""),
            ModelRequest("interviewer", "x" * 65),
            ModelRequest("interviewer", "brief", []),
            ModelRequest("interviewer", "brief", {"invalid": object()}),
            ModelRequest("interviewer", "brief", {"invalid": float("nan")}),
        ):
            with self.subTest(request=request):
                with self.assertRaises(ModelPortalError) as raised:
                    await build_portal().request(request)
                self.assertEqual(raised.exception.code, "INVALID_REQUEST")

    def test_config_rejects_nonfinite_nonpositive_and_wrong_types(self):
        for timeout in (0, -1, float("nan"), float("inf"), True, "1", None, 10 ** 1000):
            with self.subTest(timeout=timeout):
                with self.assertRaises(ModelPortalError) as raised:
                    ModelConfig(timeout_seconds=timeout)
                self.assertEqual(raised.exception.code, "INVALID_CONFIG")
        for limit in (0, -1, True, 1.5):
            with self.subTest(limit=limit):
                with self.assertRaises(ModelPortalError):
                    ModelConfig(max_response_chars=limit)
        with self.assertRaises(TypeError):
            ModelConfig(api_key="SYNTHETIC_DISALLOWED_CREDENTIAL_FIELD")


if __name__ == "__main__":
    unittest.main()
