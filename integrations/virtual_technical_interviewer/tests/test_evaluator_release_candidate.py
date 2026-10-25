"""E5 private distribution safety gates (no Mac build, signing or publication)."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/private_release_candidate.py'
spec=importlib.util.spec_from_file_location('tia_private_release_test',SCRIPT)
r=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.app=Path(self.temp.name)/'Example.app';(self.app/'Contents/Resources').mkdir(parents=True)
        (self.app/'Contents/Resources/main.js').write_text('const app = true;',encoding='utf-8')
    def test_regular_bundle_without_secrets_scans(self):
        self.assertEqual(r.safety_scan(self.app),1)
    def test_rejects_embedded_live_like_api_key(self):
        (self.app/'Contents/Resources/main.js').write_text('const secret="sk-'+'A'*40+'";',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'POSSIBLE_EMBEDDED_API_SECRET'):
            r.safety_scan(self.app)
    def test_rejects_credential_file(self):
        (self.app/'Contents/Resources/secrets.key').write_text('x')
        with self.assertRaisesRegex(ValueError,'CREDENTIAL_LIKE_FILE_IN_APP'):
            r.safety_scan(self.app)
    def test_rejects_symlink_outside_bundle(self):
        outside=Path(self.temp.name)/'outside-secret.txt';outside.write_text('x')
        (self.app/'Contents/Resources/peek.txt').symlink_to(outside)
        with self.assertRaisesRegex(ValueError,'APP_EXTERNAL_SYMLINK'):
            r.safety_scan(self.app)
    def test_non_mac_cannot_claim_release(self):
        with patch.object(r.platform,'system',return_value='Linux'):
            with self.assertRaisesRegex(ValueError,'MACOS_REQUIRED'):
                r.release(Path(self.temp.name),Path('gate.json'),Path(self.temp.name)/'out')
    def test_release_is_private_with_explicit_blockers(self):
        self.assertIn('HUMAN_UAT_NOT_RUN',r.BLOCKERS)
        self.assertIn('PUBLICATION_AUTHORIZATION_NOT_GRANTED',r.BLOCKERS)
        self.assertIn('SIGNED_NOTARIZED_DISTRIBUTION_NOT_VERIFIED',r.BLOCKERS)

if __name__=='__main__':unittest.main()
