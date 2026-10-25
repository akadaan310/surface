# Resume Surface native work from this archive

## Governing intent

The user explicitly changed direction to a **native C/C++ application with Surface's own renderer**, fully immersive and without visible interface chrome. Keep the scientific ink, local operation, real catalogue data and durable continuation. Do not resume the abandoned browser implementation, substitute a WebView or external rendering engine, or claim the earlier lost workspace was recovered. The latest user instruction governs any future change in scope.

This archive is the concrete native source and evidence checkpoint. Read `README.md`, `docs/GATE_REPORT.md`, `evidence/commission-gates.json`, `docs/RECOVERY.md` and `docs/FOUNDATION_REPLAY.md` before changing acceptance claims. The extracted project root contains `SOURCE_MANIFEST.json` and `RELEASE.json`, which supply the actual local Git source revision and exact path hashes; compare the delivered files against them before using a historical result as current evidence. Do not manufacture a revision from a conversation or the expected site URL.

## State at handoff

| Boundary | Actual state |
|---|---|
| Native app | Version 0.1.0; `org.surface.nativeink`; ARM64 Android 10+ |
| Renderer and simulation | Original C++ CPU rasterizer and numerical modules; Java only handles Android lifecycle/UI-thread system integration |
| APK | `build/Surface-arm64.apk`, 1,369,050 bytes |
| APK SHA-256 | `0a6f32c450c931699eaf75778c5e7d1fae1b5cfc1123d32aeac93d5f46a2f8da` |
| APK evidence | Native build/link, signature, ZIP/16 KiB ELF alignment and all 10 static package checks passed; no Android device/emulator execution |
| Native host tests | 9 C++ executables plus 14 Python supervisor tests passed |
| Original foundation replay | 145 original tests passed; 129 scientific files verified; 125 deterministic files regenerated exactly |
| Original lost session | Source, revision, usable URL and outstanding jobs remain unavailable/unknown |
| Old eight Octave comparisons | UNKNOWN; the eight original Oracle Python tests are different evidence |
| Broad commission | Open, with scoped accepted increments; use the current gate report rather than rewriting the original matrix |

The preserved continuation ZIP has SHA-256 `ca8f9202b4c4acc8ab39d3a7305f4ba4cf80d016a384db9714019208cd5ae622`. Its nested originals were freshly replayed without modifying their bytes. `lineage/surface-web-work-in-progress-20261025.zip` contains the halted browser-stage work for historical recovery only; it is not native application code. Preserve `lineage/` unchanged. The missing full five-partition Language Lab corpus and wider research inputs were not reconstructed.

No Android device was available. Host images are actual native raster output and are useful appearance evidence, but they do not prove touch delivery, platform lifecycle, audio routing or device performance. Host frame timings in the headless reports must stay labeled as host measurements.

## First next action: complete Android integration evidence

When a compatible authorized ARM64 device or emulator is available, preserve its model, Android/API version, ABI and the exact installed APK hash in a new receipt. Begin with the existing artifact; avoid unrelated feature changes before establishing whether it launches and works. The source ZIP excludes generated builds, so copy the separately delivered `Surface-0.1.0-arm64.apk` to `build/Surface-arm64.apk` first, or substitute its actual path in the install command.

```sh
adb devices -l
adb shell getprop ro.product.cpu.abi
adb shell getprop ro.build.version.sdk
adb install -r build/Surface-arm64.apk
adb shell am start -n org.surface.nativeink/.SurfaceActivity
```

Use the selected device explicitly if more than one is connected. Then perform this bounded integration sequence and record observations rather than predicted outcomes:

1. Confirm fullscreen startup, visible seeded fields and absence of app chrome. Check a real one-finger stroke and both portrait/landscape window sizing.
2. Exercise all seven observations with two-finger taps or keyboard 1–7. Verify a stationary pinch and a two-finger drag do not become a tap. Test one-finger sky rotation, sky pinch and negative field input.
3. Check three-finger pause/resume, background/foreground, screen off/on and window recreation. Verify there is no runaway simulation catch-up or stale worker result replacing current state.
4. Toggle sound by double tap or M. Check output routing and lifecycle silence/resume on the actual device. Do not describe the amplitude mapping as calibrated speaker pressure.
5. Export with four-finger tap or E/S. Verify an acknowledged `SURFEXP1` file appears under `Downloads/Surface`, inspect its byte count/digest, and open a supported exported document through the Android content-provider handoff. Test corrupt/oversized import rejection while the prior state remains intact.
6. Relaunch after a committed checkpoint and verify model/view continuation. A force-stop/process-loss test must distinguish committed state from uncommitted input. Keep the previous good slot and ownership record; never reset a lease or delete checkpoint data to make admission appear successful.
7. Measure sustained device frame times, responsiveness, memory and thermal behavior with the exact surface size, tracer budget and observation recorded. Native Android currently caps the raster near 550,000 pixels and targets a bounded frame cadence; report measured outcomes, not that target as achieved FPS.

Capture a short device screen recording or screenshots and relevant `Surface` log output. Fix only concrete failures, rerun the affected native checks, rebuild/sign with the same development identity, then repeat the failed device case. If no device is available, retain this gate as blocked/unknown and continue an independently useful bounded scientific gate; do not substitute a web preview for native execution.

## Rebuild and focused continuation

From the project root:

```sh
python3 tools/build_native.py --test
build/tests/test_checkpoint
build/surface --demo --frames 60 --width 720 --height 1280 \
  --output build/previews/coupled.ppm --save build/previews/demo.surface \
  --report evidence/headless-coupled.json
```

The driver compiles common modules once and links all discovered tests against those objects, without disabling assertions. The portable snapshot includes the model and view state with a SHA-256 envelope. It does not serialize renderer trail history or acoustic phase. Same-build exact numerical continuation is established by the session/physics tests; cross-architecture bit identity requires its own evidence.

For Android rebuilding, follow `tools/build_android.py` and `evidence/android-toolchain.json`. Then run `python3 tools/verify_android.py --toolchain /path/to/android-toolchain`. The actual command-level static receipt is `evidence/android-package-verification.json`; it checks the packaged ELF/JNI symbols, 16 KiB alignment, signature, permissions and only the platform shared dependencies `libandroid`, `liblog`, `libaaudio`, `libm`, `libdl` and `libc`. Do not call those ten static checks a device test.

The official NDK/build-tools/platform downloads are external dependencies, not bundled source. The signing key backup exists as a **separate local private file**, deliberately excluded from the source ZIP and the delivered artifact batch. Automatic approval review blocked its transmission because explicit authorization to disclose the credential was missing. Preserve it only through a user-approved private route; do not upload or commit it without that authorization, and do not assume it will survive loss of the current working environment. Losing/replacing that identity prevents a compatible update to an installation signed with the original development key.

Do not rerun every historical computation without a reason. The foundation replay receipt already records exact inputs, 11 supervised tasks and raw logs. Rerun an affected test or gate when code/input/toolchain changes, a mismatch appears, or a required device/scientific condition has not yet been checked.

## Scientific work after the device gate

Use `docs/GATE_REPORT.md` and `evidence/commission-gates.json` as the current dependency-aware assessment. The immutable original acceptance matrices retain their original initial statuses. A native fixture pass is not a blanket acceptance of G00–G16.

Useful next increments should each have a named input, bounded resource budget, independent reference, tolerance and durable result. Remaining areas include reconciliation of the lost-session admission/Octave evidence; calibrated battery and material parameters; independent quantum/channel comparison; N-chart topology; uncertainty-aware astronomical distance/measurement handling; real pulsar timing; collider event input; hardware-target compilation; and held-out discovery. Billion-source ingestion and dynamical astronomical models were not implemented by shipping a 10,000-source direction display. The full absent Language Lab corpus cannot be certified by examples.

Preserve the v0.1/v3 basis-order distinction: native Oracle gates use qubit zero as the most significant index bit, while v3 uses least significant. Use the tested `reorderQubits` adapter and explicit record metadata. Preserve Gaia IDs as uint64 integers and missing parallax flags; no inferred distance or synthetic source may silently replace an observed record.

## Publication boundary and recovery identity

The only newly registered site identity is `appgprj_6adda0d68b40819195aa220751fcb5b6`. Its inventory contains the expected string `https://surface-physical-ink.daintyaspen11.chatgpt.site`, but **it was never published and is not a usable release URL**. This registration is not evidence of the old lost session's identity. Do not hand it to the user as a working route.

An attempted private external repository upload was explicitly rejected by automatic approval review: destination ownership and destination-specific authorization were not established. **Do not retry that upload, use an alternate transport, or publish to another destination as a workaround.** Obtain explicit destination authorization before a future repository upload. The authorized release path for this handoff is direct APK/source/evidence artifact delivery. No remote outstanding job was identified; do not cancel an unknown process or remote job based on a stale conversation description.

Continue in bounded steps with concise progress updates. Use `tools/supervise.py` for finite child jobs when appropriate; heartbeats are not semantic progress, retries cannot reset the original deadline, and late output must not replace a newer result. Preserve failed-run evidence and the last valid checkpoint. End each increment with the actual changed files, commands, observed result and unresolved gate.
