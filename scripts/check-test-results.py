"""Fail closed if XCTest reports missing, skipped, or failed tests (Xcode 16.4)."""
import json
from pathlib import Path

summary = json.loads(Path("build/evidence/test-summary.json").read_text())
assert summary.get("result") == "Passed", summary
assert summary.get("failedTests") == 0, summary
assert summary.get("skippedTests") == 0, summary
assert summary.get("passedTests", 0) >= 4, summary
log = Path("build/evidence/test.log").read_text()
for suite in ("CounterStoreTests", "FactoryHelloUITests"):
    assert f"Test Suite '{suite}' passed" in log, f"Missing passing suite: {suite}"
Path("build/evidence/TEST_PASSED").write_text("Unit and UI suites executed and passed.\n")
