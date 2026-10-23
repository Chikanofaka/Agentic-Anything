"""E4-B1/P1: UI copy contract for Host-gated PostgreSQL fixture controls.

Static test only: no SQL process, native provider, credentials or paid request.
"""
from pathlib import Path
import re
import unittest


UI = Path(__file__).resolve().parents[1] / "ui" / "app.js"
REQUIRED = frozenset({
    "gradeTitle", "gradeNote", "gradeResultDisclaimer", "gradeCurrentQuestion",
    "gradeRequiresSQL", "gradeStatus", "gradeInspect", "gradeExpected",
    "gradeExecute", "gradePending",
})


class E4B1GradingCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = UI.read_text(encoding="utf-8")

    def test_every_grade_control_key_exists_in_en_and_zh(self):
        source = self.source
        self.assertIn('    en: {', source)
        self.assertIn('    zh: {', source)
        en = source.split('    en: {', 1)[1].split('    zh: {', 1)[0]
        zh = source.split('    zh: {', 1)[1].split('  };', 1)[0]
        for language, block in (("en", en), ("zh", zh)):
            for key in REQUIRED:
                with self.subTest(language=language, key=key):
                    self.assertRegex(block, r'(?m)^\s*' + re.escape(key) + r': "[^"\n]+",')

    def test_grade_panel_calls_have_translations(self):
        source = self.source
        used = set(re.findall(r't\("(grade[A-Za-z]+)"\)', source))
        self.assertEqual(used, REQUIRED)

    def test_consent_security_contract_not_removed(self):
        source = self.source
        for anchor in (
            'function gradingPanel()',
            'gradeFixtureApproved = false',
            'act("grade_inspect", {fixture_json: box.value})',
            'act("grade_execute", {fixture_sha256: reviewed.fixture_sha256})',
            'execute.disabled = busy || !gradeFixtureApproved',
        ):
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, source)


if __name__ == "__main__":
    unittest.main()
