"""Import boundary regressions using local, synthetic packages only.

These checks never extract archives or execute package source. The shipped legacy
fixtures also exercise compatibility with the versioned package contract.
"""
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

from hal_core import contracts
from hal_core.contracts import ContractError, inspect


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "fixtures" / "research"
RETURNS = ROOT / "fixtures" / "returns"
SENTINEL = "UNTRUSTED_DIAGNOSTIC_SENTINEL"


class PackageSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def fixture_members(self, fixture=RESEARCH, prefix=""):
        return [
            (prefix + p.relative_to(fixture).as_posix(), p.read_bytes())
            for p in sorted(fixture.rglob("*"))
            if p.is_file()
        ]

    def archive(self, members=None, compression=zipfile.ZIP_STORED):
        path = self.base / "package.zip"
        with zipfile.ZipFile(path, "w", compression=compression) as archive:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                source = members if members is not None else self.fixture_members()
                for name, content in source:
                    archive.writestr(name, content)
        return path

    def copied_fixture(self):
        path = self.base / "package"
        shutil.copytree(RESEARCH, path)
        return path

    def reject(self, path):
        with self.assertRaises(ContractError) as caught:
            inspect(path)
        self.assertNotIn(SENTINEL, str(caught.exception))
        return str(caught.exception)

    def manifest_archive(self, raw):
        members = [(name, raw if name == "harness.json" else data)
                   for name, data in self.fixture_members()]
        return self.archive(members)

    def test_root_zip_matches_directory_for_both_domains(self):
        for fixture in (RESEARCH, RETURNS):
            with self.subTest(domain=fixture.name):
                expected = inspect(fixture)
                actual = inspect(self.archive(self.fixture_members(fixture)))
                self.assertEqual(actual.digest, expected.digest)
                self.assertEqual(actual.files, expected.files)
                self.assertEqual(actual.manifest, expected.manifest)

    def test_github_wrapper_matches_root_zip_and_directory(self):
        for fixture in (RESEARCH, RETURNS):
            for explicit_directories in (False, True):
                with self.subTest(domain=fixture.name, directories=explicit_directories):
                    prefix = "specialist-repository-main/"
                    members = self.fixture_members(fixture, prefix)
                    if explicit_directories:
                        members = [(prefix, b""), (prefix + "skills/", b"")] + members
                    expected = inspect(fixture)
                    actual = inspect(self.archive(members))
                    self.assertEqual(actual.digest, expected.digest)
                    self.assertEqual(actual.files, expected.files)
                    self.assertEqual(actual.manifest, expected.manifest)

    def test_wrapper_with_outside_file_is_ambiguous(self):
        self.reject(self.archive(self.fixture_members(prefix="repo-main/") + [("outside.txt", b"outside")]))

    def test_multiple_wrapped_packages_are_ambiguous(self):
        self.reject(self.archive(self.fixture_members(prefix="repo-a/") + self.fixture_members(RETURNS, "repo-b/")))

    def test_root_and_wrapped_manifests_are_ambiguous(self):
        self.reject(self.archive(self.fixture_members() + [("nested/harness.json", b"{}")]))

    def test_nested_manifest_is_not_recursively_discovered(self):
        self.reject(self.archive(self.fixture_members(prefix="repo-main/nested/")))

    def test_invalid_raw_zip_paths_fail_before_wrapper_normalization(self):
        for name in (
            "../" + SENTINEL,
            "repo-main/../" + SENTINEL,
            "/" + SENTINEL,
            "C:/" + SENTINEL,
            "repo-main\\" + SENTINEL,
            "repo-main//" + SENTINEL,
            "repo-main/./" + SENTINEL,
        ):
            with self.subTest(path=name):
                self.reject(self.archive(self.fixture_members() + [(name, b"bad")]))

    def test_duplicate_zip_path_is_rejected(self):
        self.reject(self.archive(self.fixture_members() + [("README.md", b"duplicate")]))

    def test_case_colliding_zip_paths_are_rejected(self):
        self.reject(self.archive(self.fixture_members() + [("readme.md", b"collision")]))

    def test_file_directory_zip_collision_is_rejected(self):
        self.reject(self.archive(self.fixture_members() + [("README.md/child.txt", b"collision")]))

    def test_zip_symlink_file_is_rejected(self):
        link = zipfile.ZipInfo("alias")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.reject(self.archive(self.fixture_members() + [(link, b"README.md")]))

    def test_zip_directory_named_symlink_is_rejected(self):
        link = zipfile.ZipInfo("alias/")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.reject(self.archive(self.fixture_members() + [(link, b"target")]))

    def test_zip_fifo_is_rejected(self):
        fifo = zipfile.ZipInfo("pipe")
        fifo.create_system = 3
        fifo.external_attr = (stat.S_IFIFO | 0o600) << 16
        self.reject(self.archive(self.fixture_members() + [(fifo, b"")]))

    def test_secret_filenames_are_rejected(self):
        for name in (".env", ".env.production", ".ENV.production", "nested/.env.test", "private.key"):
            with self.subTest(path=name):
                self.reject(self.archive(self.fixture_members() + [(name, b"SYNTHETIC_ONLY")]))

    def test_restricted_directory_entry_is_rejected_even_when_empty(self):
        self.reject(self.archive(self.fixture_members() + [(".git/", b"")]))

    def test_directory_root_symlink_is_rejected(self):
        path = self.copied_fixture()
        link = self.base / "linked-package"
        try:
            link.symlink_to(path, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest("Local symlink creation unsupported: " + type(error).__name__)
        self.reject(link)

    def test_directory_child_symlink_is_rejected(self):
        path = self.copied_fixture()
        try:
            (path / "linked-file").symlink_to(path / "README.md")
        except (OSError, NotImplementedError) as error:
            self.skipTest("Local symlink creation unsupported: " + type(error).__name__)
        self.reject(path)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation unavailable")
    def test_directory_fifo_is_rejected_without_reading(self):
        path = self.copied_fixture()
        try:
            os.mkfifo(path / "pipe")
        except (OSError, NotImplementedError) as error:
            self.skipTest("Local FIFO creation unsupported: " + type(error).__name__)
        self.reject(path)

    def test_directory_empty_restricted_subdirectory_is_rejected(self):
        path = self.copied_fixture()
        (path / ".ssh").mkdir()
        self.reject(path)

    def test_directory_secret_filename_is_rejected(self):
        path = self.copied_fixture()
        (path / ".env.production").write_text("SYNTHETIC_ONLY", encoding="utf-8")
        self.reject(path)

    def test_zip_member_count_limit(self):
        path = self.archive()
        with patch.object(contracts, "MAX_FILES", 1):
            self.reject(path)

    def test_directory_entry_count_limit_includes_empty_directories(self):
        path = self.copied_fixture()
        existing_count = len(list(path.rglob("*")))
        for index in range(4):
            (path / ("empty-" + str(index))).mkdir()
        with patch.object(contracts, "MAX_FILES", existing_count + 1):
            self.reject(path)

    def test_zip_single_file_size_limit(self):
        path = self.archive()
        with patch.object(contracts, "MAX_FILE_BYTES", 8):
            self.reject(path)

    def test_directory_single_file_size_limit(self):
        with patch.object(contracts, "MAX_FILE_BYTES", 8):
            self.reject(RESEARCH)

    def test_zip_total_uncompressed_size_limit(self):
        path = self.archive()
        with patch.object(contracts, "MAX_PACKAGE_BYTES", 8):
            self.reject(path)

    def test_directory_total_size_limit(self):
        with patch.object(contracts, "MAX_PACKAGE_BYTES", 8):
            self.reject(RESEARCH)

    def test_archive_container_size_limit(self):
        path = self.archive()
        with patch.object(contracts, "MAX_ARCHIVE_BYTES", 8):
            self.reject(path)

    def test_zip_compression_ratio_limit(self):
        path = self.archive(self.fixture_members() + [("padding.txt", b"x" * 65536)], zipfile.ZIP_DEFLATED)
        with patch.object(contracts, "MAX_COMPRESSION_RATIO", 2):
            self.reject(path)

    def test_corrupt_member_crc_is_a_safe_contract_error(self):
        marker = b"CRC_MARKER_SAMPLE"
        path = self.archive(self.fixture_members() + [(SENTINEL + ".txt", marker)])
        data = path.read_bytes()
        self.assertEqual(data.count(marker), 1)
        path.write_bytes(data.replace(marker, b"CRC_MARKER_CHANGD", 1))
        self.reject(path)

    def test_truncated_zip_is_a_safe_contract_error(self):
        path = self.archive()
        path.write_bytes(path.read_bytes()[:-30])
        self.reject(path)

    def test_encrypted_member_is_a_safe_contract_error(self):
        path = self.archive()
        data = bytearray(path.read_bytes())
        local = data.index(b"PK\x03\x04")
        central = data.index(b"PK\x01\x02")
        for offset in (local + 6, central + 8):
            flags = struct.unpack_from("<H", data, offset)[0]
            struct.pack_into("<H", data, offset, flags | 1)
        path.write_bytes(data)
        self.reject(path)

    def test_unsupported_compression_is_a_safe_contract_error(self):
        path = self.archive()
        data = bytearray(path.read_bytes())
        local = data.index(b"PK\x03\x04")
        central = data.index(b"PK\x01\x02")
        for offset in (local + 8, central + 10):
            struct.pack_into("<H", data, offset, 99)
        path.write_bytes(data)
        self.reject(path)

    def test_invalid_utf8_zip_member_name_is_a_safe_contract_error(self):
        path = self.archive()
        data = bytearray(path.read_bytes())
        local = data.index(b"PK\x03\x04")
        central = data.index(b"PK\x01\x02")
        for offset in (local + 6, central + 8):
            flags = struct.unpack_from("<H", data, offset)[0]
            struct.pack_into("<H", data, offset, flags | 0x800)
        # Both headers declare UTF-8, but the first filename byte is invalid.
        data[local + 30] = 0xff
        data[central + 46] = 0xff
        path.write_bytes(data)
        self.reject(path)

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "No-follow open unavailable")
    def test_zip_root_swapped_to_symlink_before_open_is_rejected(self):
        selected = self.archive()
        alternate = self.base / "alternate.zip"
        alternate.write_bytes(selected.read_bytes())
        original_open = os.open
        swapped = False

        def swap_before_open(path, flags, *args, **kwargs):
            nonlocal swapped
            if os.fspath(path) == os.fspath(selected) and not swapped:
                selected.unlink()
                selected.symlink_to(alternate)
                swapped = True
            return original_open(path, flags, *args, **kwargs)

        with patch.object(contracts.os, "open", side_effect=swap_before_open):
            self.reject(selected)
        self.assertTrue(swapped, "Regression must exercise the archive open race")

    def test_path_depth_limit_is_shared_by_zip_and_directory(self):
        allowed = "a/" * 31 + "file.txt"
        too_deep = "a/" * 32 + "file.txt"
        inspect(self.archive(self.fixture_members() + [(allowed, b"bounded")]))
        self.reject(self.archive(self.fixture_members() + [(too_deep, b"too deep")]))
        path = self.copied_fixture()
        allowed_file = path / allowed
        allowed_file.parent.mkdir(parents=True)
        allowed_file.write_bytes(b"bounded")
        inspect(path)
        too_deep_file = path / too_deep
        too_deep_file.parent.mkdir(parents=True)
        too_deep_file.write_bytes(b"too deep")
        self.reject(path)

    def test_malformed_manifest_json_is_a_safe_contract_error(self):
        self.reject(self.manifest_archive('{"' + SENTINEL + '":'))

    def test_invalid_manifest_encoding_is_a_safe_contract_error(self):
        self.reject(self.manifest_archive(b"\xff\xfe"))

    def test_duplicate_manifest_json_keys_are_rejected(self):
        raw = (RESEARCH / "harness.json").read_text(encoding="utf-8")
        raw = raw.replace('"schema_version":', '"schema_version":"unsupported","schema_version":', 1)
        self.reject(self.manifest_archive(raw))

    def test_nonfinite_manifest_json_numbers_are_rejected(self):
        raw = (RESEARCH / "harness.json").read_text(encoding="utf-8").rstrip()
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                self.reject(self.manifest_archive(raw[:-1] + ',"extra":' + constant + '}'))

    def test_nested_secret_field_is_rejected_without_reflection(self):
        manifest = json.loads((RESEARCH / "harness.json").read_text(encoding="utf-8"))
        manifest["model_requirements"]["nested"] = [{"api_key": SENTINEL}]
        self.reject(self.manifest_archive(json.dumps(manifest)))

    def test_surrogate_manifest_string_is_rejected_before_public_receipt(self):
        manifest = json.loads((RESEARCH / "harness.json").read_text(encoding="utf-8"))
        manifest["name"] = "invalid\ud800name"
        self.reject(self.manifest_archive(json.dumps(manifest)))

    def test_overdeep_manifest_is_a_safe_contract_error(self):
        self.reject(self.manifest_archive("[" * 1200 + "0" + "]" * 1200))

    def test_inspection_does_not_extract_archive(self):
        path = self.archive(self.fixture_members(prefix="repo-main/"))
        before = tuple(sorted(p.name for p in self.base.iterdir()))
        with patch.object(zipfile.ZipFile, "extract", side_effect=AssertionError("Unexpected extraction")):
            with patch.object(zipfile.ZipFile, "extractall", side_effect=AssertionError("Unexpected extraction")):
                inspect(path)
        self.assertEqual(tuple(sorted(p.name for p in self.base.iterdir())), before)


if __name__ == "__main__":
    unittest.main()
