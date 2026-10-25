"""Run/replay bounded scientific evidence through the unchanged host Supervisor.

Usage: python -B -m research.quantum_oracle.run --runs NEW_DIRECTORY
       python -B -m research.quantum_oracle.run --replay EXISTING_DIRECTORY
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import resource
import subprocess
import sys

from tools.supervise import Supervisor, TaskSpec

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 8 * 1024 * 1024


def _safe_file(root, name):
    if not isinstance(name, str) or not name or PurePosixPath(name).is_absolute() or "\\" in name or any(p in ("", ".", "..") for p in name.split("/")):
        raise ValueError("unsafe evidence path")
    path = root / name
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError("linked evidence refused")
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("missing or oversized evidence file")
    return path


def pin_files(root, names):
    root = Path(root).resolve(strict=True)
    if len(names) > 256 or len(set(names)) != len(names):
        raise ValueError("file count or uniqueness budget")
    result = {}
    for name in sorted(names):
        raw = _safe_file(root, name).read_bytes()
        result[name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    return result


def verify_files(root, pins):
    if pin_files(root, tuple(pins)) != pins:
        raise ValueError("evidence identity mismatch")
    return True


def _write(path, value):
    with Path(path).open("x") as handle:
        json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")


def _versions():
    packages = {}
    for name in ("numpy", "scipy", "qiskit", "qutip", "astropy"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "NOT_INSTALLED"
    return {"python": platform.python_version(), "platform": platform.platform(),
            "packages": packages}


def _source_names():
    return tuple(sorted({str(path.relative_to(ROOT)) for path in
                         (ROOT / "research/quantum_oracle").rglob("*.py")} |
                        {"tools/supervise.py", "tools/commission.py", "tools/materialize_foundation.py"}))


def worker():
    # Child-only limits; the user-facing host is unaffected.
    resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))
    resource.setrlimit(resource.RLIMIT_CPU, (50, 50))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_BYTES, MAX_BYTES))
    stage = Path(os.environ["SURFACE_TASK_STAGE"])
    epoch = int(os.environ["SURFACE_TASK_EPOCH"])
    def progress(name):
        print(json.dumps({"type": "progress", "epoch": epoch, "milestone": name}), flush=True)
    progress("source-pinned")
    sources = pin_files(ROOT, _source_names())
    # Actual test output, including discovery, is retained separately from claims.
    command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "research/quantum_oracle/tests", "-v"]
    with (stage / "tests.log").open("xb") as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, timeout=40, check=False)
    progress("tests-finished")
    if result.returncode:
        return result.returncode
    from .discovery import run_affine_cycle, replay
    discovery = run_affine_cycle()
    replay(discovery)
    _write(stage / "discovery.json", discovery)
    verify_files(ROOT, sources)
    _write(stage / "verification.json", {
        "schema": "quantum-oracle.verification.v1", "execution_status": "PASS",
        "scientific_acceptance": "SCOPED_REVIEW_REQUIRED", "command": command,
        "returncode": result.returncode, "source_files": sources,
        "environment": _versions(), "outputs": pin_files(stage, ("tests.log", "discovery.json")),
        "limits": {"wall_seconds": 60, "semantic_seconds": 45, "cpu_seconds": 50,
                   "address_space_bytes": 2 << 30, "output_file_bytes": MAX_BYTES,
                   "retry_exit_codes": [], "blas_threads": 1},
        "tolerance": "Exact hashes for custody; numerical tolerance is declared in individual tests/contracts.",
        "physical_data_validation": "NOT_EVALUATED", "quantum_hardware_validation": "NOT_EXECUTED",
        "surface_readiness": "BLOCKED", "full_initiative": "UNKNOWN"})
    progress("evidence-written")
    return 0


def execute(runs):
    runs = Path(runs).resolve()
    runs.mkdir(parents=True, exist_ok=False)
    command = (sys.executable, "-B", "-m", "research.quantum_oracle.run", "--worker")
    spec = TaskSpec("scientific-reference", command, cwd=str(ROOT), timeout=60,
                    semantic_timeout=45, milestones=("source-pinned", "tests-finished", "evidence-written"),
                    outputs=("tests.log", "discovery.json", "verification.json"), retry_exit_codes=())
    result = Supervisor(runs).run(spec)
    _write(runs / "result.json", asdict(result))
    return asdict(result)


def execution_succeeded(result):
    """The retained Supervisor protocol uses lowercase execution states."""
    return result.get("status") == "succeeded" and result.get("returncode") == 0


def replay_run(runs):
    runs = Path(runs).resolve(strict=True)
    result = json.loads(_safe_file(runs, "result.json").read_text())
    if set(result) != {"task_id", "status", "reason", "epoch", "attempts", "returncode", "published", "elapsed"}:
        raise ValueError("incomplete Supervisor result schema")
    if (not execution_succeeded(result) or result["task_id"] != "scientific-reference"
            or result["returncode"] != 0 or result["attempts"] != 1
            or type(result["epoch"]) is not int or result["epoch"] < 1):
        raise ValueError("run did not succeed; inspect resume.json and logs")
    job = runs / "scientific-reference"
    committed = job / "committed" / str(result["epoch"])
    fence = json.loads(_safe_file(job, "fence.json").read_text())
    publication = json.loads(_safe_file(committed, "manifest.json").read_text())
    current = json.loads(_safe_file(job, "current.json").read_text())
    state = json.loads(_safe_file(job, "resume.json").read_text())
    if fence != {"epoch": result["epoch"]} or current != publication:
        raise ValueError("stale publication fence")
    if any(state.get(k) != v for k, v in result.items()):
        raise ValueError("Supervisor final state mismatch")
    if publication != {"schema": "surface-task-publication", "version": 1,
                       "epoch": result["epoch"], "outputs": result["published"]}:
        raise ValueError("publication manifest mismatch")
    rows = result["published"]
    expected_names = {"tests.log", "discovery.json", "verification.json"}
    if len(rows) != 3 or {row.get("name") for row in rows} != expected_names:
        raise ValueError("missing published science outputs")
    for row in rows:
        if (set(row) != {"name", "path", "bytes", "sha256"} or
                row["path"] != f"committed/{result['epoch']}/{row['name']}"):
            raise ValueError("invalid published output path")
    verify_files(committed, {row["name"]: {"bytes": row["bytes"], "sha256": row["sha256"]} for row in rows})
    # Publication layout is specified by Supervisor. Verify all published bytes.
    receipt = json.loads(_safe_file(committed, "verification.json").read_text())
    required = {"schema", "execution_status", "scientific_acceptance", "command", "returncode",
                "source_files", "environment", "outputs", "limits", "tolerance",
                "physical_data_validation", "quantum_hardware_validation", "surface_readiness", "full_initiative"}
    if (set(receipt) != required or receipt["schema"] != "quantum-oracle.verification.v1" or
            receipt["execution_status"] != "PASS" or receipt["returncode"] != 0 or
            receipt["scientific_acceptance"] != "SCOPED_REVIEW_REQUIRED" or
            set(receipt["source_files"]) != set(_source_names()) or
            set(receipt["outputs"]) != {"tests.log", "discovery.json"} or
            receipt["command"][1:] != ["-B", "-m", "unittest", "discover", "-s", "research/quantum_oracle/tests", "-v"]):
        raise ValueError("invalid scientific verification receipt")
    spec = state.get("spec", {})
    if (spec.get("command", [])[1:] != ["-B", "-m", "research.quantum_oracle.run", "--worker"] or
            spec.get("outputs") != ["tests.log", "discovery.json", "verification.json"] or
            spec.get("timeout") != 60 or spec.get("semantic_timeout") != 45 or
            spec.get("retry_exit_codes") != []):
        raise ValueError("unexpected scientific worker contract")
    verify_files(ROOT, receipt["source_files"])
    verify_files(committed, receipt["outputs"])
    from .discovery import replay
    replay(json.loads(_safe_file(committed, "discovery.json").read_text()))
    return {"status": "PASS", "scope": "source/output hashes and recomputed discovery; tests are retained historical execution",
            "execution_environment": receipt["environment"], "replay_environment": _versions()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--runs", type=Path)
    group.add_argument("--replay", type=Path)
    group.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[key] = "1"
    if args.worker:
        return worker()
    report = replay_run(args.replay) if args.replay else execute(args.runs)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" or execution_succeeded(report) else 3


if __name__ == "__main__":
    raise SystemExit(main())
