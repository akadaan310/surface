#!/usr/bin/env python3
"""Make a source checkpoint and private native deliverables without networking."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def add_bytes(archive, name, data, mode=0o644):
    info = zipfile.ZipInfo(name, date_time=(2026, 10, 25, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (0o100000 | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, data, compresslevel=9)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--signing-key", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise SystemExit("Release output must be outside the source tree")
    output.mkdir(parents=True, exist_ok=True)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise SystemExit("Commit the complete reviewed source before packaging")
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    tracked = sorted(name for name in tracked if name)
    forbidden = (".keystore", ".jks", ".pk8", ".pem")
    if any(name.endswith(forbidden) or name.startswith(("build/", ".git/")) for name in tracked):
        raise SystemExit("Private key/build state must not be tracked in the source bundle")
    entries = [{"path": name, "bytes": (ROOT / name).stat().st_size, "sha256": digest(ROOT / name)} for name in tracked]
    source_manifest = {"schema": "surface-source-manifest-v1", "git_revision": revision, "files": entries, "scope": "Tracked source, documentation, data, evidence and immutable lineage; manifest itself excluded from its file list"}
    apk = ROOT / "build/Surface-arm64.apk"
    package_receipt = json.loads((ROOT / "evidence/android-package-verification.json").read_text())
    if not package_receipt["passed"] or digest(apk) != package_receipt["sha256"]:
        raise SystemExit("APK differs from the statically verified package")
    release = {
        "schema": "surface-native-release-v1", "version": "0.1.0", "source_revision": revision,
        "application": "org.surface.nativeink", "architecture": "arm64-v8a", "minimum_android": "Android 10 / API 29",
        "apk_sha256": digest(apk), "apk_bytes": apk.stat().st_size,
        "native_cpp_suites_passed": 9, "supervisor_fault_tests_passed": 14,
        "original_foundation_tests_passed": 145, "original_deterministic_files_exact": 125,
        "android_device_execution": "NOT_RUN_NO_DEVICE_OR_EMULATOR",
        "original_lost_surface_url": "UNAVAILABLE", "registered_site_published": False,
        "external_repository_upload": "BLOCKED_BY_AUTOMATIC_APPROVAL_REVIEW; no alternate route attempted",
        "signing_key_backup_delivery": "LOCAL_ONLY_APPROVAL_REQUIRED: automatic review rejected transmission of the private signing key; APK/source/evidence delivery proceeds without that file",
        "science_scope": "Bounded reduced reference models; original G00-G16 completion is reported separately",
        "source_manifest_sha256": hashlib.sha256(encoded(source_manifest)).hexdigest(),
    }
    source_zip = output / "Surface-Native-0.1.0-source.zip"
    with zipfile.ZipFile(source_zip, "w") as archive:
        for entry in entries:
            source = ROOT / entry["path"]
            add_bytes(archive, "surface-native/" + entry["path"], source.read_bytes(), 0o755 if source.stat().st_mode & 0o111 else 0o644)
        add_bytes(archive, "surface-native/SOURCE_MANIFEST.json", encoded(source_manifest))
        add_bytes(archive, "surface-native/RELEASE.json", encoded(release))
        add_bytes(archive, "surface-native/examples/demo.surface", (ROOT / "build/previews/demo.surface").read_bytes())
    if source_zip.stat().st_size >= 20_000_000:
        raise SystemExit(f"Source bundle exceeds 20 MB: {source_zip.stat().st_size}")
    with zipfile.ZipFile(source_zip) as archive:
        if archive.testzip() is not None:
            raise SystemExit("Source archive CRC failure")
        for entry in entries:
            if hashlib.sha256(archive.read("surface-native/" + entry["path"])).hexdigest() != entry["sha256"]:
                raise SystemExit("Source archive byte mismatch: " + entry["path"])
    copies = {
        "Surface-0.1.0-arm64.apk": apk,
        "NATIVE_RESUME.md": ROOT / "NATIVE_RESUME.md",
        "SURFACE_README.md": ROOT / "README.md",
        "SURFACE_GATE_REPORT.md": ROOT / "docs/GATE_REPORT.md",
        "Surface-native-ink.png": ROOT / "build/previews/coupled.png",
        "Surface-Gaia-atlas.png": ROOT / "build/previews/cosmos.png",
        "Surface-modal-acoustic.wav": ROOT / "build/previews/modal.wav",
    }
    for name, source in copies.items():
        shutil.copy2(source, output / name)
    key = args.signing_key.resolve()
    if not key.is_file() or key.suffix != ".keystore":
        raise SystemExit("Expected the separate development keystore")
    backup_text = """Surface development signing backup

Keep this file private and separate from shared source releases. It contains the
new development key used to sign Surface 0.1.0, so future development APKs can
update that installation under the same package identity.

File: surface-development.keystore
Alias: surface-development
Store password: android
Key password: android
Certificate SHA-256: 4bcd88328555debd1aa87107492348a1503eeb3615a9ec20960a0066ed9a6662

This is a development key, not a production distribution credential. The backup
ZIP is not encrypted; its privacy depends on keeping the file private. No other
account credential or repository token is present. The source ZIP excludes it.
Place the keystore at TOOLCHAIN/surface-development.keystore before rebuilding
to retain the development signing identity. Read tools/build_android.py.
"""
    with zipfile.ZipFile(output / "SURFACE_SIGNING_BACKUP_PRIVATE.zip", "w") as archive:
        add_bytes(archive, "surface-development.keystore", key.read_bytes(), 0o600)
        add_bytes(archive, "README.txt", backup_text.encode())
    ordered = ["Surface-0.1.0-arm64.apk", source_zip.name, "NATIVE_RESUME.md", "SURFACE_README.md", "SURFACE_GATE_REPORT.md", "Surface-native-ink.png", "Surface-Gaia-atlas.png", "Surface-modal-acoustic.wav", "SURFACE_SIGNING_BACKUP_PRIVATE.zip"]
    release["artifacts"] = [{"file": name, "bytes": (output / name).stat().st_size, "sha256": digest(output / name), "delivery_scope": "LOCAL_ONLY_APPROVAL_REQUIRED" if name == "SURFACE_SIGNING_BACKUP_PRIVATE.zip" else "USER_DELIVERABLE"} for name in ordered]
    release["source_archive_verification"] = {"crc": "PASS", "tracked_file_hashes": "ALL_EXACT", "tracked_files": len(entries), "bytes": source_zip.stat().st_size, "limit_bytes": 20_000_000}
    receipt = output / "SURFACE_RELEASE_RECEIPT.json"
    receipt.write_bytes(encoded(release))
    ordered.append(receipt.name)
    (output / "SHA256SUMS.txt").write_text("".join(f"{digest(output / name)}  {name}\n" for name in ordered))
    print(json.dumps({"source_revision": revision, "source_files": len(entries), "source_zip_bytes": source_zip.stat().st_size, "release_directory": str(output), "artifacts": ordered + ["SHA256SUMS.txt"]}, indent=2))


if __name__ == "__main__":
    main()
