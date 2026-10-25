# Surface 0.1.1: Android startup repair

## Reported failure and verified scope

The user installed Surface 0.1.0 and reported an immediate crash on opening,
before a visible loading screen. No device crash log was available. Investigation
identified a concrete Java/JNI initialization defect that matches that symptom:
`SurfaceActivity` declared native callbacks but did not load their library
through the managed runtime.

The repaired **Surface Recovery 0.1.1** APK is built and has passed fourteen
static package checks. The actual Java class passes a RED→GREEN JNI regression.
**The new APK has not yet been executed on the user's phone or an emulator.**
This report does not close Android runtime acceptance.

## Cause and minimal change

Android's `NativeActivity` opens the manifest-named shared library and locates
`ANativeActivity_onCreate`. That native activity path does not itself register
an application's additional Java native declarations with ART. Consequently,
the ELF can export the correct function names while the first Java callback
still fails to resolve them. The Activity's layout listener calls
`nativeDimensions`, making the missing registration relevant immediately after
launch.

The only Java change is:

```java
static {
    System.loadLibrary("surface");
}
```

The initializer executes before Activity callbacks. This follows Android's
[JNI loading guidance](https://developer.android.com/ndk/guides/jni-tips).
The separate paths are visible in AOSP's
[NativeActivity loader](https://android.googlesource.com/platform/frameworks/base.git/+/master/core/jni/android_app_NativeActivity.cpp)
and [ART library registry](https://android.googlesource.com/platform/art/+/master/runtime/jni/java_vm_ext.cc).
These sources support the mechanism; the user's exact device exception remains
unobserved.

## Executed regression

`tools/test_android_startup.py` compiled the actual Activity against the official
API 36 platform JAR, loaded it on Java 17, and invoked its two static native
declarations through reflection. The driver never loads the library itself.
A small host JNI library records exact integer arguments and callback counts.

| Run | Observed result |
|---|---|
| Original Activity, RED | JVM exit 42; `UnsatisfiedLinkError` at the first `nativeDimensions(int,int)` call |
| Initializer added, GREEN | JVM exit 0; both callbacks resolved |
| Native witness | Two dimension calls; one open call; final dimensions 1080×2400; one non-null string reference |
| Compiled bytecode | Managed load absent before repair and present afterward |

The driver and fixture were unchanged between runs. The historical Activity
copy matches the RED input hash exactly. Evidence is retained in
`evidence/startup-jni-red.json`, `evidence/startup-jni-green.json`, their raw logs
and class disassemblies. The fixture uses opaque JNI pointer parameters and
signed 32-bit integers without inspecting JNI object internals; it does not
claim to validate URI text or Android framework behavior.

## Package identity and build evidence

| Item | Result |
|---|---|
| APK | `Surface-Recovery-0.1.1-arm64.apk` |
| Application / launcher | `org.surface.nativeink.recovery` / Surface Recovery |
| Activity | `org.surface.nativeink.SurfaceActivity` |
| Target | ARM64, Android API 29+ |
| Size | 1,369,050 bytes |
| SHA-256 | `eb430f4a71f296059901fd383edf8f128c0b4795c2df737eb1ef99e1d98ab120` |
| Static checks | 14 passed, including signature/alignment commands and byte-exact native/data identity |

The compiled Activity class matches the GREEN witness. The builder reuses the
verified 0.1.0 native ELF and assets, isolating the Java repair. Its fully
qualified Activity declaration keeps the original Java/JNI package valid under
the new application ID. See `evidence/startup-repair-build.json` and
`evidence/startup-native-origin.json`.

The original signing key was unavailable after the working environment was
lost. The replacement development key was created with the user's authorization,
saved privately and verified by round-trip hash. The recovery application
therefore installs beside the original, preserving its installation and data.
The private key and its private file identifier are excluded from source.

## Rebuild and next gate

```sh
python3 tools/build_startup_repair.py --toolchain ../android-toolchain \
  --keystore /private/path/surface-recovery.keystore
```

This build needs the pinned Android platform/build tools and Java 17. It uses
`lineage/Surface-0.1.0-libsurface.so`; an NDK rebuild is unnecessary for this
repair. The earlier science tests are preserved baseline evidence, and no
scientific gate is advanced by fixing Java library loading.

Next, install **Surface Recovery**, observe a rendered frame, and record an
actual crash log if opening still fails. Then verify lifecycle, gestures,
sound, export/import and checkpoint restoration on-device. The native state
schema is unchanged, but application-private storage is separate between the
two package identities.
