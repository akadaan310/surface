# Surface Recovery 0.1.1

Surface is native physical ink: an original C++ CPU renderer, numerical models,
audio and state persistence, with a small Android lifecycle bridge. The user
reported that release 0.1.0 immediately crashed on launch. This release repairs
a reproduced Java/JNI startup defect. **The repaired APK has not yet been
executed on an Android device; successful phone launch remains unverified.**

## Install the recovery build

| Item | Value |
|---|---|
| Delivered APK | `Surface-Recovery-0.1.1-arm64.apk` |
| Device target | ARM64, Android 10 / API 29 or later |
| Launcher name | **Surface Recovery** |
| Application ID | `org.surface.nativeink.recovery` |
| Activity class | `org.surface.nativeink.SurfaceActivity` |
| APK size | 1,369,050 bytes |
| SHA-256 | `eb430f4a71f296059901fd383edf8f128c0b4795c2df737eb1ef99e1d98ab120` |

Install the delivered APK and open **Surface Recovery**. It installs beside the
old Surface app. The original signing key was unavailable after the working
environment disappeared, so the recovery build uses a new development key,
authorized by the user and privately backed up with matching round-trip bytes.
That credential is excluded from source. Existing app-private checkpoints are
not automatically migrated between application IDs; keep the old installation
and any exported `.surface` files.

The manifest requests no permissions. The renderer, models and data remain
local, without a browser or third-party rendering engine. The repair reuses the
byte-exact native library and assets from 0.1.0 to isolate the Java change.

## Evidence and use

The actual Activity failed its first native call before the fix and passed the
same host-JVM probe after adding `System.loadLibrary("surface")`. Both native
callbacks resolved, with exact dimensions and callback counts. Fourteen static
package checks passed. These results establish the loading repair and package
integrity, not Android lifecycle or device performance. See
[STARTUP_REPAIR.md](docs/STARTUP_REPAIR.md) and the
[package receipt](evidence/startup-repair-build.json).

Gestures remain: one-finger paint/sky rotation; two-finger tap to cycle seven
observations; two-finger drag for negative input; sky pinch to zoom; three-finger
tap to pause; four-finger tap to export; double tap for sound. Keyboard controls
are 1–7, Space, M and E/S. These interactions require device verification.

Physics, calibration limits, the 10,000-source Gaia slice, recovery guarantees
and all original scientific gates are unchanged. The earlier nine native suites,
fourteen supervisor tests and 145 foundation tests are preserved historical
evidence, not newly rerun claims. Start with [NATIVE_RESUME.md](NATIVE_RESUME.md).

## Reproduce the repair

```sh
python3 tools/test_android_startup.py \
  --android-jar ../android-toolchain/android-36/android.jar --phase check
python3 tools/build_startup_repair.py --toolchain ../android-toolchain \
  --keystore /private/path/surface-recovery.keystore
```

This repair builder needs Java 17, the pinned Android platform/build tools, and
the preserved native ELF; it does not need an NDK rebuild. A full native rebuild
remains a separate operation. The source package's new `SOURCE_MANIFEST.json`
and `RELEASE.json` identify this checkpoint. Unchanged 0.1.0 root documents are
retained under `lineage/release-0.1.0/`; their old signing/delivery statements are
historical. Source recovery verified all 115 prior tracked files exactly.
