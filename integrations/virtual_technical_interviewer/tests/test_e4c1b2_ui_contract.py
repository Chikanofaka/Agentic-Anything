"""C1B.2 test-only UI paths and isolation invariants (real App runs on Mac)."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class C1B2MockUIContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / 'native/main.swift').read_text()
        cls.smoke = (ROOT / 'native/UISmoke.swift').read_text()
        cls.verifier = (ROOT / 'scripts/verify_preparer_ui.py').read_text()
        cls.provider = (ROOT / 'native/ProviderTests.swift').read_text()

    def test_testing_flag_is_isolated_from_live_network(self):
        self.assertIn('CommandLine.arguments.contains("--ui-preparer-test")', self.app)
        self.assertIn('TIATestHTTPProtocol.configuration()', self.app)

    def test_only_synthetic_proposal_queued_for_mock_transport(self):
        self.assertIn('TIATestHTTPProtocol.enqueue([.reply(text, usage:', self.app)
        self.assertIn('C1B2-PRIVATE-REFERENCE', self.app)

    def test_native_consent_has_cancel_and_allow(self):
        self.assertIn('resolvePreparerConsentForTest(approve: Bool)', self.app)
        self.assertIn('alert.informativeText.contains("Prepare 3 reviewed questions")', self.app)
        self.assertIn('approve ? .alertFirstButtonReturn : .alertSecondButtonReturn', self.app)

    def test_browser_cannot_forcibly_approve(self):
        self.assertIn('app.resolvePreparerConsentForTest(approve: approved)', self.smoke)
        self.assertIn('C1B2 native confirmation is required before any HTTP', self.smoke)

    def test_ui_checks_cancel_and_seal(self):
        self.assertIn('C1B2 cancellation preserves no-request', self.smoke)
        self.assertIn('C1B2 model result is sealed', self.smoke)
        self.assertIn('native_private_preparer?.status', self.smoke)

    def test_ui_checks_no_duplicate_charge_and_disconnect(self):
        self.assertIn('C1B2 second attempt is rejected without a second charge', self.smoke)
        self.assertIn('C1B2 disconnect clears private memory', self.smoke)

    def test_receipts_cannot_contain_reference(self):
        self.assertIn('if \'C1B2-PRIVATE-REFERENCE\' in text:', self.verifier)
        self.assertIn("'mock_http_requests': 1", self.verifier)

    def test_native_portal_awaiting_consent_never_sends_snapshot(self):
        # The real NSAlert keeps the Native bridge busy until the sheet closes.
        # A fresh `snap()` under the sheet triggers NATIVE_BUSY even when
        # opening the API Portal was successful.
        first = self.smoke.split('Step(label: "C1B2 open Native API portal with zero paid calls"', 1)[1]
        first = first.split('Step(label: "C1B2 credential entered only through Native sheet"', 1)[0]
        self.assertIn('const s=window.tiaState;', first)
        self.assertNotIn('await snap()', first)

    def test_mock_without_real_api_key(self):
        self.assertIn("'--ui-preparer-test'", self.verifier)
        self.assertIn("'real_credentials_used': False", self.verifier)
        self.assertIn('synthetic_credential_fixture_used', self.smoke)

if __name__ == '__main__':
    unittest.main()
