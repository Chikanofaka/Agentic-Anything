"""C1B safety contracts (source-level; Native self-tests/build run separately on Mac)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class NativePreparerPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT / 'native/NativePreparer.swift').read_text()
        cls.app = (ROOT / 'native/main.swift').read_text()
        cls.provider = (ROOT / 'native/OpenAI.swift').read_text()
        cls.bridge = (ROOT / 'native/Bridge.swift').read_text()
        cls.ui = (ROOT / 'ui/app.js').read_text()
        cls.build = (ROOT / 'scripts/build_app.sh').read_text()

    def test_file_compiled_in_mac_bundle(self):
        self.assertIn('"$TIA_ROOT/native/NativePreparer.swift"',self.build)

    def test_preparer_is_separate_provider_role(self):
        self.assertIn('["interviewer", "trainer", "preparer"]',self.provider)
        self.assertIn('"tia_" + role + "_reply"',self.provider)

    def test_preparer_has_explicit_distinct_output_budget(self):
        self.assertIn('role == "preparer" ? 8192 : 600',self.provider)
        self.assertIn('tokens.doubleValue == Double(role == "preparer" ? 8192 : 600)',self.provider)

    def test_no_general_webview_access_to_reference(self):
        self.assertIn('private var privatePreparation: TIAPreparerSeal?',self.app)
        self.assertNotIn('privateRawProposal',self.ui)
        self.assertNotIn('privateRawProposal',self.app)
        self.assertIn('private let privateRawProposal: String',self.native)

    def test_preparer_is_native_permission_controlled(self):
        self.assertIn('"preparer_request"',self.bridge)
        self.assertIn('if action == "preparer_request"',self.app)
        self.assertIn('confirm(notice)',self.app)
        self.assertIn('portal.publicState["live_enabled"] as? Bool == true',self.app)

    def test_preflight_binding_must_be_exact(self):
        self.assertIn('READY_FOR_FUTURE_PRIVATE_PREPARATION',self.native)
        self.assertIn('SOURCE_BOUND_CONFIRMED',self.native)
        self.assertIn('review["content_sha256"] as? String == hash',self.native)
        self.assertIn('hashes.insert(hash).inserted',self.native)

    def test_no_silent_truncation(self):
        self.assertIn('if content.utf8.count > 16000',self.native)
        self.assertIn('TIAPreparerError.inputTooLarge',self.native)
        self.assertNotIn('content.prefix(',self.native)

    def test_strict_model_response_and_wrong_question_rejected(self):
        self.assertIn('StrictJSON.object(data)',self.native)
        self.assertIn('root["question_set_sha256"] as? String == questionSetSHA',self.native)
        self.assertIn('items.count == questionCount',self.native)
        self.assertIn('item["question_sha256"] as? String == source["question_sha256"]',self.native)
        self.assertIn('Set(approach.keys) == Set(',self.native)

    def test_model_will_never_authorize_execution(self):
        self.assertIn('"execution_status": "NOT_RUN"',self.native)
        self.assertIn('"technical": "NOT_SCORED"',self.native)
        self.assertIn('"interviewer_reference_access": false',self.native)
        self.assertIn('Do not claim tests ran',self.app)

    def test_no_model_provider_call_on_review_render(self):
        self.assertIn('() => act("preparer_request", {})',self.ui)
        self.assertNotIn('act("native_commit_preparer"',self.ui)

    def test_no_auto_retry_and_failed_schema_kept_private(self):
        self.assertIn('NO automatic retry',self.app)
        self.assertIn('INVALID_OR_INCOMPLETE_PREPARATION',self.app)
        self.assertIn('self.finishLive(ok: false',self.app)

    def test_cancel_disconnect_fails_closed(self):
        self.assertIn('if liveStage == "preparer_calling"',self.app)
        self.assertIn('privatePreparation = nil; portal.disconnect()',self.app)

    def test_only_safe_status_transmitted(self):
        self.assertIn('state["native_private_preparer"] = privatePreparation?.safeStatus',self.app)
        self.assertNotIn('privateRawProposal',self.bridge)
        self.assertNotIn('privateRawProposal',self.provider)

    def test_preparer_parser_receives_request_role(self):
        self.assertIn('activeResponseRole = spec.role', self.provider)
        self.assertIn('Self.parse(data, status: code, role: role)', self.provider)
        self.assertIn('activeResponseRole = nil', self.provider)

    def test_old_reply_limits_unchanged_for_interviewer_and_trainer(self):
        self.assertIn('role == "preparer" ? 32768 : 2000', self.provider)
        self.assertIn('role == "preparer" ? 65536 : 8000', self.provider)
        self.assertIn('role == "preparer" ? 131072 : 16384', self.provider)

    def test_no_extra_python_journal_permissions(self):
        host=(ROOT/'tia_runtime/app_host.py').read_text()
        self.assertNotIn('native_commit_preparer',host)
        self.assertNotIn('preparer_request',host)

if __name__=='__main__': unittest.main()
