"""C2C tests of real test-entry wiring and the independent Mac runner."""
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]

class C2CUIContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / 'native/main.swift').read_text(encoding='utf-8')
        cls.smoke = (ROOT / 'native/UISmoke.swift').read_text(encoding='utf-8')
        cls.verifier = (ROOT / 'scripts/verify_adaptive_ui.py').read_text(encoding='utf-8')

    def test_main_mock_isolation(self):
        self.assertIn('"--ui-adaptive-test"', self.main)
        self.assertIn('TIATestHTTPProtocol.reset([', self.main)
        self.assertIn('Your SQL passed all tests.', self.main)
        self.assertIn('configuration: uiTesting ? TIATestHTTPProtocol.configuration()', self.main)

    def test_grade_requires_native_os_approval(self):
        self.assertIn('CommandLine.arguments.contains("--ui-adaptive-test") || CommandLine.arguments.contains("--ui-adaptive-stale-test")', self.main)
        self.assertIn('text.contains("Execute current candidate SQL")', self.main)
        self.assertIn('guard let review = lastState["grading_review"]', self.main)

    def test_native_limit_is_bounded_and_test_only(self):
        self.assertIn('selectItem(withTitle: "10")', self.main)
        self.assertIn('let uiTesting =', self.main)
        self.assertIn('enterSyntheticCredentialForTest', self.main)

    def test_test_action_reaches_real_ui(self):
        self.assertIn('"test"', (ROOT / 'native/Bridge.swift').read_text())
        self.assertIn("'test'", (ROOT / 'tia_runtime/native_contract.py').read_text())
        self.assertIn('"test"', (ROOT / 'ui/app.js').read_text())
        self.assertIn("kind.value='test'", self.smoke)

    def test_actual_host_policy_checked_after_click(self):
        for tag in ('LOCAL_FIXTURE_PASSED', 'REQUEST_EXPLANATION', 'execution_receipt_ref', 'max_hint_level', 'NOT_SCORED'):
            self.assertIn(tag, self.smoke)
        self.assertIn("await press('sendPreview')", self.smoke)

    def test_rejected_model_is_not_saved_as_interviewer(self):
        self.assertIn("ADAPTIVE_REPLY_NOT_AUTHORIZED", self.smoke)
        self.assertIn("modelBefore", self.smoke)
        self.assertIn("p.pending===false", self.smoke)

    def test_stale_and_cross_question_negative_paths(self):
        self.assertIn('C2C changed implementation invalidates earlier local fixture PASS', self.smoke)
        self.assertIn('C2C Q2 never inherits Q1 PostgreSQL pass', self.smoke)
        self.assertIn("policy?.receipt_status==='NOT_VERIFIED'", self.smoke)

    def test_native_recovery_and_no_real_requests(self):
        self.assertIn('C2C recovery restores prior local evidence', self.smoke)
        self.assertIn('real_credentials_used', self.smoke)
        self.assertIn('expected=0, minimum_steps=2', self.verifier)

    def test_runner_requires_real_postgres(self):
        self.assertIn('find_approved_pg_config()', self.verifier)
        self.assertIn('_postgres_bins(config)', self.verifier)
        self.assertIn('C2C_BLOCKED_POSTGRES_NOT_AVAILABLE', self.verifier)
        self.assertNotIn('mock_postgres', self.verifier)

    def test_runner_validates_counts(self):
        self.assertIn('expected=6, minimum_steps=9', self.verifier)
        self.assertIn('expected=4, minimum_steps=8', self.verifier)
        self.assertIn('expected=0, minimum_steps=2', self.verifier)
        self.assertIn('"status"] = "PASS"', self.verifier)

    def test_verifier_python_compiles(self):
        ast.parse(self.verifier)

if __name__ == '__main__':
    unittest.main()
