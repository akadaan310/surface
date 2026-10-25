# PHANTOM × QUANTUM ORACLE scientific reference system

This standalone Python package contains finite typed quantum operators, Euclidean-coordinate function spaces, PHANTOM discovery cycles, public-data adapters and historical-target circuit compilation. It has no SURFACE rendering dependency. It is a **partial scientific increment**: the complete inherited initiative is not accepted, Android readiness is separate, and no quantum hardware was used.

Start with [coverage](coverage.json), [acceptance ledger](evidence/acceptance.json), [custody audit](../../docs/QUANTUM_ORACLE_CUSTODY_AUDIT.md), and [continuation](CONTINUATION.md). Exact original requirements are retained in [inherited obligations](evidence/inherited-obligations.json); source snapshots preserve the earlier checkpoint without rewriting its evidence.

## Reproduce

Tested environment: CPython3.10.12, Linux aarch64. Portable version pins are in `requirements.txt`; `requirements-linux-aarch64-py310.lock` additionally pins the exact wheels used here. The wheel lock is platform-specific; another platform must preserve its own wheel receipts and compare numerically, rather than claim the same environment.

From the repository root:

```sh
python3 -B tools/verify_repository.py
python3 -B tools/materialize_foundation.py
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r research/quantum_oracle/requirements-linux-aarch64-py310.lock
.venv/bin/python -B -m research.quantum_oracle.run --runs build/science-reproduction-001
.venv/bin/python -B -m research.quantum_oracle.run --replay build/science-reproduction-001
```

Use `materialize_foundation.py --check` if the immutable destination already exists. Every new run needs a fresh output directory. No data download or provider submission occurs during the scientific suite. An initial package installation needs the package index or locally retained matching wheels. On other platforms use the portable pinned requirements and record the changed environment.

The supervised worker runs the complete scientific tests and recomputes the finite discovery cycle. It publishes `tests.log`, `discovery.json`, and `verification.json` through the unchanged Supervisor. Limits are60s wall,45s semantic,50s CPU,2GiB address space,8MiB per output file, one BLAS thread and no retry. A failed attempt leaves logs and resume/fence records; a heartbeat cannot extend its deadline. The supervisor is a cooperating-process tool, not a hostile-code sandbox.

Read-only replay checks the source census, output hashes, Supervisor publication and fence, and recomputes discovery. It does not call historical absolute command paths or claim to rerun the retained tests. A fresh run performs fresh tests. `evidence/core-verification.json` and earlier receipts remain bound to their earlier source revisions; new evidence never changes those old hashes.

## Mathematical contracts

| Module | Implemented finite scope | Contract |
|---|---|---|
| `quantum.py` | States/density, basis/word/address distinctions, unitaries, Kraus channels, observables, metrics, measurements and exact declared byte encoding | [Quantum](quantum-contract.md) |
| `spaces.py` | XY domains and SPD metrics, separate layout, finite Fourier function/observable spaces, affine pullbacks, modal wave/free-Schrödinger and graph dynamics, admissible Hilbert isometry | [Spaces](spaces-contract.md) |
| `discovery.py` | Pinned PHANTOM finite synthesis, retained failed candidates, independent exhaustive/held-out/null/encoding challenge and event replay | [Research cycle](discovery-contract.md) |
| `astro.py` | Exact signed16 photographic FITS decoding and explicitly selected local TAN projection | [Astronomy](astro-contract.md) |
| `collider.py` | Exact observed educational CSV identity/offsets, four-vectors, scalar/vector comparisons, decimal-rounding counterexamples | [Collider](collider-contract.md) |
| `circuits.py` | Small typed circuit compilation against an authentic historical target subgraph, full-unitary verification, explicitly limited T1/readout surrogate | [Circuits](circuits-contract.md) |

The real FITS plate has795,663 pixels. Its local TAN approximation is not the full DSS plate solution; flux calibration, PSF, time-scale interpretation and pixel uncertainty remain UNKNOWN. DSS attribution and reuse restrictions are preserved with the data.

The CERN sample contains100,000 selected observed dimuon events under CC0. Printed four-momenta and published masses are not assumed mutually consistent: every counterexample is retained. Its educational selection and absent detector/weight/systematic metadata prevent a full physics-analysis claim. CSV does not discharge ROOT/HepMC obligations.

The IBM Brisbane snapshot is historical calibration evidence from2025, pinned to a public upstream revision. It is not a current device contract. A serial zero-temperature T1 model and independent readout confusion are named assumptions; T2, crosstalk, leakage and pulse dynamics are not silently inferred. No credentials, queue submission or physical shot receipt exists.

## Evidence and review

The unchanged commission compiler preserves the current owner directive with exact UTF-8 spans and an explicit23-domain applicability review. Its source-integrity/foundation-audit tasks passed under the unchanged Supervisor; those task results do not grant scientific ACCEPT. University62-topic identities are organizational structures only.

Core tests include analytic controls, untouched-seed compatibility, Qiskit comparisons and independent reviewer counterexamples. Review found and repaired missing replay-receipt admission, nested allocation, mutable source pins, collapsed coordinates, typed qubit admission, unstable self-distance and graph null-mode/energy errors. Rejections and prior receipts remain preserved. No native source or manual-only CI policy changed.

The repository manifest binds every tracked artifact except itself. It is anchored by Git history, not an author signature. Source/data hashes establish custody; scientific correctness additionally depends on the stated model, independent comparisons and limitations. See the acceptance ledger for exact gate statuses and the continuation file for remaining work. No SURFACE SCIENTIFIC INTEGRATION READINESS REPORT is issued while prerequisite gates remain unresolved.
