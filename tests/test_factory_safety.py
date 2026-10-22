"""Prevent unsafe dispatch and false device acceptance; no network or credentials."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("factory", Path(__file__).parents[1] / "scripts/factory.py")
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)


class FactorySafetyTests(unittest.TestCase):
    def test_request_cannot_escape_local_output(self):
        for name in ("../other", "C:\\other", "/other", ".", "a/b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                factory.request_path(name)

    def test_runner_changes_rejected(self):
        for label in ("macos-latest", "macos-15-large", "self-hosted", "${{ inputs.runner }}"):
            with self.subTest(label=label), self.assertRaises(ValueError):
                factory.validate_workflow(f"runs-on: {label}\nfactory_request_id:\ncontents: read")
        factory.validate_workflow("runs-on: macos-15\nfactory_request_id:\ncontents: read")

    def test_private_repository_not_dispatched(self):
        with patch.object(factory, "gh", return_value={"private": True}) as gh:
            with self.assertRaisesRegex(ValueError, "public repository"):
                factory.build({"build_attempts": 0}, "main", "a" * 40, "1.0.1", True)
            self.assertEqual(gh.call_count, 1)

    def test_retry_limit_stops_before_network(self):
        with patch.object(factory, "gh") as gh:
            with self.assertRaisesRegex(ValueError, "repair limit"):
                factory.build({"build_attempts": 6}, "main", "a" * 40, "1.0.1", True)
            gh.assert_not_called()

    def test_wrong_run_commit_never_downloaded(self):
        with patch.object(factory, "run_info", return_value={"headSha": "b" * 40}), \
                patch.object(factory, "download") as download:
            with self.assertRaisesRegex(ValueError, "Run commit mismatch"):
                factory.fetch({}, "42", "a" * 40, "1.0.1")
            download.assert_not_called()

    def test_install_preparation_requires_verified_ipa(self):
        with self.assertRaisesRegex(ValueError, "Verified IPA"):
            factory.prepare_install({"phase": "FAILED"}, False)

    def test_successful_repair_replaces_current_failure_but_keeps_history(self):
        info = {"headSha": "a" * 40, "workflowName": "iOS build", "status": "completed",
                "attempt": 1, "url": "https://example.invalid/run/42"}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(factory, "OUTPUT", Path(directory)), \
                patch.object(factory, "run_info", side_effect=[dict(info, conclusion="failure"),
                                                              dict(info, conclusion="success")]), \
                patch.object(factory, "gh", return_value="test log"), \
                patch.object(factory, "download"), \
                patch.object(factory.verifier, "verify", return_value={"validation": "PASS"}), \
                contextlib.redirect_stdout(io.StringIO()):
            evidence = Path(directory) / "artifacts/run-42/test-evidence-42-1"
            evidence.mkdir(parents=True)
            (evidence / "test-summary.json").write_text(json.dumps({
                "result": "Passed", "failedTests": 0, "skippedTests": 0, "passedTests": 4}))
            (evidence / "test.log").write_text(
                "Test Suite 'CounterStoreTests' passed\nTest Suite 'FactoryHelloUITests' passed\n")
            state = {"request_id": "repair-test"}
            self.assertFalse(factory.fetch(state, "42", "a" * 40, "1.0.1"))
            self.assertTrue(factory.fetch(state, "42", "a" * 40, "1.0.1"))
            self.assertEqual(state["phase"], "IPA_READY")
            self.assertEqual(state["conclusion"], "success")
            failure = next(entry for entry in state["history"] if entry["phase"] == "FAILED")
            self.assertEqual(failure["conclusion"], "failure")
            self.assertIn("failure_evidence", failure)

    def test_device_version_and_data_must_match(self):
        state = {"artifact": {"version": "1.0.1"}}
        with self.assertRaisesRegex(ValueError, "version mismatch"):
            factory.record_device(state, "1.0.0", 4, 4, "user report")
        with self.assertRaisesRegex(ValueError, "retain data"):
            factory.record_device(state, "1.0.1", 4, 0, "user report")

    def test_natural_language_request_is_local_only(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(factory, "OUTPUT", Path(directory)), \
                patch.object(factory, "gh") as gh, contextlib.redirect_stdout(io.StringIO()):
            state = factory.new_request("Keep my local data while updating the counter")
            self.assertEqual(state["phase"], "DRAFT")
            path = factory.request_path(state["request_id"])
            self.assertTrue(path.is_file())
            self.assertTrue((path.parent / "request.md").is_file())
            gh.assert_not_called()

    def test_build_pass_does_not_imply_install_pass(self):
        with self.assertRaisesRegex(ValueError, "Prepare the exact IPA"):
            factory.record_install({"phase": "IPA_READY"}, "installed", "test observation")

    def test_device_acceptance_requires_installation_record(self):
        state = {"phase": "IPA_READY", "artifact": {"version": "1.0.1"}}
        with self.assertRaisesRegex(ValueError, "Record installation"):
            factory.record_device(state, "1.0.1", 4, 4, "test observation")


if __name__ == "__main__":
    unittest.main()
