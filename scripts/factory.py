"""Local orchestration; Codex writes code, this tool tracks exact CI artifacts.

No Apple credentials, signing keys, device IDs, or authentication automation.
"""
import argparse
import base64
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "local-output"
REPOSITORY = "Jupiter705/iphone-ai-app-factory"
WORKFLOW = "ios-build.yml"
MAX_REPAIRS = 5
spec = importlib.util.spec_from_file_location("verify_ipa", ROOT / "scripts/verify-ipa.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def request_path(request_id):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", request_id):
        raise ValueError("Invalid request ID")
    return OUTPUT / "requests" / request_id / "state.json"


def read_state(request_id):
    return json.loads(request_path(request_id).read_text(encoding="utf-8-sig"))


def transition(state, phase, **values):
    state.update(values)
    state.update(phase=phase, updated_at=now())
    state.setdefault("history", []).append({"phase": phase, "at": state["updated_at"], **values})
    save(request_path(state["request_id"]), state)
    print(json.dumps({"request_id": state["request_id"], "phase": phase,
                      **values}, ensure_ascii=False), flush=True)


def gh(*arguments, as_json=False):
    cli = ROOT / ".tools/gh/bin/gh.exe"
    if not cli.is_file():
        raise ValueError("Project-local gh is missing")
    environment = dict(os.environ, GH_CONFIG_DIR=str(OUTPUT / "gh-config"))
    result = subprocess.run([str(cli), *map(str, arguments)], cwd=ROOT, env=environment,
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        # No auth/token commands are invoked; keep network errors local.
        raise RuntimeError(f"gh {arguments[0]} {arguments[1]} failed: {result.stderr.strip()}")
    return json.loads(result.stdout) if as_json else result.stdout


def new_request(text):
    request_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
    path = request_path(request_id)
    path.parent.mkdir(parents=True)
    (path.parent / "request.md").write_text(text + "\n", encoding="utf-8")
    state = {"request_id": request_id, "repository": REPOSITORY, "created_at": now(),
             "build_attempts": 0, "repair_limit": MAX_REPAIRS,
             "signing": "NOT_ATTEMPTED", "installation": "NOT_ATTEMPTED",
             "device_launch": "NOT_TESTED", "renewal": "NOT_TESTED"}
    transition(state, "DRAFT")
    return state


def validate_workflow(text):
    labels = re.findall(r"^\s*runs-on:\s*(\S+)\s*$", text, re.MULTILINE)
    verifier.require(labels == ["macos-15"], "Only the reviewed standard macos-15 runner is allowed")
    verifier.require("factory_request_id:" in text, "Workflow lacks request correlation input")
    verifier.require("contents: read" in text, "Workflow permissions differ from reviewed configuration")


def build(state, ref, commit, version, no_wait):
    verifier.require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "Full commit SHA required")
    verifier.require(state["build_attempts"] < 1 + MAX_REPAIRS, "CI repair limit reached")
    if state.get("run_id"):
        previous = run_info(state["run_id"])
        verifier.require(previous["status"] == "completed", "Previous CI is still running")
    repo = gh("api", f"repos/{REPOSITORY}", as_json=True)
    verifier.require(repo.get("private") is False, "Only the authorized public repository is allowed")
    resolved = gh("api", f"repos/{REPOSITORY}/commits/{ref}", as_json=True)
    verifier.require(resolved["sha"] == commit, "Ref does not match expected commit")
    remote = gh("api", f"repos/{REPOSITORY}/contents/.github/workflows/{WORKFLOW}?ref={commit}", as_json=True)
    validate_workflow(base64.b64decode(remote["content"]).decode())
    state["build_attempts"] += 1
    correlation = f"{state['request_id']}-a{state['build_attempts']}"
    transition(state, "BUILDING", commit_sha=commit, version=version, ref=ref, correlation=correlation)
    gh("workflow", "run", WORKFLOW, "-R", REPOSITORY, "--ref", ref,
       "-f", f"factory_request_id={correlation}")
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        runs = gh("run", "list", "-R", REPOSITORY, "--workflow", WORKFLOW, "--limit", "30",
                  "--json", "databaseId,headSha,displayTitle", as_json=True)
        matching = [r for r in runs if r["headSha"] == commit and r["displayTitle"].endswith(correlation)]
        if len(matching) == 1:
            state["run_id"] = str(matching[0]["databaseId"])
            save(request_path(state["request_id"]), state)
            if not no_wait:
                watch(state)
            else:
                print(json.dumps({"run_id": state["run_id"]}), flush=True)
            return
        verifier.require(len(matching) <= 1, "Ambiguous workflow run; refusing automatic selection")
        time.sleep(5)
    raise RuntimeError("Dispatch accepted but correlated run not found; inspect runs before redispatching")


def run_info(run_id):
    verifier.require(str(run_id).isdigit(), "Numeric run ID required")
    return gh("run", "view", run_id, "-R", REPOSITORY, "--json",
              "databaseId,headSha,status,conclusion,attempt,url,jobs,workflowName,headBranch", as_json=True)


def download(run_id, name, target, sentinel):
    if not (target / sentinel).is_file():
        verifier.require(not target.exists() or not any(target.iterdir()),
                         f"Incomplete existing artifact directory: {target}")
        target.mkdir(parents=True, exist_ok=True)
        gh("run", "download", run_id, "-R", REPOSITORY, "-n", name, "-D", target)


def fetch(state, run_id, commit, version):
    info = run_info(run_id)
    verifier.require(info["headSha"] == commit, "Run commit mismatch")
    verifier.require(info["workflowName"] == "iOS build", "Unexpected workflow")
    verifier.require(info["status"] == "completed", "Run has not completed")
    attempt = str(info["attempt"])
    directory = OUTPUT / "artifacts" / f"run-{run_id}"
    directory.mkdir(parents=True, exist_ok=True)
    save(directory / f"run-attempt-{attempt}.json", info)
    log = gh("run", "view", run_id, "-R", REPOSITORY, "--attempt", attempt, "--log")
    (directory / f"run-attempt-{attempt}.log").write_text(log, encoding="utf-8")
    evidence = directory / f"test-evidence-{run_id}-{attempt}"
    download(run_id, evidence.name, evidence, "xcode.txt")
    if info["conclusion"] != "success":
        transition(state, "FAILED", run_id=str(run_id), commit_sha=commit,
                   conclusion=info["conclusion"], failure_evidence=str(directory))
        return False
    summary = json.loads((evidence / "test-summary.json").read_text())
    verifier.require(summary.get("result") == "Passed" and summary.get("failedTests") == 0
                     and summary.get("skippedTests") == 0 and summary.get("passedTests", 0) >= 4,
                     "Missing, skipped, or failed tests")
    test_log = (evidence / "test.log").read_text(encoding="utf-8", errors="replace")
    for suite in ("CounterStoreTests", "FactoryHelloUITests"):
        verifier.require(f"Test Suite '{suite}' passed" in test_log, f"Suite not passed: {suite}")
    transition(state, "TEST_PASSED", run_id=str(run_id), commit_sha=commit, version=version,
               conclusion=info["conclusion"])
    artifact = directory / f"unsigned-ipa-{run_id}-{attempt}"
    download(run_id, artifact.name, artifact, "manifest.json")
    result = verifier.verify(artifact, commit, run_id, version, REPOSITORY, attempt)
    save(artifact / "factory-verification.json", result)
    symbols = directory / f"symbols-{run_id}-{attempt}"
    if not symbols.exists() or not any(symbols.iterdir()):
        symbols.mkdir(parents=True, exist_ok=True)
        gh("run", "download", run_id, "-R", REPOSITORY, "-n", symbols.name, "-D", symbols)
    transition(state, "IPA_READY", artifact=result, run_url=info["url"],
               tests={"unit": "PASS", "ui": "PASS", "total": summary["passedTests"]})
    return True


def watch(state):
    deadline = time.monotonic() + 35 * 60
    previous = None
    while time.monotonic() < deadline:
        info = run_info(state["run_id"])
        if info["status"] != previous:
            print(json.dumps({"run_id": state["run_id"], "ci_status": info["status"]}), flush=True)
            previous = info["status"]
        if info["status"] == "completed":
            return fetch(state, state["run_id"], state["commit_sha"], state["version"])
        time.sleep(20)
    transition(state, "FAILED", error="CI monitoring timeout; existing run was not canceled")
    return False


def prepare_install(state, open_folder):
    verifier.require(state["phase"] in ("IPA_READY", "NEEDS_USER_ACTION"), "Verified IPA required")
    artifact = state["artifact"]
    result = verifier.verify(Path(artifact["ipa"]).parent, artifact["commit_sha"], artifact["run_id"],
                             artifact["version"], artifact["repository"], artifact["attempt"])
    directory = OUTPUT / "install-next" / state["request_id"]
    directory.mkdir(parents=True, exist_ok=True)
    selected = directory / f"INSTALL-FactoryHello-v{result['version']}-build{result['build']}.ipa"
    if selected.exists():
        import hashlib
        verifier.require(hashlib.sha256(selected.read_bytes()).hexdigest() == result["sha256"],
                         "Existing install copy checksum mismatch")
    else:
        shutil.copy2(result["ipa"], selected)
    instructions = (f"Factory Hello {result['version']} ({result['build']})\n"
                    f"Source: {result['commit_sha']}\nSHA256: {result['sha256']}\n\n"
                    "Use the same Apple Account and the same app. Do not delete the installed app.\n"
                    "In iloader, select your iPhone and Import IPA, then select this folder's only IPA.\n"
                    "Personally handle authentication; stop at certificate revocation prompts.\n"
                    "Report actual phone version, launch, and retained data.\n")
    (directory / "INSTALL-NEXT.txt").write_text(instructions, encoding="utf-8")
    transition(state, "NEEDS_USER_ACTION", install_ipa=str(selected),
               next_action="Import this exact IPA in iloader; authentication and device acceptance by owner")
    if open_folder:
        verifier.require(os.name == "nt", "Explorer launch is Windows-only")
        subprocess.Popen(["explorer.exe", f'/select,{selected}'])


def record_device(state, version, count, relaunch_count, evidence):
    verifier.require(state.get("artifact", {}).get("version") == version, "Device version mismatch")
    verifier.require(count == relaunch_count, "Relaunch did not retain data")
    verifier.require(bool(evidence.strip()), "User evidence required")
    verifier.require(state["phase"] == "INSTALLED", "Record installation before device acceptance")
    transition(state, "DEVICE_VERIFIED", signing="PASS_DEVICE_CONFIRMED",
               installation="PASS_DEVICE_CONFIRMED", device_launch="PASS_USER_CONFIRMED",
               device_version=version, count=count, relaunch_count=relaunch_count,
               device_evidence=evidence)


def record_install(state, outcome, evidence):
    verifier.require(bool(evidence.strip()), "Observed tool evidence required")
    verifier.require(state["phase"] in ("NEEDS_USER_ACTION", "SIGNING", "INSTALLING"),
                     "Prepare the exact IPA before recording installation")
    if outcome == "installed":
        transition(state, "INSTALLED", signing="PASS_TOOL_REPORTED",
                   installation="PASS_TOOL_REPORTED", install_evidence=evidence)
    elif outcome == "needs-auth":
        transition(state, "NEEDS_USER_ACTION", next_action="Owner authentication required",
                   install_evidence=evidence)
    elif outcome == "failed":
        transition(state, "FAILED", installation="FAILED", install_evidence=evidence)
    else:
        transition(state, outcome.upper(), install_evidence=evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    new = sub.add_parser("request")
    new.add_argument("--text", required=True)
    for action in ("build", "fetch", "watch", "prepare-install", "record-install", "record-device", "status"):
        command = sub.add_parser(action)
        command.add_argument("--request-id", required=True)
        if action in ("build", "fetch"):
            command.add_argument("--commit", required=True)
            command.add_argument("--version", required=True)
        if action == "build":
            command.add_argument("--ref", default="main")
            command.add_argument("--no-wait", action="store_true")
        if action == "fetch":
            command.add_argument("--run-id", required=True)
        if action == "prepare-install":
            command.add_argument("--open-folder", action="store_true")
        if action == "record-device":
            command.add_argument("--version", required=True)
            command.add_argument("--count", type=int, required=True)
            command.add_argument("--relaunch-count", type=int, required=True)
            command.add_argument("--evidence", required=True)
        if action == "record-install":
            command.add_argument("--outcome", required=True,
                                 choices=("signing", "installing", "installed", "needs-auth", "failed"))
            command.add_argument("--evidence", required=True)
    args = parser.parse_args()
    state = None
    try:
        if args.action == "request":
            new_request(args.text)
            return 0
        state = read_state(args.request_id)
        if args.action == "build":
            build(state, args.ref, args.commit, args.version, args.no_wait)
        elif args.action == "fetch":
            return 0 if fetch(state, args.run_id, args.commit, args.version) else 1
        elif args.action == "watch":
            return 0 if watch(state) else 1
        elif args.action == "prepare-install":
            prepare_install(state, args.open_folder)
        elif args.action == "record-device":
            record_device(state, args.version, args.count, args.relaunch_count, args.evidence)
        elif args.action == "record-install":
            record_install(state, args.outcome, args.evidence)
        else:
            print(json.dumps(state, indent=2, ensure_ascii=False))
        return 1 if state["phase"] == "FAILED" else 0
    except (OSError, ValueError, RuntimeError, KeyError, zipfile.BadZipFile) as error:
        if state is not None and args.action != "status":
            transition(state, "FAILED", error=str(error))
        else:
            print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
