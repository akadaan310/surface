# Surface — native physical ink

Surface is a fullscreen native Android application whose visible content is ink. Drawing deposits material and energy into a bounded numerical field; Surface's original C++ CPU renderer turns the resulting fields into pixels. The Android layer uses a small Java lifecycle shim for system bars, window dimensions and document intents. Simulation, rendering, audio and persistence are C++.

This is a **fresh native release**, version 0.1.0. The earlier lost session's source, URL and outstanding jobs were not recovered. The supplied scientific foundation was preserved and replayed separately; the new application is not presented as a reconstruction of unsaved work.

## Release and current verification

| Item | Current result |
|---|---|
| Android package | `org.surface.nativeink` |
| Supported APK target | ARM64 (`arm64-v8a`), Android 10 / API 29 or later |
| APK | `build/Surface-arm64.apk`, 1,369,050 bytes |
| APK SHA-256 | `0a6f32c450c931699eaf75778c5e7d1fae1b5cfc1123d32aeac93d5f46a2f8da` |
| Android verification | Native compilation/linking, signature, ZIP/16 KiB ELF alignment and all 10 static package checks passed |
| Android device execution | **Not performed**: no physical device or emulator was available |
| Current host verification | **9 native C++ test executables and 14 Python supervisor tests passed** |
| Preserved foundation | **145 original unit tests passed; 125 deterministic files regenerated exactly** |

The APK uses a development signing certificate. A separate signing-key backup exists locally, but automatic approval review blocked transmitting that credential without explicit user authorization. It is not included in the delivered files or source archive. Preserving that key is needed for compatible future updates; the APK can be installed without possessing it. The manifest requests no internet permission. Catalogue data and scientific tables are packaged locally. There is no browser, WebView, WebGL or external rendering engine in the application.

The APK and source archive are direct deliverables. No usable published site URL exists for this release. [Android build evidence](evidence/android-build.json), [static package verification](evidence/android-package-verification.json), [native test evidence](evidence/headless-build.json) and the [foundation replay receipt](evidence/foundation-replay.json) support the results above. The source ZIP's `SOURCE_MANIFEST.json` and `RELEASE.json` record the actual local Git revision and exact path hashes. The larger science commission remains open; consult [GATE_REPORT.md](docs/GATE_REPORT.md) and [commission-gates.json](evidence/commission-gates.json) for the exact accepted scopes and remaining requirements.

## Install and interact

Install the delivered `Surface-0.1.0-arm64.apk` on a compatible ARM64 Android device. Android may ask you to allow installation from the application handling the file. In a local build the same artifact is named `build/Surface-arm64.apk`; the source ZIP excludes generated builds. Copy the delivered APK to that path, or substitute its actual path below. With an authorized ADB device, the equivalent commands are:

```sh
adb install -r build/Surface-arm64.apk
adb shell am start -n org.surface.nativeink/.SurfaceActivity
```

These commands describe the next device check; they were not executed against a device for this release. Open Surface to enter the ink field. Instructions remain here so the application can stay visually uninterrupted.

| Gesture | Action |
|---|---|
| One-finger touch and drag | Paint; rotate the sky in cosmos mode |
| Two-finger short tap | Cycle the observation |
| Two-finger drag | Apply a negative field/material input; rotate the sky in cosmos mode |
| Pinch in cosmos mode | Change sky zoom |
| Three-finger short tap | Pause or resume |
| Four-finger short tap | Export an acknowledged state to `Downloads/Surface` |
| One-finger double tap | Toggle sound |

The observation cycle is coupled, magnetic, acoustic, thermal, electric, optical, then cosmos. A connected keyboard can select these with **1–7**, pause with **Space**, toggle sound with **M**, and export with **E** or **S**. The Android implementation distinguishes pinch/drag travel from a tap; device gesture and lifecycle behavior still needs the execution check described below.

State export uses Android's Downloads provider, with an app-files fallback if provider publication fails. The app accepts supported `.surface` documents through Android's `ACTION_VIEW` handoff with MIME type `application/x-surface-checkpoint`; file-manager association and actual Downloads/import behavior are part of the open device gate.

## What runs locally

- **Physical fields:** bounded wave propagation, heat transport, analytic electric/magnetic sources, reduced circuit/battery coupling and magnetic memory. Units, regularization, stability assumptions and calibration limits are in [PHYSICS.md](docs/PHYSICS.md).
- **Image formation:** original CPU streamline tracing, field sampling, compositing and pixel encoding. The official CIE 1931 observer table supplies spectral color transforms. Glow, exposure and trail persistence are declared display choices.
- **Sound:** native modal acoustic reference with AAudio output on Android. Amplitude mapping is a numerical observation transform, not calibrated speaker pressure.
- **Astronomy:** 10,000 actual Gaia DR3 sources, exact uint64 identifiers, ICRS J2016.0 coordinates and explicit missing measurements. No stellar distances are invented. The dataset is a bounded catalogue slice; see [ATLAS.md](docs/ATLAS.md).
- **PHANTOM/Quantum Oracle references:** exact finite word transitions, loss-aware binary records, pulse codecs and bounded classical state-vector operations. These library references do not make the ink solver quantum hardware; see [PHANTOM.md](docs/PHANTOM.md).
- **Recovery:** an ordered native engine thread, acknowledged state barriers, two retained checkpoint slots and owner/generation fencing. The independent host supervisor bounds finite research/build processes; see [RECOVERY.md](docs/RECOVERY.md).

Portable `SURFEXP1` exports carry a SHA-256 integrity check over the modeled session. Host tests verify exact same-build physics continuation and atomic rejection of malformed state. Renderer trail history and acoustic oscillator phase are not serialized; replay therefore does not promise an identical historical framebuffer or audio phase. Whole-process/OS failure before the next committed checkpoint is outside the in-process recovery guarantee.

## Build and reproduce

The native host build needs a C++20 compiler, pthreads and Python's standard library:

```sh
python3 tools/build_native.py --test
build/surface --demo --frames 60 --width 720 --height 1280 \
  --output build/previews/coupled.ppm --save build/previews/demo.surface \
  --report evidence/headless-coupled.json
```

The host executable renders through the same numerical and rasterization modules. [CLI.md](docs/CLI.md) documents every mode, bounds, portable import/export, audio output and measured host timing. Preview PNGs are file-format conversions of actual native PPM output, not generated illustrations. Host timing is not Android-device performance evidence.

The APK builder uses the official pinned Android NDK r30, build tools 36 and API 36 platform recorded in [android-toolchain.json](evidence/android-toolchain.json). Those large toolchain packages are not included in the source archive:

```sh
python3 tools/build_android.py --toolchain /path/to/android-toolchain \
  --keystore /path/to/preserved-development.keystore
python3 tools/verify_android.py --toolchain /path/to/android-toolchain
```

Use the expected directory layout in `tools/build_android.py` and preserve the existing signing identity. Static package verification checks the packaged native library and JNI symbols, Android platform-only shared-library dependencies, permissions, signature and alignment; it is not device execution. Transfer of the separate development-key backup awaits explicit authorization; do not assume it will survive loss of this working environment. [FOUNDATION_REPLAY.md](docs/FOUNDATION_REPLAY.md) provides the independent original-code replay commands and retained raw logs. That Python foundation is not a runtime dependency of the native app.

## Continue from evidence

Start with [NATIVE_RESUME.md](NATIVE_RESUME.md). The next integration gate is actual Android execution: installation, fullscreen launch, touch/keyboard input, pause/resume, resize, sound, Downloads export, import, process restart and measured device performance. Fresh baseline replay does not certify the lost eight Octave comparisons; those remain unknown. Full-corpus research, external quantum comparison, collider/hardware integration and the broader scientific requirements remain tracked separately.

The immutable `lineage/SURFACE_PHYSICAL_COSMOS_CONTINUATION_v1.zip` is retained in the source delivery. `lineage/surface-web-work-in-progress-20261025.zip` preserves the halted browser-stage work as historical recovery material, outside the native runtime. Gaia data retain **CC BY-NC 3.0 IGO** terms and ESA/Gaia/DPAC attribution; CIE table terms are in `data/CIE-LICENSE.md`. Code ownership and data licensing must not be conflated. External repository upload was blocked by automatic approval review because destination ownership and specific authorization were not established. Direct artifact delivery is the current authorized route.
