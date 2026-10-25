# Resume Surface Recovery 0.1.1

## Current checkpoint

Read `README.md`, `docs/STARTUP_REPAIR.md`, the current `SOURCE_MANIFEST.json` and
`RELEASE.json`, then `evidence/startup-repair-build.json`. Preserve the original
PHANTOM archives, scientific evidence, exact data encodings and native-renderer
requirement. Do not restore browser rendering or reinterpret old baseline
documents as the current release state.

The user reported an immediate launch crash in 0.1.0. The actual Activity's JNI
declarations reproduced `UnsatisfiedLinkError` on the host JVM. A single static
`System.loadLibrary("surface")` initializer made the unchanged probe pass.
The APK contains the same compiled Activity class as that passing regression;
its native ELF and all data assets match the preceding release exactly.

Current artifact: `Surface-Recovery-0.1.1-arm64.apk`, 1,369,050 bytes, SHA-256
`eb430f4a71f296059901fd383edf8f128c0b4795c2df737eb1ef99e1d98ab120`.
Its application ID is `org.surface.nativeink.recovery`; its fully qualified
activity remains `org.surface.nativeink.SurfaceActivity`. **Phone launch of
0.1.1 remains unverified.** Fourteen static package checks and the host JNI
regression are narrower evidence.

The old key disappeared with the previous working environment and no saved
copy was recovered. The user authorized private key backup. A replacement
development key was created, privately saved and byte-verified. Restore that
approved backup privately for future recovery-app updates. Never include the
credential or its private file identifier in shared source. This is a separate
application identity; it cannot update the old installation signed by the lost
key. Keep that installation and any exported state.

## First unfinished gate: Android launch

Use the delivered APK before changing more code. Record device/API/ABI, APK
hash, launch result and any actual crash stack. With an authorized ADB device,
substitute the APK's real path if it is outside the build directory:

```sh
adb install -r build/startup-repair/Surface-Recovery-0.1.1-arm64.apk
adb shell am start -W -n \
  org.surface.nativeink.recovery/org.surface.nativeink.SurfaceActivity
```

Confirm that the activity stays open, lays out its native surface and renders a
frame. Then exercise paint, observation switching, pause/background/resume,
sound, resize, export/import and checkpoint relaunch. Distinguish committed
state from input lost before a save. Record measured performance separately.
If launch still fails, obtain the exception/signal and investigate that failure;
do not claim that the host result proves the phone crash is fully resolved.

The source archive excludes generated APKs. Preserve the historical RED/GREEN
receipts; use `--phase check` for a new current-source JNI run:

```sh
python3 tools/test_android_startup.py \
  --android-jar ../android-toolchain/android-36/android.jar --phase check
python3 tools/build_startup_repair.py --toolchain ../android-toolchain \
  --keystore /private/path/surface-recovery.keystore
```

The builder pins `lineage/Surface-0.1.0-libsurface.so`, verifies the passing Java
source/class witness, and requires the existing recovery key. It does not
generate a replacement key or compile a new native engine. Restoring a full
NDK toolchain is necessary only for a later native-code change.

## Preservation and remaining work

All 115 tracked files from the previous manifest were recovered with exact
hashes. The received ZIP carrier lacked its central directory and trailing
untracked example, while the tracked local file records remained intact.
Repaired/new ZIP carriers have new archive identities; do not reuse the old
archive hash. The old root README/resume are unchanged under
`lineage/release-0.1.0/`. Read recovery receipts for the exact distinction between
source recovery, carrier repair and any subsequent changes.

All scientific gates remain as assessed in `docs/GATE_REPORT.md` and
`evidence/commission-gates.json`. In particular, the old eight Octave witnesses,
full COMPOSER/Oracle contracts, calibration work, N-chart topology, real pulsar
timing and large-catalogue ingestion remain open. The original laboratory URL
and unknown remote jobs were not recovered. No public site is established.

Use bounded, journaled jobs with fixed deadlines, explicit progress/evidence
and fenced publication. Do not rerun unchanged broad science merely to repair
this Java boundary. External repository upload remains unauthorized after its
earlier automatic-review rejection; native artifact delivery and the explicitly
authorized private key backup are separate routes.
