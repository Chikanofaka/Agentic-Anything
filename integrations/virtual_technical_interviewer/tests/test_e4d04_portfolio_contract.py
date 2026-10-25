"""E4D-04 contract tests for the offline browser-owned portfolio slice.
No server, no model, no credentials, no saved interview mutation.
"""
import re
import subprocess
import shutil
import unittest
from pathlib import Path

PORTAL = Path(__file__).resolve().parents[1] / 'tools/tia_e4d04_portfolio.html'
SCRIPT = Path(__file__).with_name('e4d04_browser_contract.js')

class PortfolioContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PORTAL.read_text(encoding='utf-8')

    def test_real_html_and_typed_file_picker(self):
        self.assertTrue(self.html.startswith('<!doctype html>'))
        self.assertIn('id="sourceFile"', self.html)
        for extension in ('.txt','.md','.csv','.json'):
            self.assertIn(extension, self.html)

    def test_versioned_portfolio_and_checkout(self):
        self.assertIn('tia-e4d04-portfolio/v1', self.html)
        self.assertIn('tia-e4d04-checkout/v1', self.html)

    def test_observed_anchors_require_evidence_and_rationale(self):
        self.assertIn('EVIDENCE_REFERENCE_REQUIRED', self.html)
        self.assertIn('OBSERVABLE_RATIONALE_REQUIRED', self.html)
        self.assertIn('USER_SELF_REPORTED_UNVERIFIED', self.html)

    def test_no_paid_provider_connection(self):
        self.assertNotRegex(self.html, r'fetch\s*\(|XMLHttpRequest\s*\(|sendBeacon\s*\(')
        self.assertNotIn('Authorization:', self.html)
        self.assertNotIn('localStorage', self.html)
        self.assertNotIn('indexedDB', self.html)

    def test_e4d03_import_is_status_only(self):
        self.assertIn("'tia-e4d03-session-report/v1'", self.html)
        self.assertIn('NOT_SCORED', self.html)
        self.assertIn('INVALID_E4D03_REPORT', self.html)

    def test_six_communication_and_five_technical(self):
        for i in range(1,6): self.assertIn("'T%02d'"%i,self.html)
        for i in range(1,7): self.assertIn("'C%02d'"%i,self.html)

    def test_60_40_registry_not_experimental_12_merge(self):
        maxima={}
        for cat in ('T','C'):
            maxima[cat]=sum(int(x) for x in re.findall(r"\['"+cat+r"\d\d','(?:Technical|Communication)','[^']+',([0-9]+),",self.html))
        self.assertEqual(maxima,{'T':60,'C':40})
        self.assertIn('70/20/10', self.html)
        self.assertIn('No crosswalk or automatic migration', self.html)

    def test_no_score_promotion_from_missing_evidence(self):
        self.assertIn('NOT_OBSERVED', self.html)
        self.assertIn('Missing dimensions do not become zero', self.html)
        self.assertIn('NOT a final score',self.html)

    def test_sha_duplicate_refusal_and_reassociation(self):
        self.assertIn('DUPLICATE_SOURCE_SHA',self.html)
        self.assertIn('SOURCE_HASH_MISMATCH',self.html)
        self.assertIn('SHA-256',self.html)

    def test_user_original_source_not_overwritten(self):
        self.assertIn('new .txt file',self.html)
        self.assertIn('BEGIN ORIGINAL FILE',self.html)
        self.assertIn('END ORIGINAL FILE',self.html)
        self.assertNotIn('writeFile(', self.html)

    def test_xss_risky_dom_insertion_absent(self):
        self.assertNotIn('.innerHTML', self.html)
        self.assertNotIn('.outerHTML', self.html)
        self.assertIn('.textContent', self.html)

    def test_browser_dom_simulation_if_node_is_available(self):
        if not shutil.which('node'):
            self.skipTest('Node.js unavailable; manual browser UAT required')
        proc=subprocess.run(['node',str(SCRIPT),str(PORTAL)],capture_output=True,text=True,timeout=25)
        self.assertEqual(proc.returncode,0,proc.stdout+'\n'+proc.stderr)
        self.assertIn('BROWSER_CONTRACT=PASS',proc.stdout)

if __name__=='__main__': unittest.main()
