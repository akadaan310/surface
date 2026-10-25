# Agent entry point — SURFACE

## Current owner handoff

The owner stopped further build and verification runs during final publication on 2026-10-25. Complete publication/package preparation only. Do not launch new checks or research jobs from this handoff; wait for the next explicit implementation instruction. The commands below document the normal workflow for a later authorized task. CI is manual-dispatch only.

## Read before implementation

1. `SUM.md`, `README.md`, `docs/ARCHITECTURE_AND_HARNESSES.md` and the current initiative's `SELF_PROMPT.md`/`INITIATIVE.json`.
2. `docs/MATHEMATICAL_ATLAS.md`, `docs/QUANTUM_V3_CONSOLIDATION.md`, `docs/GATE_REPORT.md` and `evidence/commission-gates.json`.
3. Materialize `build/foundation/`, then read original V3 and V2 self prompts/constitutions and PHANTOM `REPLAY_HANDOFF.md`. Keep the reference trees unchanged.

The owner authorizes this repository (`akadaan310/surface`) as the canonical project. An old publication refusal in historical artifacts is superseded for this destination. Never put signing keys, tokens or private credential identifiers in source, logs or artifacts.

## First bounded work unit

Record actual repository/working directory, current branch/commit/tree, dirty changes, last verified evidence, outstanding jobs, fixed deadlines and usable artifacts. Inspect `git status`, job `resume.json`/journals/fences and manifest hashes. Preserve recoverable source before editing. Do not infer another session's live status from a stale heartbeat or PID.

```sh
git status --short --branch
git log -3 --oneline
python3 tools/verify_repository.py
python3 tools/materialize_foundation.py --check
```

If materialization does not exist, run without `--check`. If files differ from a release manifest, preserve the changes, identify their cause, and create new evidence; do not rewrite a receipt to hide the mismatch.

## Instantiate a harness

Use `tools/commission.py draft` for new prose, then author/review the grounded plan. Each requirement has an exact source span, interpretation, dependency and acceptance condition. Run `compile`/`validate` before `run`. See `docs/COMMISSION_COMPILER.md` for CLI/schema; the owner's commission is the worked example.

For a new direct host adapter, use `tools/supervise.py::TaskSpec` and `Supervisor`. Define command argv, cwd, hard deadline ≤300s, semantic deadline ≤120s, ordered milestones and output paths. Write staged outputs, print epoch-bound progress and let the supervisor publish verified bytes. Exit75 is the default classified transient failure; one retry shares the original deadline. Heartbeats never extend any deadline.

External LLM/Hermes workers consume a task envelope, inspect pinned source and return bound artifact receipts for review. A model-free worker executes an existing finite grammar/adapter. Neither may rewrite old evidence or self-certify scientific ACCEPT. There is no installed Hermes runtime claim. Tool credentials and authorization remain the host's responsibility.

## Independent initiatives

Use `tools/new_initiative.py NAME --base VERIFIED_COMMIT` to create `initiative/NAME` and a sibling worktree. Verify base manifest/evidence first. Pin upstreams and record scope, missing dependencies and acceptance gates. Make bounded commits. Do not overwrite another agent's branch or force-push main. The helper refuses dirty checkouts, existing destinations and branch collisions.

## Semantic rules

- Native product: own C++ renderer and native Android window/audio/lifecycle. Research documentation and SVG diagrams are not product UI. Preserve fullscreen, ink-first interaction.
- Exact bytes, numeric encoding, width, signedness, endianness, basis order, units, coordinates, clock, uncertainty, loss and replay witnesses are separate fields.
- Memory address, basis index, logical qubit and provider hardware address are distinct types.
- Quantum simulation is a declared classical calculation. Measurement has loss; amplitudes are not arbitrary classical words. Q-Strings are classical relational records.
- Atlas layout distance is not automatically physical distance, signal similarity or force. Edge type, transition law and units must be explicit.
- A rendered observation, model simulation, laboratory measurement and scientific discovery have separate evidence.
- Apply every project atlas domain in order as APPLICABLE, NOT_APPLICABLE with reason, or OPEN. An applicability table is not a mathematical proof.
- Preserve ACCEPT/REJECT/UNKNOWN/BLOCKED/NOT_STARTED and historical failures. Do not count reruns as new tests.

## Verification and stopping

Use original references and independent controls; record implementation, command, input/output hashes, measured result, tolerance and scope. New native code requires native tests and a real Android run before phone claims. New generators require malformed input, boundedness, replay and counterexample tests. Rerun broad unchanged science only for a concrete reason.

When blocked, publish a complete resume packet: source/commit, task IDs/epochs/deadlines, logs, verified hashes, failure classification, attempts consumed, missing dependency and exact next command. Retain late results for reconciliation; never accept them through a stale fence. A host interruption cannot be solved by claiming a heartbeat renewed a task.

Update `SUM.md`, the initiative record and gate evidence when behavior changes. Keep upstream artifacts intact; version adapters beside them. Validate remote source through a fresh clone and tree/blob census when publishing via Git APIs.
