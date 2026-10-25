# Native state recovery and task supervision

Surface has two different recovery boundaries. The C++ checkpoint store preserves native continuation bytes between app launches. The independent Python supervisor bounds finite development and research child processes. Neither mechanism makes a frozen operating system recoverable from inside the frozen process.

## Native checkpoint contract

`include/surface/checkpoint.hpp` exposes:

```cpp
surface::CheckpointStore store(directory, 10 * 1024 * 1024);
const auto owner = store.acquireLease(); // Once per new runtime owner.
store.saveOwned(std::span<const std::uint8_t>(payload), generation, owner);
// A std::span<const std::byte> overload accepts Physics::serialize() output.
std::optional<surface::CheckpointRecord> record = store.load();
// record->generation is uint64_t; record->payload is vector<uint8_t>.
auto candidates = store.loadCandidates(); // At most two, newest first.
```

The store owns `slot0.bin`, `slot1.bin`, `lease.bin`, and a cooperative `flock` lock file in its directory. A runtime acquires one durable owner lease when it starts and keeps that fixed token. `saveOwned` checks that the supplied token is still current while holding the lock through every subsequent write and rename. A replacement runtime's acquisition advances the owner counter under the same lock, so an old delayed worker cannot reclaim publication by choosing a larger generation. Acquiring a lease and publishing a checkpoint therefore have one serialized order, including across cooperating processes.

After validating ownership, a writer reads both slots under that lock, rejects generation zero and any generation less than or equal to the newest valid committed generation, and selects a missing/corrupt slot or the older valid slot. It writes a uniquely named temporary file, calls `fsync` on that file, atomically renames it over the selected slot, and calls `fsync` on the containing directory before returning success. The newest previous valid slot is retained.

The legacy `save(payload, generation)` overload remains for single-owner command-line use on stores that have never acquired a lease. It refuses to write once `lease.bin` exists, so it cannot bypass runtime ownership. An absent lease cannot authorize `saveOwned`. Corrupt, truncated, zero, wrong-version, or checksum-invalid existing lease files fail closed for both acquisition and owned save; they are never silently reset. An owner-counter overflow also fails closed. The runtime must never delete or reset ownership files to work around an error.

`load()` returns the valid slot with the greatest generation. A corrupt or truncated latest slot falls back to the other valid slot. No files means `nullopt`; files with no valid envelope mean an exception. I/O failures and size violations also throw. Callers must treat a thrown save as unconfirmed durability even if a rename occurred before a later filesystem error. They must not erase a previous good checkpoint to make an error disappear.

### Portable envelope

The 32-byte header and payload use this exact layout:

| Offset | Bytes | Meaning |
| --- | ---: | --- |
| 0 | 8 | ASCII `SURFCHK` followed by zero |
| 8 | 4 | Unsigned little-endian format version, currently 1 |
| 12 | 8 | Unsigned little-endian positive generation |
| 20 | 8 | Unsigned little-endian payload byte count |
| 28 | 4 | Unsigned little-endian CRC32 |
| 32 | declared count | Opaque continuation payload |

CRC32 uses reflected polynomial `0xedb88320`, initial value `0xffffffff`, and final complement. Its preimage is bytes 0–27 followed by all payload bytes; the stored CRC field is excluded. The reader checks magic, version, positive generation, exact file length, configured payload bound, and CRC before returning any payload. The default and largest allowed payload bound is 10 MiB, plus the 32-byte header. Slot symlinks are not followed.

`lease.bin` is exactly 32 bytes using ASCII `SURFOWN` plus zero in the first eight bytes, little-endian version 1 at offset 8, the positive 64-bit owner counter at offset 12, reserved zero bytes at offsets 20–27, and the same CRC32 convention at offset 28. Lease acquisition uses a temporary file, file fsync, atomic rename, and directory fsync just like a state commit. Native payloads remain unchanged by owner acquisition.

CRC32 detects accidental corruption. It is **not authentication, a cryptographic provenance digest, or protection from a deliberate rewrite**. The release/evidence workflow uses separate SHA-256 records for source and artifact provenance.

The generic envelope intentionally cannot interpret simulation floats. The app must iterate `loadCandidates()` newest first, validate its own outer view-state schema, and pass the complete physics portion through `Physics::restore`, which performs bounded dimensions, dense counts, finite/range admission, and staged atomic restoration. If the newest CRC-valid payload fails semantic admission, the older candidate remains available. A checksum-valid blob is not sufficient evidence of a scientifically valid state. Do not apply part of a state and then validate the remainder. The next save generation must exceed the newest envelope-valid generation, including a newer candidate rejected by the semantic validator.

Portable envelope bytes do not by themselves promise identical floating-point trajectories on every architecture or compiler. Exact same-build interrupted/restored continuation belongs to the physics and app integration tests. The store does not reset a generation counter from an untrusted file, and corrupt envelopes are not authoritative generation records.

### Native runtime boundary

The renderer and numerical kernels use bounded work. C++ has no general safe API for forcefully terminating a blocked `std::thread` while retaining that process's shared state. A physics-thread stall must not be described as independently killable by this store. Full process crashes, OS stalls, storage failure, loss of the entire app process before its next committed save, and hardware failure are outside an in-process checkpoint's guarantee. Filesystem durability depends on a local filesystem and device honoring successful `fsync` and atomic same-directory rename. The checkpoint directory's existing app-storage parent is assumed durably established; this module does not separately fsync an arbitrary newly created ancestor directory tree.

This implementation targets Linux/POSIX and Android's native POSIX APIs; it is not a Windows checkpoint backend. Linux compilation and fault tests are recorded below. Android device lifecycle behavior needs runtime device/emulator evidence in addition to cross-compilation.

## Independent host task supervisor

`tools/supervise.py` uses Python's standard library and POSIX process groups. It launches each command directly in a separate session, with no shell interpolation. It never executes a task before writing and fsyncing that attempt's intent and resume record.

```python
spec = TaskSpec(
    task_id="analysis-001",
    command=("python3", "analyze.py"),
    timeout=300,
    semantic_timeout=120,
    milestones=("inputs-validated", "analysis-complete"),
    outputs=("result.json",),
)
result = Supervisor("task-runs").run(spec)
```

The child receives these environment variables:

| Variable | Meaning |
| --- | --- |
| `SURFACE_TASK_STAGE` | Unique writable directory for this attempt's declared outputs |
| `SURFACE_TASK_EPOCH` | Current monotonically increasing task epoch |
| `SURFACE_TASK_DEADLINE_UNIX` | Recorded absolute wall-clock deadline for diagnostics |

The actual watchdog uses monotonic elapsed time. The maximum task budget is 300 seconds, and the maximum semantic-progress budget is 120 seconds. Smaller budgets are supported. A retry shares the original task deadline. Heartbeats, progress messages, and retries cannot extend it.

Progress is newline-delimited JSON on stdout. A message is accepted only with the current epoch and the exact next milestone declared in the task specification:

```json
{"type":"progress","epoch":4,"milestone":"inputs-validated"}
```

Accepted milestones refresh the semantic-progress clock. Duplicate, out-of-order, undeclared, or wrong-epoch milestones do not. Heartbeats are recorded at a bounded rate and never refresh either clock:

```json
{"type":"heartbeat","epoch":4}
```

A milestone is a cooperating task's progress assertion, not independent proof of a scientific result. A task with no declared milestones must complete inside the semantic budget. The separate output/evidence checks determine whether its claimed result is usable.

### Failure handling

The default classified transient exit is code 75. Exactly one retry is permitted for a configured transient exit code. A timeout, lost semantic progress, unclassified exit, excessive log output, invalid artifact, startup error, or stale epoch does not automatically retry. The original process group is terminated and then killed if needed; this includes descendants that ignore SIGTERM, even when the leader exits first. A successful leader also cannot leave background descendants in its original group.

Stdout/stderr share a log bounded to 8 MiB per attempt. Each declared output is bounded to 64 MiB and all outputs together to 128 MiB. At most 64 output paths and 256 unique ordered milestones are admitted. Output paths cannot escape the stage; the publication manifest name is reserved. Working directories and commands remain the responsibility of the task author.

The watchdog is a supervising process, not a sandbox. A deliberately hostile child that changes session/process group, writes outside its stage, or attacks the supervisor is outside this contract. A frozen/killed supervisor, a blocked kernel/filesystem call, or a whole-host suspension also prevents timely observation. Normal timeout enforcement includes the polling interval and bounded process-termination/reaping overhead; it is not a real-time operating-system guarantee.

### Durable publication and resume

Each task directory contains:

| File/directory | Role |
| --- | --- |
| `journal.jsonl` | Fsynced intent, spawn, accepted progress, retry, publication and completion records |
| `resume.json` | Atomically replaced current specification, deadline, epoch, milestone and outcome |
| `fence.json` | Atomically replaced monotonically increasing current epoch |
| `stages/<epoch>/` | Isolated uncommitted child outputs |
| `logs/<epoch>.log` | Bounded combined diagnostic output |
| `committed/<epoch>/` | Prepared artifact bytes and their manifest |
| `current.json` | Atomic pointer/manifest for the most recently published successful output |

Only explicitly declared regular-file outputs are copied into a publication. The supervisor computes SHA-256 over the copied bytes, fsyncs the files and directories, then obtains the task lock. Publication is refused if the epoch is stale or the task's fixed deadline has expired. The prepared directory is renamed to an immutable epoch path and `current.json` is atomically replaced. A late older process cannot replace a newer task's output. Failed tasks preserve the previous successful `current.json`.

SHA-256 output digests enable byte-integrity checks; they are not signatures. The task journal and stage paths are local cooperating-process records, not an adversarial trust boundary.

Inspect a resume record without executing anything:

```sh
python3 tools/supervise.py --root task-runs --task analysis-001 --inspect
```

Run a finite task:

```sh
python3 tools/supervise.py --root task-runs --task native-tests \
  --timeout 300 --semantic-timeout 120 -- ./build/tests/test_checkpoint
```

After an interrupted supervisor, inspect `resume.json`, the journal, and the existing published manifest. A recorded `running` state is not proof that its old process is still alive. Do not kill a newly reused PID based solely on an old journal entry. A deliberate new invocation allocates a fresh epoch and stage, so old publication is fenced. The supervisor does not silently replay an interrupted side-effecting task or claim that a new invocation has the old invocation's elapsed budget. The operator must determine whether rerunning the command is valid.

## Verification

Build the current native modules and tests, then run the checkpoint executable:

```sh
python3 tools/build_native.py --test
./build/tests/test_checkpoint
```

The test now uses Session/Physics/Renderer/Phantom admission as well as the checkpoint module, so compiling only `src/checkpoint.cpp` is insufficient. It checks exact bytes, little-endian header fields, a CRC fixture independently obtained with Python zlib, cross-process generation fencing, corrupt/truncated latest-slot fallback, semantic candidate fallback, rejection when both slots are invalid, size limits, and unsupported version admission. Owner-lease regression tests reject a retired token even with an arbitrarily larger generation, exercise independent-process owner replacement, reject plain-save bypass, reject corrupted/truncated owner records without changing either slot, and verify current-owner publication remains usable.

Run the real-process watchdog tests:

```sh
python3 -m unittest discover -s tests -p test_supervisor.py -v
```

The tests launch real child processes for hangs, heartbeat-only loops, duplicate/stale progress, fixed deadlines under continuing progress, the one-retry budget, the shared deadline across retry, unclassified exits, process-group descendants, failure while journaling a newly spawned process, output hashing, late publication, and superseded epochs. They also reject a reserved output manifest name. Test faults live only in tests and child commands; no production hang switch is exposed.

The native pivot preserved the abandoned browser checkpoint prototype separately. Its tests are historical development evidence and are not part of this native implementation or its runtime claims.
