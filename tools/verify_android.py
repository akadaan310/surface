#!/usr/bin/env python3
"""Bounded, static verification of the native ARM64 package; no device claim."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--toolchain", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    toolchain = args.toolchain.resolve()
    apk = root / "build/Surface-arm64.apk"
    library = root / "build/android/libsurface.so"
    elf_reader = shutil.which("readelf")
    if not elf_reader:
        raise SystemExit("A host readelf executable is required for static ELF inspection")
    commands = {
        "signature": [str(toolchain / "android-16/apksigner"), "verify", "--verbose", "--print-certs", str(apk)],
        "alignment": [str(toolchain / "android-16/zipalign"), "-c", "-v", "4", str(apk)],
        "manifest": [str(toolchain / "android-16/aapt2"), "dump", "badging", str(apk)],
        "elf": [elf_reader, "--wide", "--file-header", "--program-headers", "--dynamic", "--dyn-syms", str(library)],
    }
    results = {}
    outputs = {}
    for name, command in commands.items():
        completed = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=30)
        outputs[name] = completed.stdout + completed.stderr
        path = root / f"evidence/android-{name}.txt"
        path.parent.mkdir(exist_ok=True)
        path.write_text(outputs[name])
        results[name] = {"command": command, "exit_code": completed.returncode, "evidence": str(path.relative_to(root))}
        if completed.returncode:
            raise SystemExit(f"{name} verification failed; see {path}")
    manifest = outputs["manifest"]
    elf = outputs["elf"]
    needed = [line.strip() for line in elf.splitlines() if "(NEEDED)" in line]
    exports = [name for name in (
        "ANativeActivity_onCreate",
        "Java_org_surface_nativeink_SurfaceActivity_nativeDimensions",
        "Java_org_surface_nativeink_SurfaceActivity_nativeOpen",
    ) if name in elf]
    platform_libraries = ("libandroid.so", "liblog.so", "libaaudio.so", "libm.so", "libdl.so", "libc.so")
    checks = {
        "arm64_package": "native-code: 'arm64-v8a'" in manifest,
        "minimum_api_29": "minSdkVersion:'29'" in manifest or "sdkVersion:'29'" in manifest,
        "no_requested_permissions": "uses-permission:" not in manifest,
        "native_arm64_elf": "AArch64" in elf,
        "elf_16k_page_alignment": all(line.rstrip().endswith("0x4000") for line in elf.splitlines() if line.strip().startswith("LOAD")),
        "only_platform_dynamic_libraries": bool(needed) and all(any(f"[{name}]" in line for name in platform_libraries) for line in needed),
        "native_and_jni_entry_points": len(exports) == 3,
    }
    with zipfile.ZipFile(apk) as archive:
        checks["archive_crc"] = archive.testzip() is None
        libraries = [name for name in archive.namelist() if name.startswith("lib/")]
        checks["one_owned_renderer_library"] = libraries == ["lib/arm64-v8a/libsurface.so"]
        checks["packaged_library_matches_inspected_elf"] = archive.read("lib/arm64-v8a/libsurface.so") == library.read_bytes()
        entries = len(archive.namelist())
    result = {
        "passed": all(checks.values()),
        "artifact": "build/Surface-arm64.apk",
        "bytes": apk.stat().st_size,
        "sha256": hashlib.sha256(apk.read_bytes()).hexdigest(),
        "checks": checks,
        "verification": results,
        "libraries": libraries,
        "elf_needed": needed,
        "entry_points_observed": exports,
        "archive_entries": entries,
        "runtime_permissions": [],
        "device_execution": "NOT_RUN_NO_DEVICE_OR_EMULATOR",
        "scope": "Package, ELF and signature checks only; not Android runtime acceptance",
    }
    (root / "evidence/android-package-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("passed", "bytes", "sha256", "checks", "device_execution")}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
