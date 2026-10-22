"""Exercise rejection of wrong provenance and malformed device artifacts."""
import hashlib
import importlib.util
import json
import plistlib
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("verify_ipa", Path(__file__).parents[1] / "scripts/verify-ipa.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.manifest = {"commit_sha": "a" * 40, "workflow_run_id": "42",
                         "workflow_run_attempt": "1", "repository": "example/factory",
                         "app_version": "1.0.1", "build_number": "2",
                         "bundle_id": module.BUNDLE_ID, "test_status": "PASS",
                         "signing_status": "UNSIGNED", "ipa_file": "app.ipa"}

    def package(self, platform=2, extra_path=None, plist_version="1.0.1", command_size=24):
        info = {"CFBundleIdentifier": module.BUNDLE_ID,
                "CFBundleShortVersionString": plist_version, "CFBundleVersion": "2",
                "CFBundleSupportedPlatforms": ["iPhoneOS"], "CFBundleExecutable": "App"}
        binary = struct.pack("<8I", 0xFEEDFACF, 0x0100000C, 0, 2, 1, 24, 0, 0)
        binary += struct.pack("<6I", 0x32, command_size, platform, 0, 0, 0)
        with zipfile.ZipFile(self.folder / "app.ipa", "w") as archive:
            archive.writestr("Payload/App.app/Info.plist", plistlib.dumps(info))
            archive.writestr("Payload/App.app/App", binary)
            if extra_path:
                archive.writestr(extra_path, b"unexpected")
        self.manifest["ipa_sha256"] = hashlib.sha256((self.folder / "app.ipa").read_bytes()).hexdigest()
        self.write_manifest()

    def write_manifest(self):
        (self.folder / "manifest.json").write_text(json.dumps(self.manifest))

    def verify(self):
        return module.verify(self.folder, "a" * 40, "42", "1.0.1", "example/factory", "1")

    def test_valid_device_package(self):
        self.package()
        self.assertEqual(self.verify()["validation"], "PASS")

    def test_wrong_run_or_commit_or_attempt_rejected(self):
        self.package()
        for field, bad in (("workflow_run_id", "41"), ("commit_sha", "b" * 40),
                           ("workflow_run_attempt", "2"), ("repository", "wrong/repo")):
            with self.subTest(field=field):
                original = self.manifest[field]
                self.manifest[field] = bad
                self.write_manifest()
                with self.assertRaisesRegex(ValueError, "Manifest mismatch"):
                    self.verify()
                self.manifest[field] = original

    def test_tampered_ipa_rejected(self):
        self.package()
        with (self.folder / "app.ipa").open("ab") as handle:
            handle.write(b"tampered")
        with self.assertRaisesRegex(ValueError, "checksum"):
            self.verify()

    def test_path_traversal_rejected_even_with_matching_hash(self):
        for path in ("../outside", "/absolute", "C:/outside", "Payload/../outside"):
            with self.subTest(path=path):
                self.package(extra_path=path)
                with self.assertRaisesRegex(ValueError, "Unsafe ZIP path"):
                    self.verify()

    def test_simulator_binary_rejected(self):
        self.package(platform=7)
        with self.assertRaisesRegex(ValueError, "iOS device"):
            self.verify()

    def test_plist_version_mismatch_rejected(self):
        self.package(plist_version="1.0.0")
        with self.assertRaisesRegex(ValueError, "App plist mismatch"):
            self.verify()

    def test_bad_load_command_rejected(self):
        self.package(command_size=64)
        with self.assertRaisesRegex(ValueError, "load command"):
            self.verify()

    def test_manifest_filename_cannot_escape_folder(self):
        self.package()
        self.manifest["ipa_file"] = "../app.ipa"
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "Unsafe IPA filename"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
