"""Package an unsigned arm64 archive; signing compatibility requires device testing."""
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

assert Path("build/evidence/TEST_PASSED").is_file(), "Tests have not passed"
archive = Path("build/FactoryHello.xcarchive")
apps = list((archive / "Products/Applications").glob("*.app"))
assert len(apps) == 1, "Expected one archived app"
app = apps[0]
with (app / "Info.plist").open("rb") as handle:
    info = plistlib.load(handle)
assert info["CFBundleIdentifier"] == "com.aifactory.helloiphone.a7e4c921"
assert info["CFBundleSupportedPlatforms"] == ["iPhoneOS"]
assert str(info["CFBundleVersion"]) == os.environ["GITHUB_RUN_NUMBER"]
executable = app / info["CFBundleExecutable"]
architectures = subprocess.check_output(["lipo", "-archs", str(executable)], text=True).split()
assert architectures == ["arm64"], architectures
release = Path("build/release")
release.mkdir(parents=True, exist_ok=False)
stage = Path("build/ipa-stage")
(stage / "Payload").mkdir(parents=True, exist_ok=False)
shutil.copytree(app, stage / "Payload" / app.name, symlinks=True)
name = f"FactoryHello-{info['CFBundleShortVersionString']}-{info['CFBundleVersion']}-unsigned.ipa"
ipa = release / name
subprocess.run(["ditto", "-c", "-k", "--keepParent", "Payload", str(ipa.resolve())], cwd=stage, check=True)
with zipfile.ZipFile(ipa) as zipped:
    assert zipped.testzip() is None, "Corrupt IPA"
    assert f"Payload/{app.name}/Info.plist" in zipped.namelist()
    assert f"Payload/{app.name}/{info['CFBundleExecutable']}" in zipped.namelist()
manifest = {
    "app_name": "Factory Hello",
    "bundle_id": info["CFBundleIdentifier"],
    "app_version": info["CFBundleShortVersionString"],
    "build_number": str(info["CFBundleVersion"]),
    "commit_sha": os.environ["GITHUB_SHA"],
    "workflow_run_id": os.environ["GITHUB_RUN_ID"],
    "workflow_run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
    "repository": os.environ["GITHUB_REPOSITORY"],
    "xcode_version": Path("build/evidence/xcode.txt").read_text().strip(),
    "xcodegen_version": Path("build/evidence/xcodegen.txt").read_text().strip(),
    "runner_image": Path("build/evidence/runner.txt").read_text().strip(),
    "test_status": "PASS",
    "ipa_file": name,
    "ipa_sha256": hashlib.file_digest(ipa.open("rb"), "sha256").hexdigest(),
    "architectures": architectures,
    "signing_status": "UNSIGNED",
    "device_status": "NOT_TESTED",
    "created_at": datetime.now(timezone.utc).isoformat(),
}
(release / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
