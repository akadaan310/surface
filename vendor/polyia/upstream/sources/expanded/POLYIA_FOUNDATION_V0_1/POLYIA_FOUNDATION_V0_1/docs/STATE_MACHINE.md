# Codex implementation state machine: POLYIA-HARNESS/0.1

## State definition

`H=(S,E,δ,s0,F,G,L)` where `S` are states, `E` labeled receipts, `δ` guarded transitions, `s0=PREFLIGHT`, `F={RELEASE_CANDIDATE}` (a milestone, not automatic production), `G` validation gates, and `L` append-only hash-chained event log. Source trust, system capability, and evidential confidence remain different dimensions.

| State | Required work | Guard to next state |
|---|---|---|
| PREFLIGHT | Inspect Oracle VM CPU/RAM/disk/services and source safety; establish isolated worktree | `environment-audit` |
| INVENTORY | Enumerate source repo refs, snapshot hashes, existing operators, grants and missing sources | `source-ledger` |
| EXTRACT | AST-led operator and capability extraction with source locators; do not execute unknown code | `candidate-inventory` |
| CLASSIFY | Deduplicate by *semantic* signature and declare separate implementations | `typed-contracts` |
| FORMALIZE | Specify type/effect/evidence laws, towers, pillars, negative grammar, costs | `law-and-negative-tests` |
| IMPLEMENT | Build independent package interfaces, compiler, registry, approved adapters | `unit-test-report` |
| VERIFY | Contract tests, independent reproductions, property and mutation tests | `integration-and-roundtrip` |
| ASSEMBLE | Compose PHONEX specialists, agency bundles, CLI, localhost API and rendered artifacts | `benchmark-and-counterexamples` |
| BENCHMARK | Compare baseline query engines, plan/compile/run times, memory, false relations | `release-gate` |
| RELEASE_CANDIDATE | Freeze versions, complete manifests, await explicit production approval | Terminal until separate authorization |

A failed guard leaves the state unchanged and creates a failure receipt/diagnostic. **Negative evidence is not thrown away**. Return to a prior stage on explicit policy with a new version; never erase a previous ledger entry. No automatic public GitHub pushes, credential consumption, network exposure, production symlink change, secret recording, or external repository modification.

## Truthful checkpoint protocol

For each stage Codex must commit *locally*:

`receipt=(source_manifest_hash, stage, tests, failures, coverage, elapsed, next_guard, responsible_process, code_sha256, evidence_sha256)`

Every event includes previous event digest. A checkpoint with no real content file and independent hash is not a successful gate. The included Python reference only checks the receipt SHA-256 *format*; it does **not** validate backing bytes/signatures, actor authorization, staged changes, or genuine test results. Codex must implement and prove those checks before using it as an enforcement boundary.

## Atomic capabilities, nested machines

A package may itself be a composed automaton with a typed external boundary. A higher agency sees only that boundary, not its internal functions. Valid composition is by ABI/WIT/IDL and resolved versions. Allow stateful kernels only when they publish explicit lifecycle effects, their concurrency model, and a replayable state transition protocol.

## Source-backed extraction rubric

For every candidate atom, `origin`, `commit/tree SHA`, `source path`, `symbol`, `tests`, `license`, `interface`, `effects`, `determinism`, `runtime`, `proof-or-falsification`, `implementation-reuse-allowed`, `adapter-only`, `ownership`, `export-permission`, `proposed canonical signature`. Assign one of `existing-tested`, `existing-untested`, `defined-not-implemented`, `proposed-only`, `unavailable`. Merely finding an operation name is not proof of its behavior.

## Responsible prioritization

1. Source manifests + six-division registry lock.
2. Contract extraction, compiler kernel and local harness.
3. First independent atom package (finite-state machine), then one operator from each university division.
4. Compiled P9/parenthology and tower/pillar witness adapter.
5. PHONEX specialist models: English and Arabic only **after validated corpora**, then more languages by same interface.
6. Word-set query graph and negative etymology guards.
7. Concierge produces specialized SDK and state-machine composition with real execution.
8. ASTRO/HOMELESS 3D and physics adapters via ports, without borrowing user projects as if completed.
9. CIA Browser/PURL/SEURL/ACSP boundary adapters, no capability escalation.
10. Efficiency, coverage, independent evaluation and release promotion.

## CLI reference harness

```
python3 -m polyia harness init --dir /tmp/polyia-state
python3 -m polyia harness status --dir /tmp/polyia-state
# Once a genuine audited evidence receipt exists:
python3 -m polyia harness advance --dir /tmp/polyia-state --receipt /path/to/evidence-receipt.json
python3 -m polyia harness verify --dir /tmp/polyia-state
```

Do **not** counterfeit passing receipts to advance this harness. Its status is a progress marker, not a secure supply-chain attestation until expanded.
