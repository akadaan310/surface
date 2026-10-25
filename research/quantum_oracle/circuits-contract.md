# Historical calibration circuit contract

This module compiles and simulates a bounded logical circuit against an authentic
**historical** IBM Brisbane snapshot. It executes no provider submission and
requires no IBM credentials. The demonstrated finite compilation and surrogate
checks do not establish current hardware behavior or complete Oracle G5.

## Exact source and acquisition

The retained source is the public
[Qiskit IBM Runtime repository at revision `1dd86e381ddecfc78db94e3287a9ce57e4ad65d8`](https://github.com/Qiskit/qiskit-ibm-runtime/commit/1dd86e381ddecfc78db94e3287a9ce57e4ad65d8).
GitHub plugin repository, branch and file metadata were inspected before bounded
raw downloads from that immutable commit. The local bytes' Git blob SHA-1 values
match the inspected metadata. The source license is Apache-2.0; its original
`LICENSE.txt` is retained. No root NOTICE file was present in the pinned directory
listing. Downloads were capped at 1 MiB per file and a 20-second HTTP timeout.

| File | Exact bytes | SHA-256 |
|---|---:|---|
| `conf_brisbane.json` | 147,793 | `309836dbf54cf635d811a273a3b4e1c933debdbea71c33b689ea1b71deafc2d2` |
| `props_brisbane.json` | 353,470 | `bc8b29433a8e1935a8f5537cafccc63194dc5ed5137edba684ff3fb77b269d1d` |
| `LICENSE.txt` | 11,416 | `7b7de08c64b1824bdc2b9f4b530814a9d0b5905a38ad0e96a717f3dd46d2bbe7` |

The files, exact raw URLs, acquisition time, source revision and license are in
[`fixtures/ibm_brisbane_snapshot/provenance.json`](fixtures/ibm_brisbane_snapshot/provenance.json),
with selected GitHub metadata alongside. Retrieval was **2026-10-25T17:08:08.887359Z**.
The properties' last-update timestamp is **2025-02-26T14:33:06-05:00**, or
**2025-02-26T19:33:06Z**. Individual parameters have their own older dates: for
example, qubit 0's T1 sample is from January 2025. All original parameter dates
remain in the unmodified properties bytes. No freshness period is invented.
IBM describes these fake-provider inputs as past system snapshots unsuitable for
claims about the latest device behavior ([official fake-provider documentation](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/fake-provider), accessed 2026-10-25).

`load_snapshot` checks the fixed source hashes before decoding. `admit_snapshot`
accepts explicit source digests, commit and acquisition time for controlled
testing; those supplied identifiers are integrity assertions, not external
authentication. It rejects duplicate JSON keys, nonfinite values, missing
required selected calibrations, unrecognized time units, timezone-free or future
dates, wrong backend identity, invalid addresses and disconnected selections.
Unselected calibrations remain in the preserved source but are not promoted into
the selected executable target. Reset metadata present in the source is retained
but is outside this unitary compiler's supported operations.
Each snapshot object retains its immutable configuration and properties bytes.
Construction re-derives and compares every selected semantic field against those
hash-bound bytes, so changing a duration, error, date or coupling while retaining
the original source identity rejects. Selected tuples are bounded before their
validation loops: at most 32 gate records and 12 directed edges, with duplicate
edges rejected.

## Types, target and finite execution

`CircuitOp` uses `LogicalQubit` addresses, never byte offsets or provider indices.
`CircuitIR` admits 1–4 qubits, the explicit LSB convention, and an immutable tuple
of at most 32 operations from I, X, Y, Z, H, S, T, RX, RY, RZ and CX. Angle and
address validation follows `quantum.py`. A selected target has exactly the same
number of physical sites as the logical register; unused ancillary sites are
not silently introduced.

`CalibrationSnapshot`, `QubitCalibration` and `GateCalibration` describe the
selected provider subgraph. All gate durations are explicitly converted from
source units to seconds. Source error rates and T2 are retained as metadata even
when the surrogate does not use them. `HardwareQubit` addresses bind provider,
backend, site and the exact properties SHA-256. Logical indices, local physical
array slots and provider site IDs are separate fields.

The demonstrated selections are physical sites 0–1, 0–2 and 0–3. Their directed
native edges are respectively `(1,0)`, `(2,1)` and `(3,2)`, with gate family
`ecr,id,rz,sx,x`. The full supplied device has 127 sites; this adapter never
allocates a 127-qubit state. A `qiskit.transpiler.Target` is constructed from the
selected real durations, reported gate errors and directed edges. Qiskit 2.2.3
uses a fixed initial layout, trivial layout selection, basic routing,
optimization level zero, approximation degree one, explicit unsigned 32-bit
seed and one worker process. This is a deterministic selected compiler path,
not an optimization or minimum-cost claim. IBM describes the topology and gate
translation roles in its [transpiler documentation](https://quantum.cloud.ibm.com/docs/en/api/qiskit/transpiler), accessed 2026-10-25.

Compilation rejects output beyond 256 native operations. A callback rejects
more than 128 transpiler passes or more than 15 seconds observed at a pass
boundary. The callback cannot interrupt a hung native pass; callers must retain
the enclosing process supervisor's hard deadline. These limits do not provide
an operating-system sandbox. The source parser admits at most 512 declared
provider sites, 2,048 couplers and 8,192 calibration gate records, within the
1 MiB source-file cap. Only 1–4 selected sites are executable.

## Full-unitary witness and mappings

`CompiledCircuit` retains all native operations, global phase, initial and final
hardware mappings, the output basis permutation, gate durations, reported gate
errors, seed and source properties digest. Every operation is checked against
its calibrated native address and directed coupling.

An independent native-matrix path embeds analytic I, X, √X, RZ and ECR matrices
with explicit scalar bit-index loops. ECR uses the published
`(IX-XY)/sqrt(2)` matrix with the first argument as the low-order local tensor
bit ([IBM ECR matrix convention](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.ECRGate), accessed 2026-10-25).
The compiler's global phase is applied and the final routing permutation is
undone. The resulting **entire** matrix is compared with the logical circuit
constructed through `quantum.py`, absolute tolerance `1e-10`. This checks every
basis input and phase, not only the all-zero output probabilities.

Direct construction of a compiled record repeats that witness, retains the
validated snapshot, and rejects forged gate actions, mappings, duration sums and
calibration error reports. Immutable records
prevent ordinary post-construction mutation. Simulation additionally verifies
that each native operation's duration, error and hardware mapping match the
supplied snapshot. This remains a trusted Python library, not protection against
deliberate interpreter/object tampering.

## Explicit calibrated surrogate

`simulate_surrogate` starts with the all-zero register. For each native gate it
applies the ideal unitary, then zero-temperature amplitude damping to **every**
selected qubit for that gate's duration. Each damping probability is
`gamma = 1 - exp(-duration/T1)`, evaluated stably using `expm1`. Its two Kraus
operators are `diag(1,sqrt(1-gamma))` and `[[0,sqrt(gamma)],[0,0]]`.

This is an intentionally **serial** schedule: the duration reported is the sum
of gate durations, not a device schedule or measured wall time. Virtual RZ gates
have the snapshot's zero duration. Idle qubits also damp during every nonzero
gate interval. The model neglects T2 dephasing, thermal excitation, crosstalk,
leakage, pulse dynamics and non-Markovian noise. Reported gate error is an
infidelity statistic; it is **not** converted into a depolarizing probability or
multiplied into an asserted hardware success probability.

Readout is a separate classical channel. For each qubit, the retained
`prob_meas1_prep0` and `prob_meas0_prep1` define a two-by-two column-stochastic
assignment matrix. Their tensor product assumes independent readout. The final
quantum density and observed probabilities are permuted back to logical order.
All these assumptions are returned in the result and receipt. Counts are local
PCG64 multinomial samples from that model, with the seed, shot count and NumPy
version pinned; no laboratory measurement is represented.

## Executed cases and replay

The 12 circuit test methods cover authentic source/unit interpretation, source
tampering, malformed dates/addresses/fields, typed IR rejection, replay,
one-qubit targets, output budget rejection, directed-gate checking, nonlocal
routing and its final permutation, forged compiled records, and independent
Qiskit Kraus/readout calculations. The first eight methods failed on the absent
module before implementation. Later malformed-result tests exposed and then
verified the direct-construction validators.
An independent reviewer reproduced a source-binding counterexample; the final
regression checks reject edited snapshot fields and compiled calibrations,
future samples, and a 10,000-fold coupling expansion while retaining the original
digests. The reviewer independently re-ran those challenges successfully after
the repair.

```sh
.venv/bin/python -B -m unittest research.quantum_oracle.tests.test_circuits -v
.venv/bin/python -B -m research.quantum_oracle.tests.test_circuits --receipt build/new-circuit-comparison.json
```

The receipt command refuses to overwrite an existing output. It compiles the
three cases and records source/code hashes, native gate counts and operations,
calibrations, mappings, errors, model probabilities and 4,096 simulated shots.
The independent calculation uses Qiskit's own native-gate matrices and Kraus
evolution, plus scalar sums for the readout channel. It shares low-level
NumPy/linear-algebra dependencies with the adapter.

| Selected sites | Native ECR count | Serial duration | Full-unitary maximum error |
|---|---:|---:|---:|
| 0,1 | 1 | 1.08 μs | `2.13e-15` or less |
| 0,1,2 | 4 | 3.72 μs | `2.56e-15` or less |
| 0,1,2,3 | 7 | 6.36 μs | `2.71e-15` or less |

The executed three-case receipt has maximum density/readout differential error
below `1.62e-15`, against tolerance `3e-14`. These are finite conformance results
for known mathematics. Scientific acceptance remains scoped to the declared
historical target and surrogate. Current calibration, hardware execution,
provider queue/pricing, pulse scheduling, broader backend families and complete
G5 remain **UNKNOWN** or unexecuted. No credential, submission or spend was used.

The final source-bound case receipt is
[`evidence/circuit-compilation-v3.json`](evidence/circuit-compilation-v3.json).
Earlier v1/v2 receipts remain separate records of the earlier code and test
revisions; they do not establish verification of the final revision. The primary
documentation extraction is retained in
[`evidence/circuits-reference-extraction.json`](evidence/circuits-reference-extraction.json),
27,534 bytes, SHA-256
`3cc0f3f7a41fac4bc137cb41d9fb7964a259f2f5480bd9a781724c77dae444c5`.
That checksum binds the `web.run` extraction response and access time, not the
original website's HTTP bytes. The downloaded calibration and license files,
in contrast, preserve their exact raw HTTP payload bytes.
