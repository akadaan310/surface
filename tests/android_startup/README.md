# Actual Activity JNI loading regression

`tools/test_android_startup.py` compiles the real `android/SurfaceActivity.java`
against the Android API JAR and loads that class on the available Java 17 host.
It invokes the Activity's real private static JNI declarations via reflection.
The driver does **not** call `System.loadLibrary` itself: the actual Activity
must arrange loading for its own callbacks. A deliberately small host
`libsurface.so` records native calls, providing a numerical witness that the
runtime resolved the intended methods in the loaded library.

The fixture checks two exact width/height pairs, two dimension callback counts,
one open callback, and receipt of a non-null string reference. Its opaque JNI
pointer types are sufficient for these Linux-host ABI signatures because it
never dereferences `JNIEnv`, calls a JNI function-table entry, or inspects an
object. **The URI's string contents are not examined by the native fixture.**
That restriction is explicit; no full JNI-header implementation is simulated.

The unchanged 0.1.0 Activity failed at its first dimensions call with
`UnsatisfiedLinkError`: its superclass's native activity loading path does not
register the library for these Java native methods. Adding the Activity's
static `System.loadLibrary("surface")` initializer allowed the exact same driver
to resolve both callbacks. Red and green receipts retain the actual Activity
source hash and all subprocess commands/output. The disassembled compiled class
has no managed load in the red run and contains the initializer in the green
run. `baseline/SurfaceActivity.java` preserves the pre-fix bytes, checked against
the actual RED run's input hash; it is historical evidence, not app build input.

```sh
python3 tools/test_android_startup.py \
  --android-jar ../android-toolchain/android-36/android.jar --phase check
```

The phase selects receipt/log paths; it never changes pass/fail expectations.
Use `check` for a new current-source run to preserve the recorded red and green
evidence. The historical red run returned nonzero despite being the expected
failure. To repeat it, use a separate checkout with the preserved baseline at
`android/SurfaceActivity.java`; do not overwrite the repaired working source.

This is host Java/JNI boundary evidence. Android lifecycle methods are not
executed, no Activity instance is constructed, and the host native fixture is
not the app's renderer or simulation. It does not certify Android launch,
surface creation, touch, audio, device performance, or the complete fix on the
user's phone. A device launch and crash log remain separate acceptance evidence.
