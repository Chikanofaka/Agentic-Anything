"""Authority and path validation for the two data-only agent contracts."""

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tia_runtime.contracts import ContractError, load_roles


ROOT = Path(__file__).resolve().parents[1]


class RoleContractsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "agents", self.root / "agents")
        self.manifest = self.root / "agents" / "roles.json"

    def tearDown(self):
        self.temp.cleanup()

    def change(self, callback):
        manifest = json.loads(self.manifest.read_text())
        callback(manifest)
        self.manifest.write_text(json.dumps(manifest))

    def test_independent_roles_load_with_narrow_permissions(self):
        roles = load_roles(self.root)
        self.assertEqual(set(roles), {"interviewer", "trainer"})
        self.assertEqual(roles["trainer"].allowed_inputs, ("closed_reviewed_receipt",))
        self.assertIn("scoring", roles["interviewer"].forbidden_authorities)
        with self.assertRaises(FrozenInstanceError):
            roles["trainer"].role_id = "interviewer"

    def test_early_trainer_permission_is_rejected(self):
        self.change(lambda manifest: manifest["roles"][1]["active_states"].append("INTERVIEWING"))
        with self.assertRaises(ContractError):
            load_roles(self.root)

    def test_score_authority_cannot_be_removed(self):
        self.change(lambda manifest: manifest["roles"][0]["forbidden_authorities"].remove("scoring"))
        with self.assertRaises(ContractError):
            load_roles(self.root)

    def test_unknown_and_duplicate_roles_are_rejected(self):
        for value in ("evaluator", "interviewer"):
            with self.subTest(role=value):
                self.change(lambda manifest: manifest["roles"][1].update(role_id=value))
                with self.assertRaises(ContractError):
                    load_roles(self.root)

    def test_path_traversal_and_absolute_documents_are_rejected(self):
        for value in ("../../outside.md", "/private/tmp/outside.md"):
            with self.subTest(path=value):
                self.change(lambda manifest: manifest["roles"][0]["documents"].update(identity=value))
                with self.assertRaises(ContractError):
                    load_roles(self.root)

    def test_document_symlink_escape_is_rejected(self):
        outside = self.root.parent / f"{self.root.name}-outside.md"
        outside.write_text("not an approved role contract")
        self.addCleanup(outside.unlink)
        document = self.root / "agents/interviewer/identity.md"
        document.unlink()
        document.symlink_to(outside)
        with self.assertRaises(ContractError):
            load_roles(self.root)

    def test_unknown_manifest_fields_are_rejected(self):
        self.change(lambda manifest: manifest.update(endpoint="https://example.invalid"))
        with self.assertRaises(ContractError):
            load_roles(self.root)

    def test_missing_document_is_rejected(self):
        (self.root / "agents/trainer/soul.md").unlink()
        with self.assertRaises(ContractError):
            load_roles(self.root)

    def test_invalid_json_is_a_contract_error(self):
        self.manifest.write_text("{")
        with self.assertRaises(ContractError):
            load_roles(self.root)


if __name__ == "__main__":
    unittest.main()
