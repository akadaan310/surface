# Mathematical N-atlas: contracts, distinctions and acceptance gates

This document makes the full V3 mathematical obligations explicit without promoting its small executable seed to a finished atlas. It is an integration specification and evidence map. The immutable authority is `QUANTUM_ORACLE_V3_EXTENSION/CONSTITUTION_V3.md`, together with V2’s constitution and the inherited PHANTOM commission. Exact identities, fresh original tests, and observed seed counterexamples are recorded in [`v3-consolidation-audit.json`](../evidence/v3-consolidation-audit.json). Source roots and callable implementations are listed in [FOUNDATION_INVENTORY.md](FOUNDATION_INVENTORY.md).

Surface’s existing `include/surface/atlas.hpp` and [ATLAS.md](ATLAS.md) describe an observed astronomical point catalogue and camera projection. They are a different subsystem from the commissioned **N-ATLAS COMPILER** of simultaneously coexisting function charts. The current native renderer has no browser or WebGL runtime. An eventual interactive N-chart scene must use Surface’s native rendering interfaces and retain numerical/provenance witnesses independently of visible pixels.

## 0. Stable mathematical domain-review catalogue

The commission compiler uses the following **23 ordered domain IDs**. Their order and ASCII spellings are stable integration identifiers. Complete coverage means that a project review accounts for every row with an applicability decision, reasoning and any required witness. It does **not** mean that the project implements or has exhaustively reviewed all of mathematics. A parser’s successful coverage check proves that entries are present and well formed; it does not prove their scientific conclusions.

For every candidate, retain applicability (`applicable`, `not applicable`, or `unknown` in the chosen versioned schema), the object/domain, assumptions, a precise claim, proof/test obligations, counterexamples/controls, budget, evidence references and an independent verdict. A theorem requires a valid proof under its stated assumptions. A finite experimental match remains a scoped computational observation. A domain may correctly be inapplicable; require a reason rather than forcing a metaphor.

| Ordered domain ID | Review question and obligation | Example challenge/control |
|---|---|---|
| `logic` | Are propositions, guards, quantifiers and inference rules explicit? | Missing evidence and cyclic self-support must not yield truth |
| `set_theory` | Are objects, membership, domains, products and cardinality bounds defined? | Test empty/duplicate inventories and distinguish finite sets from potentially unbounded families |
| `type_theory` | Do constructors, domain/codomain and composition preserve declared types? | Reject a byte offset passed as a physical qubit ID or a mismatched composition |
| `arithmetic` | Are valuation, width, signedness, rounding and overflow specified? | Carry injection, XOR and assignment must produce distinct expected traces |
| `algebra` | Which laws actually hold: closure, associativity, identity, inverse, distributivity? | Noninvertible masks cannot be admitted as group elements under the same operation |
| `order_lattices` | Is the relation a partial/total order; are meets/joins defined where claimed? | Test antisymmetry/transitivity and incomparable cases rather than infer order from labels |
| `combinatorics` | What is counted and what is the finite search bound? | Candidate programs, distinct functions and successful outputs have different denominators |
| `graph_theory` | What do vertices/edges, direction and weights mean? | Different edge types and disconnected components must remain distinguishable |
| `automata_languages` | What grammar, states, transitions, guards and acceptance rules execute? | Test rejected words, illegal transitions, cycles and budget exhaustion |
| `information_coding` | What information is preserved, compressed or lost under the codec? | Retain source bytes; test tampering, alternate encoding, distribution shift and noninvertibility |
| `geometry` | What coordinate spaces, units, metrics and transformations are admitted? | Move layout origins without changing a function or quantum state |
| `topology` | What cover/complex/topology and continuity conditions support the claim? | A graph one-skeleton and a filled complex need not have the same homology |
| `analysis_calculus` | What domains, regularity, derivatives, measures and convergence conditions apply? | Test boundaries, nondifferentiable cases and sampling ambiguities |
| `differential_equations` | What evolution law, initial/boundary data and well-posedness assumptions apply? | Compare analytic solutions and convergence under a refined time step |
| `spectral_harmonic` | What basis, transform normalization, window and spectral interpretation apply? | Test phase loss, aliasing, Parseval conventions and failed inverse reconstruction |
| `probability_statistics` | What random process, likelihood, estimator, independence and uncertainty are assumed? | Null controls, held-out data, multiple-testing corrections and equal probabilities with different states |
| `optimization_control` | What objective, constraints, admissible controls and termination criteria are used? | Compare a strong baseline; distinguish a local/search-order optimum from a global optimum |
| `numerical_analysis` | What precision, conditioning, stability and error/tolerance contract applies? | Cross-implementation comparison, malformed/nonfinite input and changed discretization |
| `category_composition` | What objects/morphisms compose; do identity, associativity and preservation diagrams hold? | Type-compatible syntax alone does not prove a functor or naturality law |
| `physics_units` | What physical model, dimensional analysis, conserved quantities and regime apply? | Do not infer force/energy from layout distance or equate dark-current calibration with dark matter |
| `quantum_information` | What state/channel/measurement semantics, basis order and equivalence convention apply? | Relative-phase, positivity, CPTP, measurement-loss and logical/physical-address controls |
| `computation_complexity` | What are state/search/work/memory bounds and the cost model? | Distinguish logical fuel, gate count, serialized bytes, elapsed time and resident memory |
| `metrology_uncertainty` | What was measured, with which calibration, traceability and error propagation? | Distinguish simulated output from observation and stale calibration from current evidence |

The sources for the review families are V2 §§1–66, V3 §§1–24 and PHANTOM’s preserved mathematical-rake/finite-bound contracts. This catalogue is the project’s finite organizational schema. It adds no automatic theorem, physical claim or universal generator guarantee.

## 1. Which space is being described?

V3 defines an atlas

$$
\mathcal A=(I,\{U_i\},\{\varphi_i\},\{o_i\},\{g_i\},\{F_i\},E,T).
$$

That tuple needs concrete schemas before its vocabulary establishes a mathematical object:

| Object | Required meaning | Must remain distinct from |
|---|---|---|
| `chart_id` in finite set `I` | Stable identity of a chart/version | Screen index, memory location, physical site |
| Chart domain `U_i` and coordinates `varphi_i` | Declared subset and coordinate map, with dimension and coordinate units | A graph of a plotted function, which may itself be one-dimensional |
| Chart origin | Declared local coordinate origin | The independently placed origin of the chart in a visual layout |
| Local metric `g_i` | A finite symmetric positive-definite matrix for a declared local Euclidean metric | Function similarity or interaction strength |
| Placement `o_i` in ambient layout space `L` | Finite coordinates, frame, units, dimensionality and placement metric | Telescope distance, Hilbert-space distance, or measured coupling |
| Observable `F_i` | Typed function/domain/codomain, units, parameters, source, uncertainty and evaluation convention | The coordinate system that displays it |
| Edge `E` | A typed relation: overlap, representation transform, coupling, dependency or logical relation | Automatic adjacency merely because two chart IDs exist |
| Map `T_ij` | An explicitly admissible, versioned transformation with domain guards and witnesses | An operation-name string such as `sine->derivative` |

For a constant positive-definite `g_i`, the local distance is

$$
d_i(u,v)^2=(u-v)^Tg_i(u-v).
$$

Admit this only after checking shape, finite entries, symmetry, positive definiteness and unit consistency. If the matrix varies with position, a further geometry and path-length contract is needed; a pointwise quadratic form is not automatically a Euclidean distance between arbitrary points. If axes carry unlike units, such as seconds and metres, first declare a meaningful conversion or nondimensionalization. A unit string attached only to a chart origin does not supply units for all coordinates and observables. These are implementation obligations from V3 §§1–5, not properties proved by a label.

The ambient distance is separately

$$
D(o_i,o_j)=\|o_i-o_j\|_L
$$

under a declared metric on `L`. The seed computes `math.dist` and checks only equality of the two origin-unit strings. Origins `(0,0)`, `(3,4)`, `(6,0)` yield distances **5, 5, and 6**. Their meaning is layout separation. They do not establish closeness of functions, physical force, quantum fidelity, or statistical dependence. [Source: `V3:atlas_quantum/core.py::Atlas.distance`, `edge`, `edges`; `examples.py`; audit valid fixtures.]

The seed also accepts three-coordinate origins and nonfinite coordinates. Its `Chart` type annotation does not enforce XY shape at runtime. The full metric gate therefore requires a stricter adapter and invalid-input tests, while leaving the source seed unchanged. [Audit counterexamples `non-xy-origin-admitted`, `nonfinite-origin-admitted`.]

## 2. Coordinate transitions and observable transformations

For two coordinate views of the **same scalar observable**, an overlap transition must satisfy

$$
F_j\circ T_{ij}=F_i
$$

on the declared common domain, either exactly or within an explicitly measured error. The transition needs domain/codomain, inverse conditions, Jacobian where relevant, units, boundary rules, loss policy and provenance. Test identities, inverse composition and triple-overlap consistency where the chosen atlas definition requires them. A layout edge does not establish that the underlying domains overlap. [V3 §§1,3,4,17.]

A derivative, Fourier spectrum and energy expression are generally **different typed observables**. They may be derived from the same signal but need their own transformation operators. If `F_i = F_j ◦ T_ij` for differentiable scalar fields, their gradients obey the chain rule with the transition Jacobian; raw derivative values need not be numerically identical after a coordinate change. Fourier transformation additionally depends on an entire declared signal domain and boundary/sampling convention, so it is not merely a relabeling of local coordinates.

For the initial sinusoidal fixture, use

$$
f(x,t)=A\sin(kx-\omega t+\phi),\qquad
\partial_xf=Ak\cos(kx-\omega t+\phi),\qquad
|f|^2=A^2\sin^2(kx-\omega t+\phi).
$$

The phase must be dimensionless: `k` has inverse-x units and `omega` inverse-time units. Each derivative changes observable units. Squared amplitude has squared-amplitude units; calling it energy requires an additional physical model, constants, measure and, often, derivative terms. For example, a particular mechanical string model would need its own mass/tension and energy-density law before a plot can carry joules. The V3 seed’s `energy` branch computes `scale*sin(theta)^2`, whereas its sine branch computes `scale*sin(theta)`. At `scale=2`, these give squared sine amplitude 4 and `energy` value 2 at the crest. This is a measured distinction, not a reason to silently reinterpret or patch the input. [Source: `V3:Atlas.wave`; audit `energy-scale-is-not-amplitude-square`.]

`fourier_sine` in the seed is exactly another sine-expression branch. It does **not** calculate Fourier coefficients. PHANTOM does separately implement `division8/transfer.py::dft`, `fft`, `stft`, and `istft`; integrating them requires explicit sampling, transform normalization and complex-value contracts. Under the common finite DFT convention

$$
X_m=\sum_{j=0}^{N-1}x_j e^{-2\pi i mj/N},\qquad
x_j=\frac1N\sum_{m=0}^{N-1}X_m e^{2\pi i mj/N},
$$

the corresponding Parseval check is `sum |x_j|² = (1/N) sum |X_m|²`, up to the declared numerical tolerance. Continuous-signal units also depend on the sample spacing and quadrature convention. An inverse STFT requires the original framing/window rules and nonzero accumulated window weight at each reconstructed sample. Downsampling, magnitude-only spectra, clipping and quantization lose information unless an appropriate extra witness is retained. [Source: `PHANTOM:division8/transfer.py`; `docs/FINITE_BOUNDS.md`, finite numerical signal processing.]

An executable transition receipt should bind, at minimum, the following fields. This is a proposed integration contract; the V3 seed does not implement it:

```json
{
  "map_id": "versioned-map-identity",
  "input_chart_revision": "sha256",
  "output_chart_revision": "sha256",
  "domain_guard": "declared finite domain",
  "operation": "typed operator reference",
  "parameters": {},
  "input_units": "declared",
  "output_units": "declared",
  "loss_policy": "exact | bounded_numeric | irreversible",
  "absolute_tolerance": 0.0,
  "relative_tolerance": 0.0,
  "source_byte_witness": "artifact reference",
  "reference_result": "artifact reference",
  "counterexamples": [],
  "resource_budget": {},
  "evidence_status": "UNKNOWN"
}
```

## 3. Function-space comparisons, graphs and topology

Comparisons need declared domains, measures and compatible codomains:

| Comparison | Admission conditions | Appropriate falsifier/control |
|---|---|---|
| `L2` difference | Same domain/measure, square-integrable values, compatible units, specified quadrature for samples | Change chart placement without changing functions: function distance must remain unchanged |
| `H1` difference | Weak derivatives exist in the stated space; boundary/domain and derivative scaling declared | Same sample values with unresolved between-sample oscillation cannot establish equal derivatives |
| Operator norm | Defined input/output normed spaces, bounded operator, dimension/discretization stated | Compare a numerical norm with an independent singular-value/reference calculation on a bounded fixture |
| Graph shortest-path distance | Edge type, weight sign/units, directedness, reachable-pair policy | Disconnected pairs must not be silently assigned finite distances |
| Overlap graph | Explicit domain-intersection predicates | Nearby origins with disjoint chart domains do not imply overlap |
| Nerve/Čech-style complex | A specified cover or metric-ball family and a declared rule for all required intersections | Pairwise intersections alone do not certify every higher simplex |
| Topological equivalence | Explicit spaces, maps and the properties required by the claim | A visual resemblance or matching graph statistic is insufficient |

For a physically dimensioned one-dimensional signal, a scaled Sobolev comparison can use an explicitly chosen reference length `ell`:

$$
\|f\|_{H^1_\ell}^2=\int_\Omega (|f|^2+\ell^2|f'|^2)\,d\mu.
$$

The choice of `ell` is part of the model, not a hidden universal constant. If no physically meaningful normalization is available, retain the separate value and derivative errors instead of adding unlike quantities. This is a proposed contract for V3 §4, not an implemented norm in `Atlas`.

PHANTOM already provides bounded graph and cubical-complex witnesses through `transition_graph`, `graph_invariants`, `cubical_homology`, `closure_monoid`, and trace-DFA functions. Their edges/cells have declared finite-word meanings. They cannot be relabeled as physical chart geometry without a new mapping and verification. The retained width-four example’s one-skeleton and filled cube have different first Betti numbers because they are different complexes. [Source: `PHANTOM:division8/geometry.py`; `docs/FINITE_BOUNDS.md`.]

The words *homomorphism*, *homeomorphism*, *holomorphic*, and *holographic* remain distinct obligations: operation preservation; a continuous bijection with continuous inverse; complex differentiability on an appropriate domain; and a separately specified encoding/reconstruction principle. A shared name, visual resemblance, or successful byte round trip establishes none of the other properties. [V2 §51; V3 §§3–4; inherited PHANTOM commission §7.]

## 4. Coupling, propagation and finite growth

A chart-placement metric does not determine a coupling law. Each environmental edge must declare whether it is **physical**, **simulated**, or **logical**, its parameters/units, permitted direction, delay and boundary behavior. A plausible initial simulated fixture is a finite mass-spring-damper network:

$$
M\ddot q+C\dot q+L_Kq=f(t),
$$

where `M` is positive definite, `C` is positive semidefinite, and symmetric nonnegative couplings define graph Laplacian `L_K`. With consistent mechanical units, its model energy is

$$
E=\tfrac12\dot q^TM\dot q+\tfrac12q^TL_Kq,\qquad
\frac{dE}{dt}=\dot q^Tf-\dot q^TC\dot q.
$$

These equations are a **proposed reference fixture**, not a claim that Surface or the V3 seed implements them. They make tests concrete: zero forcing/damping gives conserved model energy; positive damping gives the predicted loss; disconnected components provide a negative-control transfer case; eigenmodes can be compared with a direct linear-algebra reference. Numerical integrator error must be distinguished from modeled dissipation. With delays, nonlinear couplings, directed weights or time-dependent parameters, derive a matching evolution/energy contract rather than reusing the simple conservation statement. [V3 §§5,6,23.]

Dynamic chart creation and atlas-of-atlases require finite limits on node count, ambient dimension, function sample count, edges, recursion depth, event count, state memory and simulation steps. A complete undirected edge list contains `N(N-1)/2` edges; the original `Atlas.edges()` emits that list without an explicit N/edge quota. Hierarchical grouping alone does not prove a valid manifold cover or reduce the work of a dense coupling calculation. New growth operations should record parent IDs, grammar rule, seed, guard result, cost and the exact created chart/map records. [Source: `V3:Atlas.edges`; V3 §§6,21,22.]

The wave alphabet contract is `symbol_id → psi_symbol(x,t;parameters)` with support, units, normalization, phase, sampling, perturbations and reference implementation. Symbol choice is an engineered encoding. To claim transfer or confluence, freeze the candidate, test held-out contexts, change the encoding as a control, measure error/cost separately and retain failed transfers. A generator emits a new typed artifact; it cannot rewrite the past evidence that admitted its parent. [V3 §§7,21–23; PHANTOM `generators.py`, `_runtime.py`.]

## 5. Binary words, quantum states and memory records

### The valid injective correspondence

For a declared width `n` and basis convention,

$$
w\in\{0,\ldots,2^n-1\}\longmapsto |w\rangle\in\mathbb C^{2^n}
$$

is injective. It maps a finite classical word to a computational-basis vector. It does not identify arbitrary statevectors with one classical word. A general pure-state representation is

$$
|\psi\rangle=\sum_{w=0}^{2^n-1}\alpha_w|w\rangle,
\qquad\sum_w|\alpha_w|^2=1.
$$

Relative phase affects interference; multiplication of the whole vector by a global phase represents the same pure-state ray. A density matrix must be finite, dimensionally valid, Hermitian, positive semidefinite and trace one. The pure-state construction `rho = psi psi†` is only a subset of mixed-state representations. [V3 §§8–10; source `basis_lift`, `density`, `quantum_distance`; IBM [state and channel representations](https://quantum.cloud.ibm.com/docs/en/api/qiskit/quantum_info).]

`basis_lift` implements the finite mapping for widths 1–16. Its array size is `2^n`, not `n`. The finite classical description of a basis state may need only `n` bits, whereas a dense binary64 complex vector needs `16*2^n` payload bytes, and a dense density matrix needs `16*4^n`. These counts concern chosen numerical representations; they are not hardware-qubit storage requirements or a claim that an arbitrary analog state has an exact finite classical encoding.

### Keep all addresses and orders explicit

| Field/type | Meaning | Example of a prohibited conflation |
|---|---|---|
| Source byte range | Offset/length in a hash-identified original file | A detector event number is not its byte offset |
| Numeric array index | Position under declared shape, strides and storage order | A state amplitude’s index is not a physical qubit number |
| Computational-basis index | Integer labeling a basis vector under a basis order | `basis_index=3` is not logical qubit 3 |
| Logical qubit ID | Circuit-level wire identity, with namespace/revision | It is not a stable provider device site |
| Register position | Wire’s index inside a declared logical register | Its significance depends on the specified ordering |
| Physical qubit address | Provider/backend/version-specific device identifier | It is not a CPU address or amplitude-vector byte offset |
| Coupler identity | An edge/site pair in a versioned hardware topology | A layout-neighbor relation is not a calibrated interaction |
| Pulse channel | Provider-defined control/readout channel with allowed semantics | It is not a generic waveform plot ID |
| Calibration timestamp | Acquisition/validity time for a particular device snapshot | It is not simulated time, receipt time or circuit depth |
| Shot index/readout bit | Outcome record in a sampled experiment, with circuit/backend context | A shot result does not reconstruct the premeasurement state |
| Host-memory byte offset | Offset in a specific encoded payload and ABI/layout | It is not a physical quantum address |

There is a verified **basis-order mismatch in the supplied code**. Oracle v0.1’s tensor-product construction treats qubit zero as the most significant index bit. V3’s `hadamard` treats it as the least significant bit, and its encoding metadata declares that convention. The native bridge preserves v0.1 semantics for `simulateCircuit`, declares `BasisOrder`, and uses explicit index-bit reversal in `reorderQubits` when converting. The independent two-qubit check uses a non-symmetric state because a Bell distribution can hide a swapped-bit error. [Source: native [PHANTOM.md](PHANTOM.md); `ORACLE:core.py::local`; `V3:hadamard`; [IBM bit-ordering guide](https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering).]

IBM’s ordering documentation also distinguishes integer interpretation, string display, amplitude-array order and API-specific output conventions. Therefore an adapter must pin the actual API/schema version and output order rather than assume the phrase “little endian” describes every layer. Reading this documentation is not evidence of a locally installed or executed IBM backend. [IBM bit-ordering guide](https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering).

### Exact numerical encoding is a separate layer

The V3 payload convention is IEEE-754 binary64 little-endian, interleaved real then imaginary component for each amplitude. For basis index `i`, its real component starts at byte offset `16*i` and imaginary component at `16*i+8`, within that encoded vector. A general record must additionally bind dtype, shape, basis order, qubit count, schema version, origin of the numbers, rounding/quantization policy, signed-zero/NaN policy, error budget and source-byte witness. Raw original bytes and a decoded/re-encoded numerical view are separate objects. [V3 §11; `complex_pairs`; native [PHANTOM.md](PHANTOM.md).]

The original `decode_pairs` verifies payload length/hash and `2^qubits` element count, but ignores its `basis_order` label. `complex_pairs` accepts a normalized three-element vector and rounds `log2(3)` to two qubits; decoding then rejects the result. These counterexamples block a claim that the seed already enforces the full binary/quantum representation contract. The existing native adapter has stricter power-of-two, finite-number, normalization and metadata-binding checks; it intentionally rejects nonfinite numeric data rather than claiming preservation of every possible NaN payload. [Audit `non-power-of-two-state`, `basis-order-metadata-not-bound`; native `serializeState`, `deserializeState`.]

### Measurement and pairwise correspondence tests

For a computational-basis projective measurement, `p(w)=|alpha_w|²`, or `p(w)=rho_ww` for a valid density matrix. This map loses phase information and is not bijective. A random shot count adds sampling uncertainty; a seeded simulator makes that simulation repeatable, not a physical measurement deterministic. The seed computes probabilities but does not sample shots. Oracle v0.1 supplies bounded seeded `shots`, and no physical provider receipt is implied. [Sources: V3 `measure_distribution`; Oracle `shots`; V3 §10.]

| Proposed pair | Valid scoped statement | Mandatory counterexample or qualification |
|---|---|---|
| Classical bit flip/XOR ↔ quantum X | X permutes the two basis states and agrees with classical NOT on known computational-basis inputs | Its action on a coherent state must retain amplitudes and phase; a bit truth table alone does not describe interference |
| Reversible finite classical map ↔ basis-permutation unitary | A bijection on the declared finite basis defines a permutation matrix | A many-to-one map is not a unitary on the same register; any reversible extension needs an explicit enlarged space and ancilla contract |
| Hadamard ↔ superposition/interference | H maps `∣0⟩` to equal-magnitude amplitudes; a later phase-sensitive operation distinguishes coherences | Equal measurement probabilities do not prove equal state preparation |
| Classical distribution ↔ diagonal density matrix | A normalized nonnegative distribution defines a diagonal density operator in a declared basis | The pure `∣+⟩` state and its diagonal dephased mixture have identical Z probabilities but different off-diagonal coherence |
| Statevector ↔ complex-byte record | A chosen finite-precision array can round-trip under a declared codec | The record is not a universal intrinsic bit pattern of an unknown physical qubit |
| Gate ↔ matrix/Kraus/pulse/device form | Each admitted conversion can preserve a defined operation under declared assumptions | A logical matrix alone does not establish a calibrated pulse implementation or hardware execution |

The audit explicitly compares `|+>` and `|->`: their basis probabilities are equal, while their Fubini–Study distance is `pi/2`. The original global-phase test uses a basis vector and returns zero. An additional Hadamard-state/global-phase probe returns a numerical residual of `2.1073424255447017e-8` radians, from the floating overlap followed by `acos`; it is not evidence that global phase is physically distinguishable. Retain that error and its precision convention instead of silently reporting every numerical case as exact zero. These are separate controls. [Audit `equal_probabilities_distinct_relative_phase`, `global_phase_distance`; V3 §§13–14.]

## 6. Quantum comparisons and gate/channel admission

Use a declared convention for each quantity. For normalized pure states, the V3 seed implements

$$
d_{FS}(\psi,\phi)=\arccos|\langle\psi|\phi\rangle|.
$$

This is distance between rays, with range `[0, pi/2]` under this convention. It does not measure chart-origin separation. For density matrices of the same dimension, one possible set of conventions is:

$$
D_{\mathrm{tr}}(\rho,\sigma)=\tfrac12\|\rho-\sigma\|_1,
\quad
F(\rho,\sigma)=\left(\operatorname{Tr}\sqrt{\sqrt\rho\,\sigma\sqrt\rho}\right)^2,
\quad
D_B(\rho,\sigma)=\sqrt{2(1-\sqrt F)}.
$$

These equations specify squared fidelity. Some libraries use the square root as their quantity named fidelity; compare conventions before comparing numbers. **Fidelity itself is not a distance metric**: larger values mean greater similarity and self-fidelity is one. The trace and Bures formulas require valid positive trace-one inputs, specified tolerances, and a stable matrix-square-root/eigensolver policy. None is implemented by the original V3 seed. The exact `d_FS` fixture and broader density-matrix metric gates must remain separate. [V3 §14; [IBM quantum-information API and state fidelity convention](https://quantum.cloud.ibm.com/docs/en/api/qiskit/quantum_info).]

Required operation admission includes matrix dimension, finite entries, domain, conditions, units where relevant, and independent reference vectors:

| Operation family | Mathematical admission | Supplied implementation |
|---|---|---|
| I, X, Y, Z, H, S, T, Rx, Ry, Rz, CX, CZ, SWAP | Matching dimensions; `U†U=I` within declared tolerance; wire order and parameter convention | Oracle/native support I/X/Y/Z/H/S/T/RX/RZ/CX; V3 seed supports H only |
| Measurement | POVM/projectors, probabilities, outcome record and postmeasurement update/loss if claimed | Probability extraction in V3; seeded basis shots in Oracle; no general measurement instruction semantics |
| Reset and classical control | Declared channel/instrument, control predicates, branch traces | No original V3 implementation |
| Kraus channel | `sum K_a†K_a=I` for trace preservation, matching dimensions and finite entries; CP through a valid Kraus construction | No typed V3 channel grammar |
| Lindblad evolution | Hamiltonian/collapse operators, assumptions, time/unit convention and numerical error | Oracle’s bounded matrix-exponential fixture; independent QuTiP comparison remains an obligation |
| Hardware compilation | Versioned target, topology, native gates, timing/noise/calibration and authenticated backend receipt | No inherited provider adapter or physical execution |

The QuTiP documentation provides an independent reference route for closed and open evolution. Merely citing it does not close a comparison gate. Record an actual installed version, fixture, invocation, trajectory/error result and receipt when the comparison is executed. [QuTiP master-equation guide](https://qutip.readthedocs.io/en/stable/guide/dynamics/dynamics-master.html); V2 G2/G5, V3 §§12,18.]

## 7. Every V3 constitutional provision: gate map

`ACCEPT` below applies only to the scope explicitly written in its row. `UNKNOWN` means the full obligation is not established; `NOT_STARTED` means the required integration has no supplied executable implementation. An observed invalid admission is retained as a counterexample rather than hidden by a passing local suite. The complete V3 release remains **UNKNOWN/incomplete**.

| V3 § | Required gate | Existing witness and current status | Work needed for full admission |
|---|---|---|---|
| 1 | Finite typed XY atlas, origins, SPD metrics, observables and maps | `Chart/Atlas` fields and distance fixture; **UNKNOWN** | Enforce dimensions/finite values/units; implement local metrics, domains and admissible maps |
| 2 | Ambient layout metric separate from similarity/physics | Seed edge labels make the distinction; **UNKNOWN** for general metric contract | Reject invalid origins, define ambient dimension and unit conversions, test metric axioms |
| 3 | Same-signal transitions and typed derivative/spectral/energy views | Sine/derivative fixtures; **UNKNOWN** | Executable transition maps, scale/phase/domain compatibility, inverse/loss/error receipts |
| 4 | Function norms and valid graph/cover/topology comparisons | PHANTOM has finite graph/cube operators; **NOT_STARTED** for atlas integration | Domain/measure/norm schemas, overlap/cover predicates and higher-intersection controls |
| 5 | Coupling, delays, damping and energy laws | No seed coupling solver; **NOT_STARTED** | Reference dynamics, conservation/dissipation tests, physical/simulated/logical edge tags |
| 6 | Dynamic N, nesting, budgets and deterministic visual trace | A finite list of charts and all-pairs edges only; **NOT_STARTED** for full gate | Resource caps, hierarchical semantics, native scene, chronology and replay |
| 7 | Wave alphabet and held-out transfer/confluence discovery | PHANTOM has bounded support/context transfer; **NOT_STARTED** for wave-atlas integration | Typed symbol laws, null/encoding controls, frozen candidate evaluation |
| 8 | Integer word to basis-ket injection | `basis_lift`, 1–16 bits; **ACCEPT** for this declared finite mapping | Keep basis convention and inverse-domain restrictions explicit at integration boundaries |
| 9 | Pure/mixed states, relative/global phase and density validity | Pure-state fixture, outer product, native guards; **UNKNOWN** | Full density schema, positivity/Hermiticity/trace guards and mixed-state negative controls |
| 10 | Born measurement with loss and sampling, Bloch/Pauli views | Probability and seeded Oracle-shot fixtures; **UNKNOWN** | Measurement instruments/loss records, uncertainties, declared Bloch/Pauli conventions |
| 11 | Exact declared numerical encoding plus original-byte witness | Byte and complex round trips; encoder/metadata counterexamples; **UNKNOWN** | Bound all metadata, reject invalid dimension, state precision/signed-zero/NaN policies |
| 12 | Required gates, channels, reset and control | Subset of ideal gates and one Lindblad fixture; **UNKNOWN** | Missing operations, typed channel/control semantics and unitary/CPTP/reference checks |
| 13 | Pairwise correspondences with break cases | Basis/H/phase fixtures and finite PHANTOM maps; **UNKNOWN** | Complete pair inventory, permutation/channel controls and explicit counterexample artifacts |
| 14 | Fubini–Study, trace, fidelity and Bures comparisons | Fubini–Study fixture only; **UNKNOWN** | Density prerequisites, convention tests, reference metrics; no conflation with layout |
| 15 | Distinct register/hardware/coupler/pulse/readout addresses | Native basis-order enum/conversion; **NOT_STARTED** for full address model | Provider/version schemas, logical-to-physical layout and calibration/readout bindings |
| 16 | Binary provenance below every scientific/control artifact | PHANTOM source/ledger and native numeric records; **UNKNOWN** | Bind every new domain’s raw frames/offsets through typed transformations to evidence |
| 17 | Domain charts with explicit overlap maps | Numerical functions and separate astronomical catalogue; **NOT_STARTED** for multi-domain atlas | Schrödinger/Bloch/Poincaré/image/event/time-series charts and validated cross-maps |
| 18 | Quantum hardware target/transpilation/noise/calibrated evidence | Ideal simulation only; **NOT_STARTED** | Offline target fixture and calibrated simulator first; authorized credentials/budget for optional device submission |
| 19 | FITS/WCS/time/calibration/PSF/spectral/photometry adapter | Existing catalogue is a distinct input path; **NOT_STARTED** for this gate | Licensed real FITS fixture, raw/derived separation, independent reader and uncertainty checks |
| 20 | ROOT/HepMC events, particles, four-vectors, weights/systematics | No supplied experimental event adapter; **NOT_STARTED** | Real licensed fixture, source offsets/digests, independent readers, invariant/selection controls |
| 21 | V3 research-state machine with typed witnessed transitions | PHANTOM has a different actual path; **UNKNOWN** | Explicit adapter between phase schemas, new event IDs, seeds, budgets and exact replay coordinates |
| 22 | Finite generator-of-generators with independent verification | PHANTOM factory and six compiled children; **ACCEPT** for inherited family; **UNKNOWN** for atlas generation | Versioned atlas grammar, independent checking of emitted maps/dynamics and immutable history |
| 23 | Laplacian/eigenmode/Fourier/covariance/clustering research with controls | Individual PHANTOM numerical/graph fixtures; **NOT_STARTED** for integrated discovery | Named priors, analytic and independent numerical references, perturbations and novelty obligations |
| 24 | Preserve all V2 gates; honest ACCEPT/REJECT/UNKNOWN/BLOCKED ledger | All source obligations preserved; full execution **UNKNOWN** | Close V2 G0–G7 within their scopes and run integrated release replay |

The source basis for this table is the full V3 constitution, the inspected implementations and the audit receipt. No row treats the current commission-text parser, generated work harness or astronomical catalogue as evidence that a physical or mathematical atlas solver exists.

## 8. Acceptance examples A–G

| Example | Observed evidence | Verdict and exact remaining scope |
|---|---|---|
| A: three XY plots of sine, derivative and square with distances 5/5 | Original `examples.py` outputs three chart records and pair distances 5,6,5 | **ACCEPT for numerical fixture**; no interactive N-chart visual scene in the seed |
| B: all 256 byte values reconstruct | `test_exact_bytes`; fresh audit repeats exact reconstruction | **ACCEPT**, opaque-byte domain only |
| C: 0 → `∣0⟩`, H → equal probabilities, LE binary64 complex round trip | Original basis/H/bridge tests and fresh example | **ACCEPT for valid normalized fixture**; malformed-state and metadata admission remain open |
| D: global-phase rays have zero distance | `test_phase_equivalence`; fresh audit; native phase-sensitive controls | **ACCEPT for stated pure-state convention and fixtures** |
| E: reject bad dimensions, units, tampered bytes and normalization | Payload tampering and unlike unit strings reject; several malformed inputs are admitted | **REJECT as a claim of complete seed validation**; counterexamples retained in audit |
| F: N-chart dynamic forces with reference solutions | No original seed implementation | **NOT_STARTED** |
| G: full V2 cold replay | Core baseline has scoped replay; integrated real-data/hardware/discovery gates are unresolved | **UNKNOWN** for the full V2 integration |

## 9. Domain receipts and final release test

For an astrophysics gate, preserve FITS HDUs/headers/data, WCS, time scale, units, calibration, masks, PSF/response, provenance and uncertainty. Raw-to-calibrated transforms need explicit loss and source bindings. A catalogue plot is a useful bounded result but does not supply the complete image/calibration pipeline. Astropy’s FITS documentation is a candidate reader/reference source; a concrete installed version and licensed real-data receipt are still necessary. [Astropy FITS guide](https://docs.astropy.org/en/stable/io/fits/index.html); V2 §§31–37; V3 §19.]

For a collider gate, retain actual ROOT/HepMC source records, release/schema, event/particle IDs, four-momenta, units, weights, detector interpretation, uncertainty and selection history. Verify invariants and reader agreement on a real declared dataset. An accelerator-inspired toy ring trajectory is not a collision event, calibrated accelerator model or live control interface. [Oracle `ring_tracking`; V2 §§38–45; V3 §20.]

For hardware, preserve the target topology/native gates, logical-to-physical mapping, calibration acquisition/validity, schedules, noise assumptions, shot/cost budgets and backend receipts. A local calibrated-simulator fixture can support the required compilation gate. Physical submission requires the user’s authorization and available credentials; no hardware execution is claimed by this document or audit. [V2 G5 and §§28–30; V3 §18.]

The final release witness must connect exact source bytes → structural decoding → typed operation/machine → numerical or physical model → observations → graded evidence, with the inverse reconstruction witness wherever claimed. It must state command, platform, source/code/package versions, denominator, output digest, tolerance, budget, controls and deviations. Preserve rejected candidates and unresolved claims. Independent cold replay must execute the integrated paths, not merely verify a manifest or display a generated checklist. [V2 release gates; V3 §§16,21–24; [consolidation assessment](QUANTUM_V3_CONSOLIDATION.md).]

## References and provenance

The controlling commission texts are immutable supplied sources. Their exact hashes and recursive read inventory are in the audit JSON. Official external references were checked on 25 October 2026 for conventions and potential independent comparisons, not as evidence of locally executed backends:

* [IBM Quantum: bit ordering](https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering).
* [IBM Quantum: states, channels and fidelity measures](https://quantum.cloud.ibm.com/docs/en/api/qiskit/quantum_info).
* [QuTiP: Lindblad master-equation solver](https://qutip.readthedocs.io/en/stable/guide/dynamics/dynamics-master.html).
* [Astropy: FITS file handling](https://docs.astropy.org/en/stable/io/fits/index.html).

No universal quantum/classical equivalence, new physical law, unrestricted semantic translation, physical hardware execution or fully completed atlas is claimed.
