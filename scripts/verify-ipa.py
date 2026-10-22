"""Verify a specific unsigned device IPA without extracting it or reading credentials."""
import hashlib
import json
import plistlib
import re
import struct
import zipfile
from pathlib import Path, PurePosixPath

BUNDLE_ID = "com.aifactory.helloiphone.a7e4c921"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(folder, commit, run_id, version, repository, attempt):
    folder = Path(folder)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8-sig"))
    for key, expected in {
        "commit_sha": commit, "workflow_run_id": str(run_id),
        "workflow_run_attempt": str(attempt), "repository": repository,
        "app_version": version, "bundle_id": BUNDLE_ID,
        "test_status": "PASS", "signing_status": "UNSIGNED",
    }.items():
        require(manifest.get(key) == expected, f"Manifest mismatch: {key}")
    name = manifest.get("ipa_file", "")
    require(bool(name) and name.endswith(".ipa") and
            not any(c in name for c in "/\\:") and name not in (".", ".."),
            "Unsafe IPA filename")
    digest = manifest.get("ipa_sha256", "")
    require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "Invalid checksum")
    ipa = folder / name
    with ipa.open("rb") as handle:
        actual = hashlib.file_digest(handle, "sha256").hexdigest()
    require(actual == digest, "IPA checksum mismatch")
    with zipfile.ZipFile(ipa) as archive:
        entries = archive.infolist()
        names = [item.filename for item in entries]
        require(len(names) == len(set(names)), "Duplicate ZIP paths")
        require(len(names) <= 10000 and sum(x.file_size for x in entries) <= 1500 * 1024**2,
                "IPA exceeds validation limits")
        for name_in_zip in names:
            path = PurePosixPath(name_in_zip)
            require(not path.is_absolute() and ".." not in path.parts and
                    "\\" not in name_in_zip and ":" not in name_in_zip,
                    "Unsafe ZIP path")
        require(archive.testzip() is None, "Corrupt IPA")
        plists = [n for n in names if n.startswith("Payload/") and n.count("/") == 2
                  and n.endswith(".app/Info.plist")]
        require(len(plists) == 1, "Expected one main app")
        info = plistlib.loads(archive.read(plists[0]))
        for key, expected in {
            "CFBundleIdentifier": BUNDLE_ID, "CFBundleShortVersionString": version,
            "CFBundleSupportedPlatforms": ["iPhoneOS"],
        }.items():
            require(info.get(key) == expected, f"App plist mismatch: {key}")
        require(str(info.get("CFBundleVersion")) == manifest.get("build_number"),
                "App build number mismatch")
        executable = info.get("CFBundleExecutable", "")
        require(executable and not any(c in executable for c in "/\\:"),
                "Unsafe executable filename")
        binary = archive.read(plists[0].removesuffix("Info.plist") + executable)
        require(len(binary) >= 32, "Truncated Mach-O")
        magic, cpu, _, filetype, commands, command_bytes, _, _ = struct.unpack_from("<8I", binary)
        require((magic, cpu, filetype) == (0xFEEDFACF, 0x0100000C, 2),
                "Expected thin arm64 executable")
        require(32 + command_bytes <= len(binary) and commands <= command_bytes // 8,
                "Invalid Mach-O command bounds")
        position, platform = 32, None
        for _ in range(commands):
            require(position + 8 <= 32 + command_bytes, "Truncated load command")
            command, size = struct.unpack_from("<II", binary, position)
            require(size >= 8 and position + size <= 32 + command_bytes,
                    "Invalid load command")
            if command == 0x32:
                require(size >= 24, "Truncated build version command")
                platform = struct.unpack_from("<I", binary, position + 8)[0]
            position += size
        require(position == 32 + command_bytes and platform == 2,
                "Mach-O is not an iOS device build")
    return {"ipa": str(ipa.resolve()), "sha256": actual, "commit_sha": commit,
            "run_id": str(run_id), "attempt": str(attempt), "repository": repository,
            "version": version, "build": manifest["build_number"], "bundle_id": BUNDLE_ID,
            "platform": "iOS device arm64", "validation": "PASS"}
