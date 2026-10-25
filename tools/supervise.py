#!/usr/bin/env python3
"""Finite, independently killable POSIX task supervision with durable publication.

This supervises development/research child processes. It cannot terminate an
individual blocked C++ thread, survive its own host being killed, or sandbox an
adversarial child. Commands run directly, never through a shell.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import shutil
import signal
import subprocess
import tempfile
import time
from typing import Optional


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    command: tuple[str, ...]
    cwd: Optional[str] = None
    timeout: float = 300.0
    semantic_timeout: float = 120.0
    milestones: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    retry_exit_codes: tuple[int, ...] = (75,)

    def __post_init__(self):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", self.task_id):
            raise ValueError("task_id must be a simple identifier")
        if not self.command or any(not isinstance(part, str) or not part or "\0" in part for part in self.command):
            raise ValueError("command must contain nonempty argument strings")
        for name, value, maximum in (("timeout", self.timeout, 300), ("semantic_timeout", self.semantic_timeout, 120)):
            if not math.isfinite(value) or not 0 < value <= maximum:
                raise ValueError(f"{name} must be positive and at most {maximum} seconds")
        if len(self.milestones) > 256 or len(set(self.milestones)) != len(self.milestones):
            raise ValueError("milestones must be unique and bounded")
        if any(not isinstance(item, str) or not item or len(item) > 200 for item in self.milestones):
            raise ValueError("invalid milestone")
        if len(self.outputs) > 64 or len(set(self.outputs)) != len(self.outputs):
            raise ValueError("outputs must be unique and bounded")
        for name in self.outputs:
            path = PurePosixPath(name)
            if not name or path.is_absolute() or any(part in ("..", ".", "") for part in name.split("/")) or "\\" in name or "\0" in name or name == "manifest.json":
                raise ValueError("output paths must be relative without parent traversal")
        if len(self.retry_exit_codes) > 8 or any(not isinstance(code, int) or not 1 <= code <= 255 for code in self.retry_exit_codes):
            raise ValueError("invalid classified retry exit code")


@dataclass(frozen=True)
class Result:
    task_id: str
    status: str
    reason: str
    epoch: int
    attempts: int
    returncode: Optional[int]
    published: tuple[dict, ...]
    elapsed: float


def _sync_directory(path: Path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _atomic_json(path: Path, value):
    raw = (json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":")) + "\n").encode()
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _sync_directory(path.parent)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


class Supervisor:
    MAX_LOG_BYTES = 8 * 1024 * 1024
    MAX_OUTPUT_BYTES = 64 * 1024 * 1024
    MAX_TOTAL_OUTPUT_BYTES = 128 * 1024 * 1024

    def __init__(self, root, *, poll_interval=0.05, terminate_grace=0.2):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        if not 0 < poll_interval <= 0.25 or not 0 <= terminate_grace <= 1:
            raise ValueError("invalid watchdog polling or termination budget")
        self.poll_interval = poll_interval
        self.terminate_grace = terminate_grace

    @contextmanager
    def _lock(self, directory):
        with open(directory / "lock", "a+b") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    @staticmethod
    def _epoch(directory):
        try:
            return int(json.loads((directory / "fence.json").read_text())["epoch"])
        except FileNotFoundError:
            return 0

    @staticmethod
    def _append(directory, event):
        raw = (json.dumps({"wall_time": time.time(), **event}, sort_keys=True, allow_nan=False) + "\n").encode()
        with open(directory / "journal.jsonl", "ab", buffering=0) as handle:
            handle.write(raw)
            os.fsync(handle.fileno())

    def _begin(self, spec, attempt, deadline_wall):
        directory = self.root / spec.task_id
        directory.mkdir(exist_ok=True)
        for name in ("stages", "logs", "committed"):
            (directory / name).mkdir(exist_ok=True)
        with self._lock(directory):
            epoch = self._epoch(directory) + 1
            if epoch > 2**63 - 1:
                raise RuntimeError("task epoch exhausted")
            _atomic_json(directory / "fence.json", {"epoch": epoch})
            stage = directory / "stages" / str(epoch)
            stage.mkdir()
            intent = {"event": "intent", "epoch": epoch, "attempt": attempt, "spec": asdict(spec), "deadline_wall": deadline_wall, "stage": str(stage)}
            self._append(directory, intent)  # Durable intent precedes process creation.
            _atomic_json(directory / "resume.json", {**intent, "status": "running", "last_milestone": None})
        return directory, stage, epoch

    def _record(self, directory, epoch, event, **fields):
        with self._lock(directory):
            current = self._epoch(directory) == epoch
            self._append(directory, {"event": event, "epoch": epoch, "current": current, **fields})
            if current and event == "progress":
                state = json.loads((directory / "resume.json").read_text())
                _atomic_json(directory / "resume.json", {**state, "last_milestone": fields["milestone"]})
            return current

    def _kill(self, process):
        # Every launched child has a separate session/process group. Descendants
        # that deliberately create a new session are outside this host contract.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=self.terminate_grace)
        except subprocess.TimeoutExpired:
            pass
        # The leader may exit on SIGTERM while a descendant ignores it. Group
        # cleanup therefore cannot depend on whether wait() reaped the leader.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=1)

    def _child(self, spec, directory, stage, epoch, deadline, deadline_wall):
        environment = {**os.environ, "SURFACE_TASK_STAGE": str(stage), "SURFACE_TASK_EPOCH": str(epoch), "SURFACE_TASK_DEADLINE_UNIX": str(deadline_wall)}
        try:
            process = subprocess.Popen(list(spec.command), cwd=spec.cwd, env=environment, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True, bufsize=0)
        except OSError as error:
            self._record(directory, epoch, "spawn-failed", detail=str(error))
            return None, "spawn-failed"
        selector = None
        try:
            self._record(directory, epoch, "spawned", pid=process.pid)
            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ)
            os.set_blocking(process.stdout.fileno(), False)
        except BaseException:
            self._kill(process)
            if selector is not None:
                selector.close()
            process.stdout.close()
            raise
        last_progress = time.monotonic()
        last_heartbeat = 0.0
        milestone_index = 0
        buffered = b""
        total_bytes = 0
        reason = "exit-code"
        try:
            with open(directory / "logs" / f"{epoch}.log", "wb") as log:
                while True:
                    now = time.monotonic()
                    if self._epoch(directory) != epoch:
                        reason = "superseded"
                        break
                    if now >= deadline:
                        reason = "deadline"
                        break
                    if now - last_progress >= spec.semantic_timeout:
                        reason = "no-semantic-progress"
                        break
                    for key, _ in selector.select(min(self.poll_interval, deadline - now)):
                        try:
                            chunk = os.read(key.fileobj.fileno(), 65536)
                        except BlockingIOError:
                            continue
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        total_bytes += len(chunk)
                        if total_bytes > self.MAX_LOG_BYTES:
                            reason = "output-limit"
                            break
                        log.write(chunk)
                        buffered += chunk
                        while b"\n" in buffered:
                            line, buffered = buffered.split(b"\n", 1)
                            if len(line) > 16384:
                                continue
                            try:
                                message = json.loads(line)
                            except (ValueError, UnicodeDecodeError):
                                continue
                            if not isinstance(message, dict) or message.get("epoch") != epoch:
                                continue
                            if message.get("type") == "progress" and milestone_index < len(spec.milestones) and message.get("milestone") == spec.milestones[milestone_index]:
                                last_progress = time.monotonic()
                                self._record(directory, epoch, "progress", milestone=spec.milestones[milestone_index])
                                milestone_index += 1
                            elif message.get("type") == "heartbeat" and time.monotonic() - last_heartbeat >= 5:
                                self._record(directory, epoch, "heartbeat")
                                last_heartbeat = time.monotonic()
                        if len(buffered) > 16384:
                            buffered = b""  # Bound an unterminated diagnostic line.
                    if reason == "output-limit":
                        break
                    returncode = process.poll()
                    if returncode is not None:
                        reason = "success" if returncode == 0 else "exit-code"
                        break
                log.flush()
                os.fsync(log.fileno())
            # Completion of the group leader must not leave background work
            # outside the fixed task budget or racing artifact publication.
            self._kill(process)
            return process.returncode, reason
        finally:
            if process.poll() is None:
                self._kill(process)
            selector.close()
            process.stdout.close()

    def _publish(self, spec, directory, stage, epoch, deadline):
        pending = Path(tempfile.mkdtemp(prefix=f".pending-{epoch}-", dir=directory / "committed"))
        outputs = []
        total = 0
        try:
            for name in spec.outputs:
                if time.monotonic() >= deadline:
                    raise TimeoutError("publication deadline expired")
                source = stage / name
                try:
                    source.resolve(strict=True).relative_to(stage.resolve())
                except (ValueError, FileNotFoundError):
                    raise ValueError(f"missing or escaped output: {name}")
                if source.is_symlink() or not source.is_file():
                    raise ValueError(f"output must be a regular file: {name}")
                target = pending / name
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                count = 0
                with open(source, "rb") as incoming, open(target, "wb") as outgoing:
                    while chunk := incoming.read(65536):
                        if time.monotonic() >= deadline:
                            raise TimeoutError("publication deadline expired")
                        count += len(chunk)
                        total += len(chunk)
                        if count > self.MAX_OUTPUT_BYTES or total > self.MAX_TOTAL_OUTPUT_BYTES:
                            raise ValueError("staged output exceeds size budget")
                        outgoing.write(chunk)
                        digest.update(chunk)
                    outgoing.flush()
                    os.fsync(outgoing.fileno())
                outputs.append({"name": name, "path": f"committed/{epoch}/{name}", "bytes": count, "sha256": digest.hexdigest()})
            manifest = {"schema": "surface-task-publication", "version": 1, "epoch": epoch, "outputs": outputs}
            _atomic_json(pending / "manifest.json", manifest)
            for path, _, _ in os.walk(pending, topdown=False):
                _sync_directory(Path(path))
            with self._lock(directory):
                if self._epoch(directory) != epoch:
                    return None
                if time.monotonic() >= deadline:
                    raise TimeoutError("publication deadline expired")
                os.rename(pending, directory / "committed" / str(epoch))
                _sync_directory(directory / "committed")
                _atomic_json(directory / "current.json", manifest)
                self._append(directory, {"event": "published", "epoch": epoch, "outputs": outputs})
            return tuple(outputs)
        finally:
            if pending.exists():
                shutil.rmtree(pending)

    def _finish(self, directory, result):
        with self._lock(directory):
            current = self._epoch(directory) == result.epoch
            self._append(directory, {"event": "completed", "current": current, **asdict(result)})
            if current:
                state = json.loads((directory / "resume.json").read_text())
                _atomic_json(directory / "resume.json", {**state, **asdict(result), "finished_wall": time.time()})
        return result

    def run(self, spec: TaskSpec) -> Result:
        started = time.monotonic()
        deadline = started + spec.timeout
        deadline_wall = time.time() + spec.timeout
        for attempt in (1, 2):
            directory, stage, epoch = self._begin(spec, attempt, deadline_wall)
            returncode, reason = self._child(spec, directory, stage, epoch, deadline, deadline_wall)
            if reason == "success":
                try:
                    published = self._publish(spec, directory, stage, epoch, deadline)
                except TimeoutError:
                    reason = "deadline"
                except (OSError, ValueError) as error:
                    self._record(directory, epoch, "invalid-output", detail=str(error))
                    reason = "invalid-output"
                else:
                    status = "succeeded" if published is not None else "superseded"
                    return self._finish(directory, Result(spec.task_id, status, "success" if published is not None else "superseded", epoch, attempt, returncode, published or (), time.monotonic() - started))
            if reason == "exit-code" and returncode in spec.retry_exit_codes and attempt == 1 and time.monotonic() < deadline:
                if self._record(directory, epoch, "retry", classification=f"transient-exit-{returncode}", remaining=1):
                    continue
                reason = "superseded"
            status = "superseded" if reason == "superseded" else "failed"
            return self._finish(directory, Result(spec.task_id, status, reason, epoch, attempt, returncode, (), time.monotonic() - started))
        raise AssertionError("retry bound violated")

    def inspect(self, task_id):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", task_id):
            raise ValueError("invalid task identifier")
        return json.loads((self.root / task_id / "resume.json").read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".surface-tasks")
    parser.add_argument("--task", required=True)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--semantic-timeout", type=float, default=120)
    parser.add_argument("--cwd")
    parser.add_argument("--milestone", action="append", default=[])
    parser.add_argument("--output", action="append", default=[])
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    runner = Supervisor(arguments.root)
    if arguments.inspect:
        print(json.dumps(runner.inspect(arguments.task), indent=2))
        return 0
    command = arguments.command[1:] if arguments.command[:1] == ["--"] else arguments.command
    spec = TaskSpec(arguments.task, tuple(command), arguments.cwd, arguments.timeout, arguments.semantic_timeout, tuple(arguments.milestone), tuple(arguments.output))
    result = runner.run(spec)
    print(json.dumps(asdict(result), sort_keys=True))
    return 0 if result.status == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
