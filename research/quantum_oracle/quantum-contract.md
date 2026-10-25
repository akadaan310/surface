# Finite quantum admission contract, version 1

`quantum.py` is a separate classical numerical reference adapter. It leaves the
V3 seed and original Oracle unchanged and does not modify native SURFACE code.
It closes the tested finite admission cases; it does not close the full Oracle
G0–G7 commission, implement every quantum operation, establish new physics, or
claim calibrated or physical hardware execution.

## Types and finite domain

| Type or operation | Admitted meaning and bound |
|---|---|
| `ClassicalWord` | Unsigned exact integer, width 1–64. A quantum lift additionally requires width equal to the register size. |
| `Basis` | 1–4 qubits, dimension 2–16; explicit `qubit_0_lsb` or `qubit_0_msb`. Integer index still addresses the corresponding array element. |
| `BasisIndex`, `LogicalQubit`, `ByteOffset`, `HardwareQubit` | Distinct classes; no implicit address conversion. Hardware fields identify a declared provider/device/site/calibration ID; they do not authenticate a provider snapshot. |
| `StateVector` | One dimensional finite complex128 array of exactly the declared dimension; squared norm within absolute `1e-10` of one. |
| `DensityMatrix` | Square finite complex128 array, Hermitian and trace one within absolute `1e-10`; eigenvalues at least `-1e-10`. |
| `ProbabilityDistribution` | Finite real nonnegative vector with mass one within absolute `1e-10`; no amplitude or phase semantics. |
| `Unitary` | Square finite matrix satisfying `U†U ≈ I`, elementwise absolute tolerance `1e-10`, no relative tolerance. |
| `StochasticMap` | Square column-stochastic real matrix; `p_after = P @ p_before`. It accepts distributions, never quantum states. |
| `QuantumChannel` | 1–16 square Kraus operators, `Σ K†K ≈ I` at `1e-10`. The Kraus construction supplies complete positivity; completeness supplies trace preservation within numerical tolerance. Only equal input/output dimensions are implemented. |
| `Observable` | Hermitian operator, explicit unit label, coefficients bounded by magnitude `1e6`. |
| `Hamiltonian` | Angular-frequency generator `H/ℏ`, explicitly in `rad/s`; Joule-valued Hamiltonians require an external unit conversion and are rejected directly. |
| `MeasurementRecord`, `MeasurementOutcome` | Validated counts/probabilities and computational-basis postselection, always explicitly lossy. At most 100,000 shots, unsigned 64-bit seed. |

Inputs are bounded lists, tuples or NumPy arrays. Shape checks occur before the
numeric copy; generators and arbitrary implicit coercions are rejected. Numeric
strings, boolean arrays and complex-to-real coercion are not admitted. Python
integer fields reject booleans, floats and NumPy scalar aliases. Array records
hold immutable bytes; each `.data` access returns a detached copy. Ordinary
Python object tampering is outside this scientific API's trust boundary.

Admission never repairs source states, silently changes basis, or normalizes
source bytes. The tolerance is a finite floating-point admission policy, not a
proof of exact positivity or exact unitarity. Operation outputs are admitted
again; accumulated error can cause a long circuit to reject rather than silently
renormalize. `run_circuit` accepts a concrete list of at most 256 unitaries.
The channel Choi array is at most 256×256 complex128 (1 MiB). These are logical
input/work bounds, not an operating-system sandbox or a real-time guarantee.

## Representations, operations and loss

`basis_lift` injects the admitted integer into a computational-basis vector. It
does not identify arbitrary coherent states with classical words. `rebase`
explicitly reverses bit significance when changing LSB/MSB conventions while
preserving logical-qubit labels; density matrices permute both indices. Operators
and states with different basis metadata reject until an explicit adaptation.
IBM documents why integer significance, diagram order and state-vector index
order must be handled separately ([bit ordering](https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering)).

The implemented gate family is I, X, Y, Z, H, S, T, RX, RY, RZ and controlled-X.
Rotation angles are finite radians with magnitude at most `1e6`. `evolve_closed`
uses the spectral decomposition of a Hermitian angular-frequency generator and
`exp(-i (H/ℏ) t)`, supporting pure and density states. Absolute time is bounded by
`1e6` seconds and absolute eigenphase by `1e6` radians. These caps avoid unbounded
work; they do not certify phase accuracy for every ill-conditioned or rapidly
oscillating model. Lindblad integration, pulse compilation, calibrations and
general rectangular channels remain outside this adapter.

`QuantumChannel.apply` requires an explicit density operator. Its Choi convention
is `J[(a,i),(b,j)] = Φ(|a><b|)[i,j]` with column-vectorized Kraus matrices; its
trace is the input dimension, not one. For the implemented finite dimensions,
Kraus, Choi and channel actions are numerical representations of the established
channel construction ([IBM channel representations](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/quantum-channels/representations-of-channels)).

`probabilities` obtains Born weights, clips only negative roundoff accepted by
the density tolerance, and divides by their sum. This is an explicit numerical
observation policy, bounded by admission error; it does not modify the stored
state. `measure` samples a NumPy PCG64 multinomial distribution for independent,
identically prepared systems. A seed plus the pinned NumPy version is required
for count replay. Counts are not a sequence of repeated measurements of a single
collapsed state and do not constitute laboratory observations. `project_measurement`
records a selected outcome probability and its computational-basis projector,
rejecting impossible outcomes. Sampling and postselection discard phase and
cannot reconstruct the input state. General POVMs and partial-register
measurement are not implemented.

`expectation` reports `Tr(ρ A)` in the observable's declared unit; `variance`
reports `Tr(ρ A²) - Tr(ρ A)²` in the squared unit. Final tiny negative variance
roundoff is clipped to zero. The returned scalar does not replace the state.

## Metrics and numerical interpretation

Fubini–Study is the pure-state ray angle in radians, range `[0, π/2]`. The
implementation normalizes temporary representatives, aligns their relative
global phase, and evaluates
`2 atan2(||a-b_aligned||, ||a+b_aligned||)`. Stored input bytes are unchanged.
This avoids the loss of relative precision in `acos(abs(<a,b>))` near equal rays.
Tests include twelve deterministic complex vectors of dimension sixteen with
random global phases and a `1e-7` radian separation control.

Trace distance is `½ ||ρ-σ||₁`, computed from the Hermitian difference's
eigenvalues. `state_fidelity` uses **squared** Uhlmann fidelity; it is an
equivalence measure, not itself a distance. All three density metrics use
explicit temporary mathematical representatives: normalized pure vectors, or
Hermitian positive-semidefinite density matrices projected within admission
roundoff and divided by trace. Their stored source bytes remain unchanged.
This ensures that accepted trace/norm residuals do not masquerade as physical
distance. Fidelity clips final roundoff to `[0,1]`.

Bures distance is mathematically `sqrt(2 - 2 sqrt(F))`. Its implementation avoids
the cancellation of that expression near equality: for pure states it uses
`2 sin(FubiniStudy/2)`; otherwise it uses the Frobenius norm of optimally aligned
matrix square roots. If `A=sqrt(ρ)`, `B=sqrt(σ)` and `A†B=U S V†`, the alignment
is `V U†`, minimizing `||A-B V U†||_F`. Expanding this squared norm gives
`Tr(ρ)+Tr(σ)-2 Tr(S)`, the same normalized Bures expression. Eigenvalue/square-root
conditioning near rank deficiency still limits floating-point accuracy; no
exact real-arithmetic metric certificate is claimed. The fidelity
convention agrees with the [Qiskit quantum-information API](https://quantum.cloud.ibm.com/docs/en/api/qiskit/quantum_info#state-fidelity).

Equal computational-basis probabilities do not establish equal rays or equal
density operators: the plus/minus pure-state control has equal probabilities
but Fubini–Study distance `π/2`. The coherent plus state and the uniform diagonal
mixture have trace distance `1/2` and purities one versus `1/2`. Metrics here do
not describe layout distance, physical force, memory-address similarity or
universal classical/quantum equivalence.

## Versioned byte and legacy admission

`encode_state` / `decode_state` use `quantum-oracle.statevector/1`, explicit
little-endian complex128 real/imaginary pairs, exact integer shape, qubit count,
basis order and normalization policy. SHA-256 binds the payload separately from
the canonical JSON interpretation including payload. Signed zeros round-trip
exactly on the declared IEEE-754 representation. NaNs and infinities reject.
The digest establishes internal integrity, not authenticity: a party able to
change and rehash a record can author a new interpretation. Preserve original
source bytes and an externally anchored digest in the enclosing substrate IR.

`admit_v3_seed` imports only the exact `complex-f64-le/1` seed fields and its
literal LSB basis label. It verifies raw-byte metadata, declared dimensions,
payload digest, finite values and norm. The normalized three-amplitude seed
counterexample and changed basis label reject. The original seed is never
patched and remains a conformance fixture.

Inspected immutable sources:

| Source | SHA-256 |
|---|---|
| `build/foundation/QUANTUM_ORACLE_V3_EXTENSION/atlas_quantum/core.py` | `637368c05000fbcb2e7739cd7b9abe134be6b42222a2bab32bbcc880439369f6` |
| `build/foundation/quantum_oracle/quantum_oracle/core.py` | `82efce911b2bcdc42f42872aea97ff320a7bdc9341b3267b5fa486354c970178` |

## Executable evidence and scope

Run from the repository root after materializing the immutable foundation and
installing the pinned scientific environment:

```sh
.venv/bin/python -B -m unittest research.quantum_oracle.tests.test_quantum research.quantum_oracle.tests.test_qiskit_reference -v
```

The 33 test methods cover rejected shapes/nonfinite values/normalization; address-type
confusion; LSB/MSB adaptation; immutable state storage; byte and interpretation
tampering; seed and original Oracle gate conformance; pure/mixed distinctions;
phase and metric controls; unitary inversion and circuit bounds; analytic Pauli
dynamics and independent SciPy matrix-exponential comparisons; scalar-loop
state/channel action; Kraus completeness and Choi positivity/partial-trace
controls; measurement reproducibility/loss; and direct measurement-record
validation; normalization-residual metric regressions; and nested-data rejection
before numeric allocation. The scalar implementations use explicit sums rather than production
matrix-multiplication helpers. They are independent finite implementations, not
separate physical devices or full industrial quantum backends.

The required Qiskit 2.2.3 suite separately constructs phase-sensitive circuits
for 1–4 qubits, compares three amplitude-damping channels and Choi matrices,
and compares fidelity on four seeded mixed-state pairs. Trace-distance controls
use SciPy singular values rather than the production Hermitian eigenvalue path.
Bures controls derive from Qiskit's independent fidelity result for states well
away from the near-equality cancellation regime. These produce **22 measured
comparison rows**, plus a relative-phase negative-control test. The comparisons
share NumPy/SciPy and low-level linear algebra, so they do not demonstrate fully
independent numerical stacks. Missing Qiskit causes a test error rather than a
passing skip. QuTiP was not installed: its source-build attempt reached the
task's 300-second bound and was stopped.

An actual measured comparison receipt is generated by:

```sh
.venv/bin/python -B -m research.quantum_oracle.tests.test_qiskit_reference --receipt research/quantum_oracle/evidence/backend-comparison.json
```

The command refuses to overwrite an existing receipt. It records executed time,
exact code and numeric fixture hashes, operation recipes or random seeds,
versions, tolerances and observed errors. Its comparison statuses evaluate
declared numerical predicates; the encompassing scientific gate still requires
review and remains open beyond these finite cases.

The initial 21 test methods were executed red before implementation, then green.
Four subsequent adversarial cases exposed unvalidated measurement dataclasses,
float shape coercion and stochastic overflow; the fixes were checked with those
tests. Original Oracle gate conformance added a separate source comparison.
Repeated runs are not new scientific trials. Numerical comparisons use the
explicit tolerances in the test assertions, generally `1e-14` or tighter;
admission tolerance remains `1e-10`. Test success is finite numerical evidence,
not a theorem covering all admitted matrices.

## External reference provenance

The three IBM primary documentation URLs linked above were accessed through
`web.run` on **2026-10-25**. Direct HTTP byte acquisition returned `403 Forbidden`
for each URL; no raw HTML download is claimed. The preserved web extraction
response, including exact URLs, is a **25,139-byte** JSON artifact with SHA-256
`e46177ae3dfd2271880331aa2432f992c474f155ddeb79d9228e75da95497983`.
This hash identifies the extraction response, not IBM's original HTTP bytes.
The task-level evidence packet retains the extraction and failed byte-download
receipt; online documentation can subsequently change. These references support
conventions and formulas; they do not serve as execution evidence.
