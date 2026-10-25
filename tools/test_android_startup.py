#!/usr/bin/env python3
"""Run the actual Activity's JNI declarations on a bounded desktop JVM fixture."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--android-jar", type=Path, required=True)
    parser.add_argument("--phase", choices=("red", "green", "check"), default="check")
    parser.add_argument("--compiler", default="c++")
    options = parser.parse_args()
    android_jar = options.android_jar.resolve()
    fixture = ROOT / "tests/android_startup/bridge_fixture.cpp"
    driver = ROOT / "tests/android_startup/StartupProbe.java"
    activity = ROOT / "android/SurfaceActivity.java"
    out = ROOT / "build/startup-jni" / options.phase
    out.mkdir(parents=True, exist_ok=True)
    classes = out / "classes"
    classes.mkdir(exist_ok=True)
    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)
    receipt_path = evidence / f"startup-jni-{options.phase}.json"
    log_path = evidence / f"startup-jni-{options.phase}.log"
    receipt = {
        "schema": "surface-startup-jni-host-v1",
        "phase_label": options.phase,
        "status": "IN_PROGRESS",
        "platform": platform.platform(),
        "scope": "Actual SurfaceActivity static Java native-method resolution on host JVM with an instrumented native fixture; no Android Activity/device execution",
        "native_fixture_abi": "Linux JNI pointer parameters are opaque; jint is signed 32-bit; no JNIEnv table access; no native string-content claim",
        "actual_activity": {"path": "android/SurfaceActivity.java", "sha256": sha256(activity)},
        "fixture": {"path": "tests/android_startup/bridge_fixture.cpp", "sha256": sha256(fixture)},
        "driver": {"path": "tests/android_startup/StartupProbe.java", "sha256": sha256(driver)},
        "android_jar": {"path": str(android_jar)},
        "commands": [],
        "assertions": [
            "Actual Activity class initializes without constructing an Android Activity",
            "First native dimensions call receives (320, 480) exactly",
            "Actual nativeOpen declaration resolves and passes a non-null String reference",
            "Second native dimensions call receives (1080, 2400) exactly",
            "Observed callback counts are dimensions=2, open=1, nonnull-String=1",
        ],
        "log": str(log_path.relative_to(ROOT)),
    }
    logs = []
    begin = time.monotonic()

    def save():
        receipt["elapsed_seconds"] = time.monotonic() - begin
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
        log_path.write_text("\n".join(logs))

    def run(command, label):
        record = {"label": label, "argv": [str(part) for part in command], "timeout_seconds": 30}
        receipt["commands"].append(record)
        started = time.monotonic()
        try:
            result = subprocess.run(record["argv"], cwd=ROOT, text=True, capture_output=True, timeout=30)
            record.update(exit_code=result.returncode, wall_seconds=time.monotonic() - started)
            logs.extend(["COMMAND " + json.dumps(record["argv"]), result.stdout, result.stderr])
            save()
            return result
        except subprocess.TimeoutExpired as error:
            record.update(exit_code=None, timed_out=True, wall_seconds=time.monotonic() - started)
            receipt["status"] = "BLOCKED_TIMEOUT"
            logs.append(f"TIMEOUT {label}: {error}")
            save()
            raise

    if not android_jar.is_file():
        receipt["status"] = "BLOCKED_INPUT_MISSING"
        receipt["error"] = "Android platform JAR is not present"
        save()
        print(json.dumps({"status": receipt["status"], "receipt": str(receipt_path)}))
        return 2
    receipt["android_jar"]["sha256"] = sha256(android_jar)
    java = shutil.which("java")
    compiler = shutil.which(options.compiler)
    if java is None or compiler is None:
        receipt["status"] = "BLOCKED_TOOLCHAIN_MISSING"
        receipt["error"] = "Java and a host C++ compiler are required"
        save()
        return 2
    try:
        version = run([java, "-version"], "java-version")
        if version.returncode:
            receipt["status"] = "BLOCKED_TOOLCHAIN"
            save()
            return 2
        native = run([compiler, "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror", "-fPIC", "-shared", "-fvisibility=hidden", fixture, "-o", out / "libsurface.so"], "compile-host-jni-fixture")
        if native.returncode:
            receipt["status"] = "BLOCKED_FIXTURE_COMPILE"
            save()
            return 2
        java_compile = run([java, "-m", "jdk.compiler/com.sun.tools.javac.Main", "-source", "8", "-target", "8", "-classpath", android_jar, "-d", classes, activity, driver], "compile-actual-activity-and-driver")
        if java_compile.returncode:
            receipt["status"] = "BLOCKED_JAVA_COMPILE"
            save()
            return 2
        result = run([java, f"-Djava.library.path={out}", "-cp", str(classes) + ":" + str(android_jar), "org.surface.nativeink.StartupProbe"], "execute-actual-jni-bridge")
        receipt["runtime_exit_code"] = result.returncode
        receipt["expected_missing_load_failure_observed"] = result.returncode == 42 and "UnsatisfiedLinkError" in result.stderr and "SurfaceActivity.nativeDimensions" in result.stderr
        witness = None
        for line in result.stdout.splitlines():
            if line.startswith('{"status":'):
                witness = json.loads(line)
        receipt["witness"] = witness
        passed = result.returncode == 0 and witness == {"status": "PASS", "dimension_calls": 2, "open_calls": 1, "width": 1080, "height": 2400, "nonnull_string_calls": 1}
        receipt["status"] = "PASS" if passed else "FAIL"
        receipt["passed"] = passed
        receipt["compiled_activity_sha256"] = sha256(classes / "org/surface/nativeink/SurfaceActivity.class")
        receipt["fixture_library_sha256"] = sha256(out / "libsurface.so")
        if receipt["actual_activity"]["sha256"] != sha256(activity):
            receipt["status"] = "BLOCKED_SOURCE_CHANGED_DURING_RUN"
            receipt["passed"] = False
        save()
        print(json.dumps({key: receipt[key] for key in ("status", "runtime_exit_code", "expected_missing_load_failure_observed", "witness")}, indent=2))
        print("Evidence:", receipt_path.relative_to(ROOT), log_path.relative_to(ROOT))
        return 0 if receipt["passed"] else 1
    except subprocess.TimeoutExpired:
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
