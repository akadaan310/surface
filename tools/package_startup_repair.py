#!/usr/bin/env python3
"""Checkpoint the narrowly verified startup repair without private credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def add(archive, name, payload):
    info = zipfile.ZipInfo(name, date_time=(2026, 10, 25, 0, 0, 0))
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, payload, compresslevel=9)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    target = args.output.resolve()
    if target == ROOT or ROOT in target.parents:
        raise SystemExit('Output must be outside source tree')
    target.mkdir(parents=True, exist_ok=True)
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip():
        raise SystemExit('Commit the reviewed repair before packaging')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    paths = sorted(p for p in subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0') if p)
    if any(p.endswith(('.keystore', '.jks', '.pk8', '.pem')) for p in paths):
        raise SystemExit('Private credential in source file set')
    if 'SOURCE_MANIFEST.json' in paths or 'RELEASE.json' in paths:
        raise SystemExit('Historical generated manifests must live under lineage; avoid duplicate ZIP entries')
    files = [{'path': p, 'bytes': (ROOT / p).stat().st_size, 'sha256': sha(ROOT / p)} for p in paths]
    manifest = {'schema': 'surface-source-manifest-v1', 'git_revision': revision, 'recovered_baseline_revision': 'b16a63a8fc9466c93f9233d0a45bd3840ac39536', 'files': files}
    build = json.loads((ROOT / 'evidence/startup-repair-build.json').read_text())
    apk = ROOT / build['artifact']
    if not build['passed'] or sha(apk) != build['sha256']:
        raise SystemExit('Repair APK does not match passing build receipt')
    release = {
        'schema': 'surface-startup-repair-release-v1', 'version': '0.1.1', 'source_revision': revision,
        'application_id': build['application_id'], 'activity_class': build['activity_class'],
        'apk_sha256': build['sha256'], 'apk_bytes': build['bytes'], 'certificate_sha256': build['certificate_sha256'],
        'startup_regression': 'RED UnsatisfiedLinkError to GREEN exact callback witness on actual Java Activity class',
        'package_checks_passed': len(build['checks']), 'native_core': 'BYTE_IDENTICAL_TO_0.1.0',
        'private_signing_backup': 'Saved separately with explicit user authorization; exact downloaded bytes verified; excluded from this archive',
        'android_device_execution': 'NOT_RUN; user must confirm launch on their phone',
        'scientific_gate_changes': 'NONE; previous scoped evidence remains historical',
        'source_manifest_sha256': hashlib.sha256(json_bytes(manifest)).hexdigest(),
    }
    source = target / 'Surface-Recovery-0.1.1-source.zip'
    with zipfile.ZipFile(source, 'w') as archive:
        for entry in files:
            add(archive, 'surface-native/' + entry['path'], (ROOT / entry['path']).read_bytes())
        add(archive, 'surface-native/SOURCE_MANIFEST.json', json_bytes(manifest))
        add(archive, 'surface-native/RELEASE.json', json_bytes(release))
    if source.stat().st_size >= 20_000_000:
        raise SystemExit('Source archive exceeds 20 MB delivery bound')
    with zipfile.ZipFile(source) as archive:
        if archive.testzip() is not None:
            raise SystemExit('Archive CRC failed')
        if len(set(archive.namelist())) != len(archive.namelist()):
            raise SystemExit('Duplicate source archive members')
        for entry in files:
            if hashlib.sha256(archive.read('surface-native/' + entry['path'])).hexdigest() != entry['sha256']:
                raise SystemExit('Source member differs: ' + entry['path'])
    copies = {
        'Surface-Recovery-0.1.1-arm64.apk': apk,
        'SURFACE_STARTUP_REPAIR.md': ROOT / 'docs/STARTUP_REPAIR.md',
        'SURFACE_RECOVERY_README.md': ROOT / 'README.md',
        'SURFACE_RECOVERY_RESUME.md': ROOT / 'NATIVE_RESUME.md',
    }
    for name, original in copies.items():
        shutil.copy2(original, target / name)
    names = [*copies, source.name]
    release['source_verification'] = {'files': len(files), 'all_hashes_exact': True, 'crc': 'PASS', 'source_zip_bytes': source.stat().st_size}
    release['artifacts'] = [{'file': n, 'bytes': (target / n).stat().st_size, 'sha256': sha(target / n)} for n in names]
    receipt = target / 'SURFACE_RECOVERY_RELEASE.json'
    receipt.write_bytes(json_bytes(release))
    names.append(receipt.name)
    (target / 'SHA256SUMS.txt').write_text(''.join(f'{sha(target / name)}  {name}\n' for name in names))
    print(json.dumps({'source_revision': revision, 'source_files': len(files), 'source_zip_bytes': source.stat().st_size, 'files': names + ['SHA256SUMS.txt']}, indent=2))


if __name__ == '__main__':
    main()
